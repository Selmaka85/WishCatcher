"""Composable WishCatcher contextual-intelligence plugin host.

Embedding, online search and MCP are optional *research* sources. They can
corroborate an opportunity but never overwrite first-party conversation evidence.

Provider-free defaults:
- Existing rule-driven context resolver (opt-in OpenAI-compatible LLM)
- SQLite FTS5 + typed-edges graph RAG
- No web/MCP requests and no arbitrary tool execution

All external research requires an explicit call with research=True AND enabled
provider configuration. This module imports only Python stdlib at import time.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
from urllib.parse import urlparse

from app.wishcatcher.contextual.context_resolver import ConversationContextResolver


class SearchAdapter(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        ...


class ToolAdapter(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        ...


@dataclass
class AnalysisOutput:
    frame: Dict[str, Any]
    knowledge: List[Dict[str, Any]] = field(default_factory=list)
    external_research: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "knowledge": self.knowledge,
            "external_research": self.external_research,
            "warnings": self.warnings,
        }


class SQLiteGraphRAG:
    """Local searchable corpus and explicit document links.

    Retrieval is lexical FTS5, with graph expansion using typed edges.
    This is *graph-assisted RAG*, not graph neural reasoning or embeddings.
    Only indexed documents and their explicitly declared links are retrieved.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = Path(
            db_path or os.getenv("WISHCATCHER_RAG_DB")
            or str(Path(__file__).resolve().parents[3] / "data" / "context_graph_rag.sqlite3")
        )
        if self.db_path.name == ":memory:":
            raise ValueError("Use a persistent sqlite path for graph RAG")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._fts_supported = True
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS documents ("
                "id TEXT PRIMARY KEY, body TEXT NOT NULL, source TEXT NOT NULL,"
                "metadata TEXT NOT NULL DEFAULT '{}')"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS edges ("
                "source_id TEXT NOT NULL, target_id TEXT NOT NULL,"
                "relation TEXT NOT NULL,"
                "PRIMARY KEY(source_id, target_id, relation),"
                "FOREIGN KEY(source_id) REFERENCES documents(id) ON DELETE CASCADE,"
                "FOREIGN KEY(target_id) REFERENCES documents(id) ON DELETE CASCADE)"
            )
            try:
                db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(id UNINDEXED, body)")
            except sqlite3.OperationalError:
                self._fts_supported = False

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.db_path), timeout=10)
        db.execute("PRAGMA foreign_keys=ON")
        db.row_factory = sqlite3.Row
        return db

    def put(self, doc_id: str, body: str, *, source: str = "local",
            metadata: Optional[Dict[str, Any]] = None) -> None:
        if not doc_id or len(doc_id) > 180 or not body.strip():
            raise ValueError("Expected nonempty document ID (<=180) and body")
        if len(body) > 100_000:
            raise ValueError("Document too large: split before indexing")
        with self._connect() as db:
            db.execute(
                "INSERT INTO documents(id,body,source,metadata) VALUES(?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET body=excluded.body,"
                "source=excluded.source,metadata=excluded.metadata",
                (doc_id, body, source[:200], json.dumps(metadata or {}, ensure_ascii=False)),
            )
            if self._fts_supported:
                db.execute("DELETE FROM documents_fts WHERE id=?", (doc_id,))
                db.execute("INSERT INTO documents_fts(id,body) VALUES(?,?)", (doc_id, body))

    def link(self, source_id: str, target_id: str, relation: str = "related") -> None:
        relation = relation.strip()[:80]
        if not relation:
            raise ValueError("Empty relation")
        with self._connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO edges(source_id,target_id,relation) VALUES(?,?,?)",
                (source_id, target_id, relation),
            )

    @staticmethod
    def _tokens(query: str) -> List[str]:
        # Constrain MATCH to plain quoted alphanumeric terms; no user FTS operators.
        words = re.findall(r"[\w]{3,}", query.lower(), flags=re.UNICODE)
        return list(dict.fromkeys(words))[:16]

    def retrieve(self, query: str, *, limit: int = 5, graph_hops: int = 1) -> List[Dict[str, Any]]:
        tokens = self._tokens(query)
        if not tokens:
            return []
        limit = max(1, min(int(limit), 20))
        with self._connect() as db:
            if self._fts_supported:
                expression = " OR ".join('"' + t.replace('"', '""') + '"' for t in tokens)
                rows = db.execute(
                    "SELECT d.id,d.body,d.source,d.metadata, "
                    "bm25(documents_fts) AS rank "
                    "FROM documents_fts JOIN documents d ON d.id=documents_fts.id "
                    "WHERE documents_fts MATCH ? ORDER BY rank LIMIT ?",
                    (expression, limit),
                ).fetchall()
            else:
                # FTS5-less Python builds remain functional, just slower.
                rows = db.execute("SELECT id,body,source,metadata FROM documents LIMIT 2000").fetchall()
                rows = sorted(
                    (r for r in rows if any(t in r["body"].lower() for t in tokens)),
                    key=lambda r: sum(r["body"].lower().count(t) for t in tokens),
                    reverse=True,
                )[:limit]
            result = [self._to_hit(row, "lexical") for row in rows]
            if graph_hops > 0 and result:
                seen = {row["id"] for row in result}
                seed_ids = list(seen)
                for current_id in seed_ids:
                    neighbors = db.execute(
                        "SELECT d.id,d.body,d.source,d.metadata,e.relation "
                        "FROM edges e JOIN documents d ON "
                        "d.id=CASE WHEN e.source_id=? THEN e.target_id ELSE e.source_id END "
                        "WHERE (e.source_id=? OR e.target_id=?) LIMIT 10",
                        (current_id, current_id, current_id),
                    ).fetchall()
                    for neighbor in neighbors:
                        if neighbor["id"] not in seen and len(result) < limit * 2:
                            seen.add(neighbor["id"])
                            result.append(self._to_hit(neighbor, "graph"))
            return result

    @staticmethod
    def _to_hit(row: sqlite3.Row, matched_via: str) -> Dict[str, Any]:
        return {
            "id": row["id"], "excerpt": row["body"][:700],
            "source": row["source"], "metadata": json.loads(row["metadata"]),
            "matched_via": matched_via,
        }


class BraveWebSearch:
    """Explicit opt-in online research. Search results are untrusted third-party claims."""

    def __init__(self) -> None:
        self.enabled = os.getenv("WISHCATCHER_WEB_SEARCH_ENABLED", "0") == "1"
        self.key = os.getenv("WISHCATCHER_BRAVE_API_KEY", "")

    async def search(self, query: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.enabled or not self.key or not query.strip():
            return []
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.key, "Accept": "application/json"},
                params={"q": query[:300], "count": max(1, min(limit, 10))},
            )
            response.raise_for_status()
            results = response.json().get("web", {}).get("results", [])
            return [
                {
                    "source_type": "brave_web",
                    "title": str(x.get("title") or "")[:200],
                    "url": str(x.get("url") or "")[:1000],
                    "snippet": str(x.get("description") or "")[:700],
                }
                for x in results[:limit] if isinstance(x, dict)
            ]


class MCPResearchBridge:
    """Allowlisted *read/search only* MCP tool bridge.

    Supports the 2026 Python MCP SDK's Streamable HTTP client. The bridge
    never auto-discovers and invokes arbitrary tools or spawns child processes.
    Operator configures an explicit read-only tool and allowed endpoint.
    """

    def __init__(self) -> None:
        self.enabled = os.getenv("WISHCATCHER_MCP_ENABLED", "0") == "1"
        self.endpoint = os.getenv("WISHCATCHER_MCP_ENDPOINT", "")
        self.tool_name = os.getenv("WISHCATCHER_MCP_SEARCH_TOOL", "search")
        self.allow_remote = os.getenv("WISHCATCHER_MCP_ALLOW_REMOTE", "0") == "1"
        self.allowlist = {
            x.strip() for x in
            os.getenv("WISHCATCHER_MCP_READ_ONLY_TOOLS", "search,search_web").split(",")
            if x.strip()
        }

    def _permitted(self) -> bool:
        parsed = urlparse(self.endpoint)
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        return (
            self.enabled and bool(parsed.hostname)
            and self.tool_name in self.allowlist
            and (parsed.scheme == "https" or (parsed.scheme == "http" and local))
            and (local or (self.allow_remote and parsed.scheme == "https"))
        )

    async def search(self, query: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        if not self._permitted() or not query.strip():
            return []
        try:
            from mcp import Client  # optional 2026 SDK dependency
        except ImportError:
            raise RuntimeError("MCP integration requires the optional 'mcp' package")

        async with Client(self.endpoint) as client:
            tools = await client.list_tools()
            if self.tool_name not in {tool.name for tool in tools.tools}:
                raise ValueError("Requested allowlisted tool unavailable on MCP server")
            result = await asyncio.wait_for(
                client.call_tool(self.tool_name, {"query": query[:300], "limit": min(10, limit)}),
                timeout=40,
            )
            if getattr(result, "is_error", False):
                raise RuntimeError("MCP research tool returned an error")
            structured = getattr(result, "structured_content", None)
            if structured is not None:
                payload = json.dumps(structured, ensure_ascii=False)
            else:
                payload = "\n".join(
                    str(getattr(block, "text", "")) for block in getattr(result, "content", [])
                )
            return [{"source_type": "mcp", "tool": self.tool_name,
                     "snippet": payload[:4000], "untrusted": True}]


class WishCatcherPlugin:
    """Re-usable entrypoint for CLI, FastAPI, MCP server, or external agents.

    Call 'analyze' with an explicit thread dictionary to avoid hard coupling
    to Reddit, a specific provider, or proprietary ChatGPT ad machinery.
    """

    def __init__(
        self,
        *,
        resolver: Optional[ConversationContextResolver] = None,
        rag: Optional[SQLiteGraphRAG] = None,
        web_search: Optional[SearchAdapter] = None,
        mcp_search: Optional[ToolAdapter] = None,
    ) -> None:
        self.resolver = resolver or ConversationContextResolver()
        self.rag = rag  # lazy default: do not create files on import
        self.web_search = web_search or BraveWebSearch()
        self.mcp_search = mcp_search or MCPResearchBridge()

    async def analyze(
        self, conversation: Dict[str, Any], *,
        retrieve_knowledge: bool = False, research: bool = False,
    ) -> AnalysisOutput:
        frame = await self.resolver.resolve(conversation)
        output = AnalysisOutput(frame=frame.to_dict())
        topic = frame.problem or frame.desired_outcome or frame.intent

        if retrieve_knowledge and topic:
            try:
                rag = self.rag or SQLiteGraphRAG()
                output.knowledge = rag.retrieve(topic, limit=5, graph_hops=1)
            except Exception as exc:
                output.warnings.append(f"Local RAG unavailable: {type(exc).__name__}")

        if research and frame.actionable and topic:
            # Deliberately NOT used to fabricate the speaker's intent.
            for name, provider in (("web", self.web_search), ("mcp", self.mcp_search)):
                try:
                    output.external_research.extend(
                        await provider.search(topic, limit=5)
                    )
                except Exception as exc:
                    output.warnings.append(
                        f"{name} research unavailable: {type(exc).__name__}"
                    )
        return output
