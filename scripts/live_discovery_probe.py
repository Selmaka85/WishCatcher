#!/usr/bin/env python3
"""One-off live source smoke for WishCatcher (not a synthetic test).

No paid providers, private data, platform logins, or stored user messages.
Read official public Hacker News API once per feed, run the actual
DiscoveryRunner and report anonymized evidence-backed opportunities.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.wishcatcher.discovery.sources import HackerNewsSource
from app.wishcatcher.discovery.pipeline import DiscoveryIndex, DiscoveryRunner


class CachedSource:
    def __init__(self, conversations):
        self.conversations = conversations

    async def fetch(self, limit=5):
        return self.conversations


async def main():
    # Run entirely provider-free; no sensitive source material is retained
    # outside temporary local SQLite files or submitted to an LLM provider.
    os.environ["WISHCATCHER_CONTEXT_LLM_ENABLED"] = "0"
    os.environ["WISHCATCHER_DISCOVERY_PERSIST_RAG"] = "1"
    with tempfile.TemporaryDirectory(prefix="wishcatcher-live-") as folder:
        os.environ["WISHCATCHER_DISCOVERY_DB"] = str(Path(folder) / "discovery.sqlite3")
        os.environ["WISHCATCHER_RAG_DB"] = str(Path(folder) / "knowledge.sqlite3")
        sources = {}
        metadata = []
        source_failures = {}
        for name, feed in (("hn_ask", "ask"), ("hn_show", "show")):
            try:
                reader = HackerNewsSource(
                    feed=feed, max_comments_per_story=8,
                    max_authors_per_story=3,
                )
                conversations = await asyncio.wait_for(reader.fetch(limit=8), timeout=85)
                sources[name] = CachedSource(conversations)
                for item in conversations:
                    conv = item.conversation
                    topic = conv.get("post_title") or (conv.get("metadata") or {}).get("thread_topic") or ""
                    metadata.append({
                        "source": name,
                        "source_id": item.source_id,
                        "topic": str(topic)[:180],
                        "url": item.url,
                        "message_count": 1 + len(conv.get("comments") or []),
                    })
            except Exception as exc:
                source_failures[name] = type(exc).__name__ + ": " + str(exc)[:180]
        if not sources:
            print("LIVE_WISHCATCHER_PROBE=" + json.dumps({
                "status": "SOURCE_NETWORK_FAILURE",
                "source_failures": source_failures,
            }, ensure_ascii=False))
            return 2

        index = DiscoveryIndex()
        runner = DiscoveryRunner(index=index, sources=sources)
        started = time.monotonic()
        result = await asyncio.wait_for(
            runner.run(list(sources), max_per_source=10, max_contexts=70),
            timeout=100,
        )
        clusters = result.get("clusters") or []
        with index.connect() as db:
            findings = db.execute(
                "SELECT source, source_key, cluster_id FROM findings"
            ).fetchall()
        accepted = []
        by_key = {
            (item["source"], index._digest(
                ("hackernews" if item["source"] in ("hn_ask", "hn_show") else item["source"])
                + "|" + item["source_id"]
            )): item for item in metadata
        }
        for finding in findings:
            # Original sources retain source="hackernews" for both feeds.
            info = next(
                (m for m in metadata
                 if index._digest("hackernews|" + m["source_id"]) == finding["source_key"]),
                None,
            )
            cluster = next(
                (c for c in clusters if c["cluster_id"] == finding["cluster_id"]), None
            )
            accepted.append({
                "topic": info["topic"] if info else "",
                "url": info["url"] if info else "",
                "problem": str((cluster or {}).get("frame", {}).get("problem") or "")[:280],
                "desired_outcome": str((cluster or {}).get("frame", {}).get("desired_outcome") or "")[:280],
                "cluster_id": finding["cluster_id"],
                "market_status": "UNVERIFIED",
            })
        report = {
            "status": result["status"],
            "collection": {
                "source_conversations": {name: len(s.conversations)
                                         for name, s in sources.items()},
                "total_contexts_examined": result["collected"],
                "accepted": result["accepted"],
                "new_findings": result["inserted"],
                "skipped": result["skipped"],
                "clusters": len(clusters),
                "elapsed_seconds": round(time.monotonic() - started, 2),
            },
            "source_failures": source_failures,
            "pipeline_errors": result["errors"],
            "sampled_topics": metadata[:18],
            "findings": accepted[:15],
            "cluster_summary": [
                {
                    "domain": c["domain"],
                    "intent": str(c["frame"].get("intent") or "")[:280],
                    "problem": str(c["frame"].get("problem") or "")[:280],
                    "unique_threads": c["unique_threads"],
                    "known_actors": c["known_actors"],
                    "status": c["status"],
                    "market_demand": c["market_demand"],
                }
                for c in clusters[:15]
            ],
        }
        print("LIVE_WISHCATCHER_PROBE=" + json.dumps(report, ensure_ascii=False))
        return 0 if result["status"] in ("completed", "partial") else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
