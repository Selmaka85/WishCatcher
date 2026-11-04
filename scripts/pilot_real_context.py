#!/usr/bin/env python3
"""P1/P2 naturally occurring HN context pilot, local-only, not a gold benchmark.

Source retrieval: Algolia HN locator + author/story verified by official Firebase,
plus a small neutral Ask HN sample. Every case is interpreted twice with exactly
the same public messages. Reports contain public URLs, hashes and aggregate
decisions, NOT copied comments, usernames or supposedly human gold labels.

Important: model agreement is NOT accuracy. This one-shot *observational* pilot
cannot compute recall, precision, customer demand or model superiority.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from scripts.evaluate_context_ab import local_interpreter
from app.wishcatcher.contextual.context_resolver import ConversationContextResolver
from app.wishcatcher.contextual.quality import ContextQualityGate
from app.wishcatcher.discovery.need_search import HackerNewsNeedSearch
from app.wishcatcher.discovery.sources import HackerNewsSource, SourceConversation

PACKS = ("explicit", "workaround", "friction", "outcome")
DEFAULT_MAX = 12
MAX_ALLOWED = 20


def select_balanced(samples: Dict[str, List[SourceConversation]], limit: int,
                    *, unique_threads: bool = True
                    ) -> List[tuple[str, SourceConversation]]:
    """One candidate per stratum per round; dedupe across indexed HN packs."""
    selected: List[tuple[str, SourceConversation]] = []
    seen: set[tuple[str, str]] = set()
    seen_threads: set[str] = set()
    order = list(PACKS) + ["hn_ask_neutral"]
    for index in range(max((len(samples.get(pack) or []) for pack in order), default=0)):
        for pack in order:
            items = samples.get(pack) or []
            if index >= len(items):
                continue
            item = items[index]
            key = (item.source, item.source_id)
            if key in seen:
                continue
            if unique_threads and item.url in seen_threads:
                continue
            # Only verified public Hacker News. Other sources need separate rights review.
            if item.source != "hackernews" or not item.url.startswith(
                    "https://news.ycombinator.com/item?id="):
                continue
            seen.add(key)
            seen_threads.add(item.url)
            selected.append((pack, item))
            if len(selected) >= limit:
                return selected
    return selected


def summary_case(pack: str, item: SourceConversation,
                 rule_frame: Dict[str, Any], rule_quality: Any,
                 llm_frame: Dict[str, Any], llm_quality: Any,
                 llm_seconds: float) -> Dict[str, Any]:
    """No model-generated text or raw source messages in Actions logs."""
    original_method = llm_frame.get("interpretation_method") or "unknown"
    domain = rule_frame.get("domain") or "other"
    primary_id = str(item.conversation.get("post_id") or "")
    match = re.fullmatch(r"hn:([0-9]{1,18})", primary_id)
    # This comment/story ID comes from verified HN source data, not an LLM.
    primary_url = ("https://news.ycombinator.com/item?id=" + match.group(1)
                   if match else None)
    # Never publish or persist extracted details from sensitive discussions.
    return {
        "case_hash": hashlib.sha256(
            (item.source + ":" + item.source_id).encode("utf-8")
        ).hexdigest()[:16],
        "source_url": item.url,
        "primary_evidence_url": primary_url,
        "stratum": pack,
        "domain": domain if domain not in {"health"} else "sensitive_excluded",
        "message_count": int(rule_frame.get("message_count") or 0),
        "rules_accepted": bool(rule_quality.accepted),
        "model_accepted": bool(llm_quality.accepted),
        "model_interpretation_adopted": original_method == "llm_contextual",
        "model_method": original_method,
        "decision_disagreement": bool(rule_quality.accepted) != bool(llm_quality.accepted),
        "rule_flags": list(rule_quality.flags or [])[:4],
        "model_flags": list(llm_quality.flags or [])[:4],
        "llm_seconds": round(llm_seconds, 3),
        "review_status": "UNLABELED_REAL_PUBLIC_SOURCE",
        "willingness_to_pay": "UNKNOWN",
    }


async def acquire(per_pack: int, *, include_neutral: bool = True,
                  source_override: Optional[Dict[str, Any]] = None
                  ) -> tuple[Dict[str, List[SourceConversation]], Dict[str, str]]:
    records: Dict[str, List[SourceConversation]] = {}
    errors: Dict[str, str] = {}
    source_override = source_override or {}
    for pack in PACKS:
        try:
            scout = source_override.get(pack) or HackerNewsNeedSearch(
                query_pack=pack, max_queries=3, max_actor_messages=4,
            )
            records[pack] = await asyncio.wait_for(
                scout.fetch(limit=per_pack), timeout=95
            )
        except Exception as exc:
            # Never log external source text or raw response bodies.
            errors[pack] = type(exc).__name__
            records[pack] = []
    if include_neutral:
        name = "hn_ask_neutral"
        try:
            source = source_override.get(name) or HackerNewsSource(
                feed="ask", max_comments_per_story=6, max_authors_per_story=2
            )
            records[name] = await asyncio.wait_for(
                source.fetch(limit=per_pack), timeout=90
            )
        except Exception as exc:
            errors[name] = type(exc).__name__
            records[name] = []
    return records, errors


async def evaluate(samples: Sequence[tuple[str, SourceConversation]],
                   model: Any) -> Dict[str, Any]:
    rule_engine = ConversationContextResolver()
    rule_engine.interpreter.enabled = False
    model_engine = ConversationContextResolver(interpreter=model)
    gate = ContextQualityGate()
    rows: List[Dict[str, Any]] = []
    counts = Counter()
    for pack, item in samples:
        original = await rule_engine.resolve(item.conversation)
        rule_frame = original.to_dict()
        # Keep model inputs identical; do not read synthetic case labels.
        begin = time.monotonic()
        candidate = await model_engine.resolve(item.conversation)
        llm_seconds = time.monotonic() - begin
        model_frame = candidate.to_dict()
        rule_quality = gate.assess(item.conversation, rule_frame)
        model_quality = gate.assess(item.conversation, model_frame)
        row = summary_case(
            pack, item, rule_frame, rule_quality, model_frame,
            model_quality, llm_seconds
        )
        # Sensitive domains are out of scope for this research instrument.
        if row["domain"] == "sensitive_excluded":
            counts["sensitive_excluded"] += 1
            continue
        rows.append(row)
        counts["cases"] += 1
        counts["rule_accepted"] += int(row["rules_accepted"])
        counts["model_accepted"] += int(row["model_accepted"])
        counts["model_adopted"] += int(row["model_interpretation_adopted"])
        counts["disagreements"] += int(row["decision_disagreement"])
        counts["fallback"] += int(not row["model_interpretation_adopted"])
    return {
        "n": counts["cases"],
        "rule_accepted": counts["rule_accepted"],
        "model_accepted": counts["model_accepted"],
        "model_adopted": counts["model_adopted"],
        "fallback": counts["fallback"],
        "decision_disagreements": counts["disagreements"],
        "sensitive_excluded": counts["sensitive_excluded"],
        "cases": rows,
    }


async def run(args: argparse.Namespace, *, sources: Optional[Dict[str, Any]] = None,
              interpreter: Any = None) -> Dict[str, Any]:
    if not 1 <= args.maximum <= MAX_ALLOWED or not 1 <= args.per_pack <= 8:
        raise ValueError("Bounded pilot requires 1..20 cases and 1..8 per pack")
    acquired, errors = await acquire(
        args.per_pack, source_override=sources
    )
    selected = select_balanced(acquired, args.maximum)
    if not selected:
        return {
            "status": "NO_PUBLIC_SOURCES",
            "source_errors": errors,
            "source_counts": {k: len(v) for k, v in acquired.items()},
        }
    model = interpreter or local_interpreter(args.local_url, args.local_model)
    result = await evaluate(selected, model)
    return {
        "kind": "REAL_UNLABELED_PUBLIC_SOURCE_OBSERVATIONAL_PILOT",
        "status": (
            "MODEL_USED_REAL_SOURCES" if result["model_adopted"]
            else "NO_MODEL_ADOPTION_DIAGNOSTIC"
        ),
        "source_counts": {key: len(value) for key, value in acquired.items()},
        "selected_by_pack": dict(Counter(pack for pack, _ in selected)),
        "distinct_threads_selected": len({item.url for _, item in selected}),
        "sampling_rule": "AT_MOST_ONE_ACTOR_CONTEXT_PER_VERIFIED_THREAD",
        "source_errors": errors,
        "sample": result,
        "precision": None,
        "recall": None,
        "human_gold_label_count": 0,
        "population_coverage": "UNMEASURED_SEARCH_BIAS",
        "note": "Observed agreement/disagreement is not human-verified correctness or paid demand.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maximum", type=int, default=DEFAULT_MAX)
    parser.add_argument("--per-pack", type=int, default=4)
    parser.add_argument("--local-url", default="http://127.0.0.1:11434/v1/chat/completions")
    parser.add_argument("--local-model", default="qwen2.5:1.5b")
    args = parser.parse_args()
    os.environ["WISHCATCHER_CONTEXT_ALLOW_REMOTE"] = "0"
    os.environ["WISHCATCHER_WEB_SEARCH_ENABLED"] = "0"
    os.environ["WISHCATCHER_MCP_ENABLED"] = "0"
    result = asyncio.run(run(args))
    print("P1_P2_NATURAL_PILOT=" + json.dumps(result, ensure_ascii=False))
    if result["status"] != "MODEL_USED_REAL_SOURCES":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
