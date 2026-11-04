#!/usr/bin/env python3
"""Reproducible bilingual contextual-intent evaluation.

Synthetic fixtures are regression controls, not a real-world scientific score.
Compare baseline fallback against evidence/quality gated candidates. Model
providers are not contacted; separate live labeled validation is required.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.wishcatcher.contextual.context_resolver import ConversationContextResolver
from app.wishcatcher.contextual.quality import ContextQualityGate


def confusion(predicted: List[bool], expected: List[bool]) -> Dict[str, Any]:
    tp = sum(p and y for p, y in zip(predicted, expected))
    fp = sum(p and not y for p, y in zip(predicted, expected))
    tn = sum(not p and not y for p, y in zip(predicted, expected))
    fn = sum(not p and y for p, y in zip(predicted, expected))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4), "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


async def evaluate(path: Path) -> Dict[str, Any]:
    fixtures = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
    old_env = os.getenv("WISHCATCHER_CONTEXT_LLM_ENABLED")
    os.environ["WISHCATCHER_CONTEXT_LLM_ENABLED"] = "0"
    try:
        engine, gate = ConversationContextResolver(), ContextQualityGate()
        expected: List[bool] = []
        baseline: List[bool] = []
        filtered: List[bool] = []
        cases: List[Dict[str, Any]] = []
        langs: Dict[str, Dict[str, List[bool]]] = {}
        for row in fixtures:
            if not isinstance(row.get("label"), bool):
                raise ValueError("Gold fixture label must be a boolean")
            frame = (await engine.resolve(row["conversation"])).to_dict()
            decision = gate.assess(row["conversation"], frame)
            truth = row["label"]
            initial, after = bool(frame["actionable"]), decision.accepted
            expected.append(truth)
            baseline.append(initial)
            filtered.append(after)
            language = str(row.get("language") or "unknown")
            bucket = langs.setdefault(language, {"expected": [], "baseline": [], "filtered": []})
            bucket["expected"].append(truth)
            bucket["baseline"].append(initial)
            bucket["filtered"].append(after)
            cases.append({
                "id": row.get("id"), "expected": truth, "baseline": initial,
                "quality_gated": after, "flags": decision.flags,
                "error": "false_positive" if after and not truth
                    else "false_negative" if not after and truth else "",
            })
        return {
            "dataset": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "kind": "SYNTHETIC_REGRESSION_NOT_REAL_WORLD_ACCURACY",
            "n": len(fixtures),
            "baseline": confusion(baseline, expected),
            "quality_gated": confusion(filtered, expected),
            "per_language": {lang: {
                "n": len(data["expected"]),
                "baseline": confusion(data["baseline"], data["expected"]),
                "quality_gated": confusion(data["filtered"], data["expected"]),
            } for lang, data in langs.items()},
            "errors": [x for x in cases if x["error"]],
        }
    finally:
        if old_env is None:
            os.environ.pop("WISHCATCHER_CONTEXT_LLM_ENABLED", None)
        else:
            os.environ["WISHCATCHER_CONTEXT_LLM_ENABLED"] = old_env


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--dataset", type=Path, default=ROOT / "benchmarks/context_gold_v1.jsonl")
    cli.add_argument("--output", type=Path)
    cli.add_argument("--min-precision", type=float, default=None)
    cli.add_argument("--min-recall", type=float, default=None)
    args = cli.parse_args()
    report = asyncio.run(evaluate(args.dataset.resolve()))
    content = json.dumps(report, indent=2, ensure_ascii=False)
    print(content)
    if args.output:
        args.output.write_text(content + "\n", encoding="utf-8")
    score = report["quality_gated"]
    if ((args.min_precision is not None and score["precision"] < args.min_precision)
            or (args.min_recall is not None and score["recall"] < args.min_recall)):
        sys.exit(1)


if __name__ == "__main__":
    main()
