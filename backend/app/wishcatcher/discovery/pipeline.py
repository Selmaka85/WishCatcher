"""Conservative autonomous discovery: sources -> context -> evidence -> clusters.

Unverified conversations are NOT customers, revenue or validated market demand.
This implementation deliberately separates source provenance from the user's
interpretation and requires independent actors AND threads for corroboration.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from app.astra_genesis.context_bridge import GenesisContextBridge
from app.wishcatcher.contextual.context_resolver import ConversationContextResolver
from app.wishcatcher.contextual.quality import ContextQualityGate
from app.wishcatcher.discovery.sources import ConversationSource, SourceConversation, configured_source
from app.wishcatcher.discovery.rss_source import PublicRSSSource
from app.wishcatcher.discovery.search_discovery import BraveIndexDiscovery, OfficialThreadHydrator
from app.wishcatcher.discovery.need_search import HackerNewsNeedSearch

_ALIASES = {
    "facturi": "invoice", "facturile": "invoice", "factura": "invoice",
    "invoicing": "invoice", "invoices": "invoice", "billing": "invoice",
    "contabilitate": "accounting", "bookkeeping": "accounting",
    "banca": "bank", "bancă": "bank", "banking": "bank",
    "aplicatie": "software", "aplicație": "software", "programe": "software",
    "program": "software", "apps": "software", "app": "software",
    "scump": "cost", "expensive": "cost", "costly": "cost",
    "automatic": "automate", "automatically": "automate",
    "integrate": "connect", "integration": "connect",
    "conecteaza": "connect", "conectează": "connect",
    "pierd": "waste", "pierde": "waste", "hours": "time", "ore": "time",
    "termin": "finish", "terminat": "finish", "finaliza": "finish",
    "repede": "fast", "rapid": "fast", "rapidă": "fast", "rapida": "fast",
    "reconciling": "reconciliation", "reconcile": "reconciliation",
    "reconciliere": "reconciliation", "invoicing": "invoice",
}
_STOP = set(("the this that what with have has had from were was want need needs "
             "and or to for are is it of on in a i am do does but my we me "
             "eu ca cu sa să iar un una e si și mi ma mea care ceva pot doar "
             "vreau dar asta ale unei unui ar fi trebuie din nu de la mai "
             "daca dacă as ai încercat tried tool tools get them "
             "potential unmet workflow inferred first person pain repeated "
             "problem statements").split())
# Domain is already checked separately; generic workflow adjectives must NOT
# be allowed to merge banking reconciliations with PDF invoice exports.
_GENERIC = {"software", "manual", "manually", "slow", "time",
            "spend", "spent", "waste", "cost", "expensive", "simple", "fast"}
_SENSITIVE_DOMAINS = {"health"}
_SENSITIVE_TEXT = re.compile(
    r"\b(?:medical|patient|diagnos|medic|doctor|political affiliation|"
    r"religious belief|sexual orientation|password|api.key|access.token)\b", re.I)


def tokens(value: str) -> set[str]:
    return {_ALIASES.get(t, t)
            for t in re.findall(r"[a-zăâîșț0-9]{3,}", value.lower())[:240]
            if t not in _STOP}


def similarity(left: Dict[str, Any], right: Dict[str, Any]) -> float:
    """Conservative grouping by shared specific need, not generic LLM text.

    This is lexical RO/EN normalization, not an embedding similarity model.
    False merges are particularly costly because they inflate independence.
    """
    if left.get("domain") != right.get("domain"):
        return 0.0
    def key(frame: Dict[str, Any]) -> set[str]:
        return tokens(" ".join(str(frame.get(k) or "") for k in (
            "problem", "desired_outcome", "intent"))) - _GENERIC
    a, b = key(left), key(right)
    if not a or not b or len(a & b) < 2:
        return 0.0
    goals_a = tokens(str(left.get("desired_outcome") or "")) - _GENERIC
    goals_b = tokens(str(right.get("desired_outcome") or "")) - _GENERIC
    # Different explicit outcomes cannot be grouped merely because the same
    # tools or pains are described in both posts.
    if goals_a and goals_b and not (goals_a & goals_b):
        return 0.0
    dice = 2 * len(a & b) / (len(a) + len(b))
    overlap = len(a & b) / min(len(a), len(b))
    return 0.65 * dice + 0.35 * overlap


def _redact_private_text(value: Any, max_length: int) -> str:
    """Best-effort redaction for small stored extracts (not formal anonymization)."""
    excerpt = str(value or "")
    excerpt = re.sub(r"(?i)\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b",
                     "[email-redacted]", excerpt)
    excerpt = re.sub(
        r"(?i)\b(api[-_ ]?key|password|token)\s*[:=]\s*[^\s,;]{6,}",
        "[secret-redacted]", excerpt,
    )
    excerpt = re.sub(r"(?<!\w)\+?\d[\d ()-]{8,}\d(?!\w)",
                     "[number-redacted]", excerpt)
    return excerpt[:max_length]


def minimal_frame(frame: Dict[str, Any]) -> Dict[str, Any]:
    """Bounded redacted source summary; no full-thread or actor profile."""

    keys = ("language", "domain", "problem", "desired_outcome", "intent",
            "constraints", "attempted_solutions", "epistemic_status",
            "interpretation_method", "confidence", "actionable")
    result = {key: frame.get(key) for key in keys}
    for key in ("problem", "desired_outcome", "intent"):
        result[key] = _redact_private_text(result.get(key), 500)
    for key in ("constraints", "attempted_solutions"):
        result[key] = [_redact_private_text(x, 160)
                       for x in (result.get(key) or [])[:8]]
    result["source_id"] = "src_" + hashlib.sha256(
        str(frame.get("source_id") or "").encode("utf-8")
    ).hexdigest()[:20]
    # Preserve auditability without archiving full conversations.
    # The evidence is exclusively from the primary actor as checked by
    # ContextQualityGate, and obvious contact details/keys are redacted.
    evidence = []
    for entry in (frame.get("evidence") or [])[:6]:
        if not isinstance(entry, dict):
            continue
        evidence.append({
            "message_id": _redact_private_text(entry.get("message_id"), 120),
            "excerpt": _redact_private_text(entry.get("excerpt"), 190),
        })
    result["evidence"] = evidence
    result["quality_status"] = str(frame.get("quality_status") or "unknown")[:60]
    result["grounding_status"] = str(frame.get("grounding_status") or "unverified")[:70]
    return result


class DiscoveryIndex:
    """SQLite WAL journal with stable HMAC pseudonyms and transactional updates."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.path = Path(db_path or os.getenv("WISHCATCHER_DISCOVERY_DB")
                         or str(Path(__file__).resolve().parents[3] / "data" / "discovery.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS findings(
                id TEXT PRIMARY KEY, source TEXT NOT NULL,
                source_key TEXT NOT NULL, thread_key TEXT NOT NULL,
                actor_key TEXT NOT NULL, url TEXT NOT NULL,
                frame_json TEXT NOT NULL, cluster_id TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                UNIQUE(source, source_key)
            );
            CREATE TABLE IF NOT EXISTS clusters(
                id TEXT PRIMARY KEY, domain TEXT NOT NULL,
                frame_json TEXT NOT NULL, genesis_json TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs(
                id TEXT PRIMARY KEY, sources TEXT NOT NULL,
                status TEXT NOT NULL, collected INTEGER NOT NULL,
                accepted INTEGER NOT NULL, inserted INTEGER NOT NULL,
                skipped INTEGER NOT NULL, errors_json TEXT NOT NULL,
                created_at INTEGER NOT NULL, finished_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS lock(
                id INTEGER PRIMARY KEY CHECK(id=1), acquired_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_findings_cluster ON findings(cluster_id);
            """)
            if not db.execute("SELECT value FROM config WHERE key='hmac_secret'").fetchone():
                db.execute("INSERT INTO config(key,value) VALUES('hmac_secret',?)",
                           (secrets.token_hex(32),))

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.path), timeout=12)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=12000")
        return db

    def _digest(self, text: str) -> str:
        with self.connect() as db:
            secret = db.execute("SELECT value FROM config WHERE key='hmac_secret'").fetchone()[0]
        return hmac.new(bytes.fromhex(secret), text.encode("utf-8"), hashlib.sha256).hexdigest()[:32]

    def begin(self, sources: Sequence[str]) -> str:
        now, ident = int(time.time()), uuid.uuid4().hex
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM lock WHERE acquired_at < ?", (now - 1800,))
            try:
                db.execute("INSERT INTO lock(id,acquired_at) VALUES(1,?)", (now,))
            except sqlite3.IntegrityError as exc:
                raise RuntimeError("Discovery is already running; concurrent runs are blocked") from exc
            db.execute(
                "INSERT INTO runs(id,sources,status,collected,accepted,inserted,skipped,"
                "errors_json,created_at) VALUES(?,?,'running',0,0,0,0,'[]',?)",
                (ident, json.dumps(list(sources)), now))
        return ident

    def finish(self, ident: str, metrics: Dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE runs SET status=?,collected=?,accepted=?,inserted=?,"
                "skipped=?,errors_json=?,finished_at=? WHERE id=?",
                (metrics["status"], metrics["collected"], metrics["accepted"],
                 metrics["inserted"], metrics["skipped"],
                 json.dumps(metrics["errors"])[:10000], int(time.time()), ident))
            db.execute("DELETE FROM lock WHERE id=1")

    def already_seen(self, item: SourceConversation) -> bool:
        """Avoid repeated inference costs on identical source IDs.

        Current v1 treats a discovered thread as a snapshot; incremental
        re-evaluation of edited/new replies needs versioned fingerprints.
        """
        key = self._digest(item.source + "|" + item.source_id)
        with self.connect() as db:
            return db.execute(
                "SELECT 1 FROM findings WHERE source=? AND source_key=?",
                (item.source, key),
            ).fetchone() is not None

    def ingest(self, item: SourceConversation, frame: Dict[str, Any],
               *, match_threshold: float = 0.74) -> str:
        if not frame.get("actionable") or not frame.get("evidence"):
            return "non_actionable"
        domain = str(frame.get("domain") or "other")
        if domain in _SENSITIVE_DOMAINS:
            return "sensitive_excluded"
        if _SENSITIVE_TEXT.search(str(frame.get("problem") or "") +
                                  " " + str(frame.get("intent") or "")):
            return "sensitive_excluded"
        safe = minimal_frame(frame)
        source_key = self._digest(item.source + "|" + item.source_id)
        meta = item.conversation.get("metadata") or {}
        thread_id = str(meta.get("thread_id") or item.source_id.split(":actor:")[0])
        thread_key = self._digest(item.source + "|" + thread_id)
        actor = str(frame.get("primary_actor") or "")
        # Unknown authors must not become false independent customers.
        actor_key = (self._digest(item.source + "|actor|" + actor)
                     if actor and not actor.startswith("__unknown") else "")
        now = int(time.time())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM findings WHERE source=? AND source_key=?",
                          (item.source, source_key)).fetchone():
                return "duplicate"
            cluster_id: Optional[str] = None
            best = match_threshold
            for row in db.execute("SELECT id,frame_json FROM clusters WHERE domain=?",
                                  (domain,)).fetchall():
                score = similarity(safe, json.loads(row["frame_json"]))
                if score >= best:
                    cluster_id = row["id"]
                    best = score
            if cluster_id is None:
                cluster_id = "need_" + uuid.uuid4().hex[:18]
                # Genesis is a hypothesis composer, not a revenue estimator.
                # Persist the same minimized, redacted factual material
                # in both the discovery frame and Genesis hypotheses.
                # Otherwise the brief reintroduced sensitive raw excerpts.
                genesis = GenesisContextBridge.compose({
                    **safe, "evidence": safe.get("evidence") or [],
                })
                db.execute(
                    "INSERT INTO clusters(id,domain,frame_json,genesis_json,created_at)"
                    " VALUES(?,?,?,?,?)",
                    (cluster_id, domain, json.dumps(safe, ensure_ascii=False),
                     json.dumps(genesis, ensure_ascii=False), now))
            db.execute(
                "INSERT INTO findings(id,source,source_key,thread_key,actor_key,url,"
                "frame_json,cluster_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                ("finding_" + uuid.uuid4().hex[:18], item.source, source_key,
                 thread_key, actor_key, item.url[:1000],
                 json.dumps(safe, ensure_ascii=False), cluster_id, now))
        return cluster_id

    def clusters(self, limit: int = 30) -> List[Dict[str, Any]]:
        limit = max(1, min(limit, 100))
        with self.connect() as db:
            rows = db.execute("""
                SELECT c.id,c.domain,c.frame_json,c.genesis_json,c.created_at,
                  COUNT(f.id) AS mentions,
                  COUNT(DISTINCT f.thread_key) AS unique_threads,
                  COUNT(DISTINCT NULLIF(f.actor_key,'')) AS known_actors,
                  COUNT(DISTINCT f.source) AS source_count,
                  MAX(f.created_at) AS last_seen
                FROM clusters c JOIN findings f ON c.id=f.cluster_id
                GROUP BY c.id ORDER BY unique_threads DESC,known_actors DESC,
                                   mentions DESC,c.created_at DESC LIMIT ?
            """, (limit,)).fetchall()
            # Include small per-thread provenance samples for independent
            # auditing; never expose HMAC person identifiers or full threads.
            provenance = {}
            for cluster in rows:
                candidates = db.execute(
                    "SELECT source,url,thread_key,frame_json FROM findings "
                    "WHERE cluster_id=? ORDER BY created_at DESC LIMIT 40",
                    (cluster["id"],),
                ).fetchall()
                seen_threads = set()
                samples = []
                for evidence_row in candidates:
                    if evidence_row["thread_key"] in seen_threads:
                        continue
                    seen_threads.add(evidence_row["thread_key"])
                    parsed = json.loads(evidence_row["frame_json"])
                    samples.append({
                        "source": evidence_row["source"],
                        "url": evidence_row["url"][:1000],
                        "evidence": (parsed.get("evidence") or [])[:2],
                        "grounding_status": parsed.get("grounding_status", "unknown"),
                    })
                    if len(samples) >= 6:
                        break
                provenance[cluster["id"]] = samples
        result = []
        for row in rows:
            # Deliberately NOT "market validated": evidence from multiple
            # distinct authors/threads can only corroborate recurrence.
            corroborated = row["unique_threads"] >= 2 and row["known_actors"] >= 2
            signal = min(1.0, 0.25 * row["unique_threads"] +
                         0.15 * row["known_actors"] + 0.1 * row["source_count"])
            result.append({
                "cluster_id": row["id"], "domain": row["domain"],
                "frame": json.loads(row["frame_json"]),
                "genesis": json.loads(row["genesis_json"]),
                "mentions": row["mentions"], "unique_threads": row["unique_threads"],
                "known_actors": row["known_actors"], "source_count": row["source_count"],
                "status": "CORROBORATED_NEED_HYPOTHESIS" if corroborated
                          else "SINGLE_SOURCE_HYPOTHESIS",
                "signal_score": round(signal, 3),
                "market_demand": "UNKNOWN", "willingness_to_pay": "UNKNOWN",
                "supporting_sources": provenance.get(row["id"], []),
                "last_seen": row["last_seen"],
            })
        return result

    def recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
                (max(1, min(limit, 30)),)).fetchall()
        return [
            {"id": r["id"], "sources": json.loads(r["sources"]),
             "status": r["status"], "collected": r["collected"],
             "accepted": r["accepted"], "inserted": r["inserted"],
             "skipped": r["skipped"], "errors": json.loads(r["errors_json"]),
             "created_at": r["created_at"], "finished_at": r["finished_at"]}
            for r in rows
        ]


class DiscoveryRunner:
    """Operator-initiated run; can also be invoked by an opt-in scheduler."""

    SUPPORTED = frozenset(("hn_ask", "hn_show", "hn_new", "hn_need_search",
                           "approved_jsonl", "public_rss", "search_hn"))

    def __init__(self, *, index: Optional[DiscoveryIndex] = None,
                 resolver: Optional[ConversationContextResolver] = None,
                 sources: Optional[Dict[str, ConversationSource]] = None) -> None:
        self.index = index or DiscoveryIndex()
        self.resolver = resolver or ConversationContextResolver()
        self.quality = ContextQualityGate()
        self.sources = sources or {}

    async def _get_source(self, name: str, max_per_source: int) -> List[SourceConversation]:
        if name in self.sources:
            return await self.sources[name].fetch(limit=max_per_source)
        if name == "hn_need_search":
            return await HackerNewsNeedSearch().fetch(limit=max_per_source)
        if name == "public_rss":
            url = os.getenv("WISHCATCHER_APPROVED_RSS_URL", "")
            if os.getenv("WISHCATCHER_RSS_APPROVED", "0") != "1" or not url:
                raise PermissionError("Set WISHCATCHER_RSS_APPROVED=1 and approved RSS URL")
            return await PublicRSSSource(url, approved=True).fetch(limit=max_per_source)
        if name == "search_hn":
            # Search index discovery never becomes intent evidence on its own.
            search = BraveIndexDiscovery()
            leads = await search.search(max_queries=2, per_query=max_per_source)
            if not leads:
                return []
            return await OfficialThreadHydrator().hydrate(leads, limit=max_per_source)
        return await configured_source(name).fetch(limit=max_per_source)

    async def run(self, source_names: Sequence[str], *, max_per_source: int = 5,
                  max_contexts: int = 40) -> Dict[str, Any]:
        names = list(dict.fromkeys(source_names))
        if not names or any(name not in self.SUPPORTED for name in names):
            raise ValueError("Sources must be selected from " +
                             ", ".join(sorted(self.SUPPORTED)))
        max_per_source = max(1, min(int(max_per_source), 10))
        max_contexts = max(1, min(int(max_contexts), 70))
        ident = self.index.begin(names)
        metrics: Dict[str, Any] = {
            "id": ident, "sources": names, "status": "completed",
            "collected": 0, "accepted": 0, "inserted": 0,
            "skipped": 0, "errors": [], "rejection_reasons": {},
        }
        def reject(reason: str) -> None:
            metrics["skipped"] += 1
            counts = metrics["rejection_reasons"]
            counts[reason] = counts.get(reason, 0) + 1
        inspected: set[tuple[str, str]] = set()
        try:
            for name in names:
                try:
                    collected = await self._get_source(name, max_per_source)
                except Exception as exc:
                    metrics["errors"].append(f"{name}: {type(exc).__name__}: {str(exc)[:180]}")
                    continue
                for item in collected:
                    if metrics["collected"] >= max_contexts:
                        break
                    dedupe_key = (item.source, item.source_id)
                    if dedupe_key in inspected:
                        reject("duplicate_in_batch")
                        continue
                    inspected.add(dedupe_key)
                    metrics["collected"] += 1
                    # Cost guard: repeated scheduled polls must not send
                    # already-indexed discussions to remote/local LLM again.
                    if self.index.already_seen(item):
                        reject("already_indexed")
                        continue
                    try:
                        frame = (await self.resolver.resolve(item.conversation)).to_dict()
                        quality = self.quality.assess(item.conversation, frame)
                        if not quality.accepted:
                            reject(quality.flags[0] if quality.flags else "no_quality_verdict")
                            continue
                        frame["quality_status"] = quality.status
                        frame["quality_flags"] = quality.flags
                        frame["field_evidence"] = quality.field_evidence
                        metrics["accepted"] += 1
                        result = self.index.ingest(item, frame)
                        if result.startswith("need_"):
                            metrics["inserted"] += 1
                            # Optional local knowledge memory: useful for
                            # future retrieval, not new customer evidence.
                            if os.getenv("WISHCATCHER_DISCOVERY_PERSIST_RAG", "1") == "1":
                                try:
                                    from app.wishcatcher.integrations.plugin_runtime import SQLiteGraphRAG
                                    rag = SQLiteGraphRAG()
                                    doc_id = rag.remember_context_frame(frame)
                                    if doc_id:
                                        rag.put(
                                            result,
                                            "Need category: " + str(frame.get("domain") or "") +
                                            "\nProblem: " + str(frame.get("problem") or "")[:350] +
                                            "\nGoal: " + str(frame.get("desired_outcome") or "")[:350],
                                            source="discovery_cluster",
                                            metadata={"market_validation": "UNKNOWN",
                                                      "kind": "unverified_need_cluster"},
                                        )
                                        rag.link(doc_id, result, "observed_as")
                                except Exception as rag_exc:
                                    metrics["errors"].append(
                                        f"local RAG enrichment: {type(rag_exc).__name__}"
                                    )
                        else:
                            reject(result)
                    except Exception as exc:
                        metrics["errors"].append(
                            f"{name} context failure {type(exc).__name__}: {str(exc)[:120]}")
                if metrics["collected"] >= max_contexts:
                    break
            if metrics["errors"]:
                metrics["status"] = "partial" if metrics["collected"] else "failed"
            return {
                **metrics, "clusters": self.index.clusters(limit=20),
            }
        except Exception as exc:
            metrics["status"] = "failed"
            metrics["errors"].append(f"fatal: {type(exc).__name__}: {str(exc)[:180]}")
            raise
        finally:
            self.index.finish(ident, metrics)
