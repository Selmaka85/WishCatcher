#!/usr/bin/env python3
"""P1 optional real local LLM execution smoke on existing SYNTHETIC controls.

This is a cheap, falsifiable integration probe, NOT a human-annotated field
benchmark, real-world precision or market validation.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from scripts.evaluate_context_ab import evaluate_arm, local_interpreter


def balanced_fixture_sample(path: Path, per_stratum: int) -> list[dict]:
    buckets: dict[tuple[str, bool], list[dict]] = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row.get("label"), bool):
                raise ValueError("Expected explicit synthetic boolean label")
            key = (str(row.get("language")), row["label"])
            buckets.setdefault(key, []).append(row)
    selected = []
    for key in (("en", True), ("en", False), ("ro", True), ("ro", False)):
        if len(buckets.get(key, [])) < per_stratum:
            raise ValueError(f"Insufficient synthetic cases for {key}")
        selected.extend(buckets[key][:per_stratum])
    return selected


async def run(args: argparse.Namespace) -> dict:
    cases = balanced_fixture_sample(args.dataset, args.per_stratum)
    rules = await evaluate_arm(cases)
    model = local_interpreter(args.local_url, args.local_model)
    model.timeout_seconds = min(model.timeout_seconds, 120.0)
    llm = await evaluate_arm(cases, interpreter=model)
    result = {
        "kind": "SYNTHETIC_MODEL_EXECUTION_SMOKE_NOT_REAL_WORLD_ACCURACY",
        "n": len(cases),
        "models": {"rules": rules, "llm_with_fallback": llm},
        "model_adopted": llm["model_frames"],
        "model_fallback": llm["rule_fallback_frames"],
        "accuracy_comparison_allowed": False,
        "status": (
            "MODEL_OUTPUT_ADOPTED" if llm["model_frames"] > 0
            else "NO_VALID_MODEL_OUTPUT_MODEL_OR_INTEGRATION_FAILURE"
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path,
                        default=ROOT / "benchmarks/context_gold_v1.jsonl")
    parser.add_argument("--per-stratum", type=int, default=2)
    parser.add_argument("--local-url", default="http://127.0.0.1:11434/v1/chat/completions")
    parser.add_argument("--local-model", default="qwen2.5:1.5b")
    args = parser.parse_args()
    if not 1 <= args.per_stratum <= 3:
        parser.error("--per-stratum must be 1..3 for a bounded quick smoke")
    os.environ["WISHCATCHER_CONTEXT_ALLOW_REMOTE"] = "0"
    output = asyncio.run(run(args))
    print("P1_LOCAL_MODEL_SMOKE=" + json.dumps(output, ensure_ascii=False))
    if output["model_adopted"] == 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
