#!/usr/bin/env python3
"""WishCatcher Context Intelligence command-line plugin.

Examples:
    python scripts/wishcatcher_cli.py analyze examples/accounting_thread.json
    python scripts/wishcatcher_cli.py solution examples/accounting_thread.json
    python scripts/wishcatcher_cli.py ingest knowledge:1 /path/to/note.txt
    python scripts/wishcatcher_cli.py link knowledge:1 knowledge:2
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.wishcatcher.integrations.plugin_runtime import SQLiteGraphRAG, WishCatcherPlugin
from app.astra_genesis.context_bridge import GenesisContextBridge


def load_thread(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            raise ValueError("Conversation JSON must be an object")
        return obj
    entries = []
    for line in raw.splitlines():
        value = line.strip()
        if not value:
            continue
        speaker, sep, message = value.partition(": ")
        if sep and len(speaker) <= 55 and message:
            entries.append({"author": speaker.strip(), "text": message.strip()})
        elif entries:
            entries[-1]["text"] += "\n" + value
        else:
            entries.append({"author": "Owner", "text": value})
    if not entries:
        raise ValueError("No messages found")
    return {
        "post_id": "import:" + path.stem,
        "post_author": entries[0]["author"],
        "post_text": entries[0]["text"],
        "comments": [
            {"id": "m" + str(i), "author": row["author"],
             "text": row["text"], "timestamp": i}
            for i, row in enumerate(entries[1:], 1)
        ],
    }


async def analyze(args: argparse.Namespace) -> dict:
    conversation = load_thread(Path(args.input))
    plugin = WishCatcherPlugin()
    result = await plugin.analyze(
        conversation, research=args.research, remember=args.remember,
        retrieve_knowledge=args.retrieve,
    )
    if args.command == "solution":
        return GenesisContextBridge.compose(result.frame)
    return result.to_dict()


def main() -> int:
    parser = argparse.ArgumentParser(description="WishCatcher contextual needs plugin")
    subs = parser.add_subparsers(dest="command", required=True)
    for action in ("analyze", "solution"):
        action_parser = subs.add_parser(action)
        action_parser.add_argument("input", help="Conversation .json or speaker-labelled .txt")
        action_parser.add_argument("--research", action="store_true", help="Allow configured web/MCP search")
        action_parser.add_argument("--remember", action="store_true", help="Store a minimized need in local SQLite")
        action_parser.add_argument("--retrieve", action="store_true", help="Retrieve local RAG evidence")
        action_parser.add_argument("--output", help="Optional destination JSON file")
    ingest = subs.add_parser("ingest", help="Index a local UTF-8 knowledge file")
    ingest.add_argument("id")
    ingest.add_argument("file")
    ingest.add_argument("--source", default="operator-approved")
    link = subs.add_parser("link", help="Add an explicit local graph edge")
    link.add_argument("source_id")
    link.add_argument("target_id")
    link.add_argument("--relation", default="related")

    args = parser.parse_args()
    try:
        if args.command in ("analyze", "solution"):
            result = asyncio.run(analyze(args))
            serialized = json.dumps(result, indent=2, ensure_ascii=False)
            if args.output:
                Path(args.output).write_text(serialized + "\n", encoding="utf-8")
                print(args.output)
            else:
                print(serialized)
        elif args.command == "ingest":
            text = Path(args.file).read_text(encoding="utf-8")
            SQLiteGraphRAG().put(args.id, text, source=args.source)
            print(json.dumps({"stored": args.id}))
        elif args.command == "link":
            SQLiteGraphRAG().link(args.source_id, args.target_id, args.relation)
            print(json.dumps({"linked": [args.source_id, args.target_id]}))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print("WishCatcher error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
