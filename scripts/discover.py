#!/usr/bin/env python3
"""Local operator CLI: run discovery and inspect independently grounded needs.

Examples:
  python scripts/discover.py run --sources hn_ask hn_show --limit 3
  python scripts/discover.py run --sources approved_jsonl
  python scripts/discover.py clusters
  python scripts/discover.py runs
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.wishcatcher.discovery.pipeline import DiscoveryIndex, DiscoveryRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="WishCatcher login-free discovery")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Bounded source collection and clustering")
    run.add_argument("--sources", nargs="+", default=["hn_ask"])
    run.add_argument("--limit", type=int, default=3, help="Max stories per source (1-10)")
    run.add_argument("--max-contexts", type=int, default=30, help="Overall cap (1-70)")
    commands.add_parser("clusters", help="Show stored needs and source counts")
    commands.add_parser("runs", help="Show execution history")
    args = parser.parse_args()
    try:
        if args.command == "run":
            report = asyncio.run(DiscoveryRunner().run(
                args.sources, max_per_source=args.limit,
                max_contexts=args.max_contexts))
        elif args.command == "clusters":
            report = {"clusters": DiscoveryIndex().clusters(limit=100)}
        else:
            report = {"runs": DiscoveryIndex().recent_runs(limit=30)}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if args.command != "run" or report.get("status") != "failed" else 2
    except (ValueError, PermissionError, RuntimeError, OSError) as exc:
        print("WishCatcher discovery: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
