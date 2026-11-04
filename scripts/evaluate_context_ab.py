#!/usr/bin/env python3
"""P1: paired, source-grounded WishCatcher evaluation; no implicit provider calls.

The existing scripts/evaluate_context.py remains the synthetic regression gate.
This evaluator requires *operator-labeled* real cases and keeps a strict
distinction between a rule fallback and a valid local-model interpretation.
It never asserts market demand, real-world representativeness or calibrated
confidence from these observations.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from scripts.evaluate_context import confusion
from app.wishcatcher.contextual.context_resolver import (
    ContextStateBuilder, ConversationContextResolver,
    OpenAICompatibleContextInterpreter,
)
from app.wishcatcher.contextual.quality import ContextQualityGate

_LOCAL = {"localhost", "127.0.0.1", "::1", "host.docker.internal"}
_LANGUAGES = {"ro", "en"}


def load_labeled_cases(path: Path, *, minimum: int = 100) -> List[Dict[str, Any]]:
    """Fail closed on missing human annotation/provenance; never invent labels."""
    cases: List[Dict[str, Any]] = []
    identities: set[str] = set()
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}") from exc
            if not isinstance(row, dict) or type(row.get("label")) is not bool:
                raise ValueError(f"Missing boolean human label at line {line_number}")
            if row.get("language") not in _LANGUAGES:
                raise ValueError(f"Missing RO/EN language at line {line_number}")
            if not isinstance(row.get("conversation"), dict):
                raise ValueError(f"Missing conversation at line {line_number}")
            annotation = row.get("annotation")
            if (not isinstance(annotation, dict)
                    or not str(annotation.get("reviewer_id") or "").strip()
                    or not str(annotation.get("source_url") or "").strip()):
                raise ValueError(f"Missing annotation provenance at line {line_number}")
            root = ContextStateBuilder.flatten(row["conversation"])
            if not root or not root[0].text.strip():
                raise ValueError(f"Missing original-source message at line {line_number}")
            known_ids = {message.message_id for message in root
                         if message.author == root[0].author}
            refs = annotation.get("evidence_ids")
            if (not isinstance(refs, list)
                    or (row["label"] and not refs)
                    or any(not isinstance(ref, str) or ref not in known_ids for ref in refs)):
                raise ValueError(f"Human evidence must cite primary actor messages at line {line_number}")
            source_id = str(row.get("id") or "").strip()
            if not source_id or source_id in identities:
                raise ValueError(f"Duplicate/missing case ID at line {line_number}")
            identities.add(source_id)
            cases.append(row)
    if len(cases) < minimum:
        raise ValueError(f"Expected at least {minimum} independently annotated cases, got {len(cases)}")
    return cases


def local_interpreter(url: str, model: str) -> OpenAICompatibleContextInterpreter:
    parsed = urlparse(url)
    if (parsed.scheme not in {"http", "https"}
            or parsed.hostname not in _LOCAL
            or not parsed.path.endswith("/chat/completions")
            or not model.strip()
            or parsed.username or parsed.password):
        raise ValueError("P1 accepts only an explicit local OpenAI-compatible chat endpoint")
    interpreter = OpenAICompatibleContextInterpreter()
    interpreter.endpoint = url
    interpreter.model = model
    interpreter.enabled = True
    interpreter.allow_remote = False
    interpreter.api_key = ""
    if not interpreter._permitted():
        raise ValueError("Local model endpoint was rejected by provider policy")
    return interpreter


async def evaluate_arm(rows: List[Dict[str, Any]], *,
                       interpreter: Optional[OpenAICompatibleContextInterpreter] = None
                       ) -> Dict[str, Any]:
    resolver = ConversationContextResolver(interpreter=interpreter)
    # Enforce rules-only mode without touching process-global environment.
    if interpreter is None:
        resolver.interpreter.enabled = False
    gate = ContextQualityGate()
    predicted: List[bool] = []
    truth: List[bool] = []
    languages: Dict[str, Dict[str, List[bool]]] = {}
    model_frames = 0
    rejection_reasons: Dict[str, int] = {}
    errors: List[Dict[str, Any]] = []
    started = time.monotonic()
    for row in rows:
        frame = (await resolver.resolve(row["conversation"])).to_dict()
        result = gate.assess(row["conversation"], frame)
        observed_model = frame.get("interpretation_method") == "llm_contextual"
        model_frames += int(observed_model)
        predicted.append(bool(result.accepted))
        truth.append(row["label"])
        bucket = languages.setdefault(row["language"], {"predicted": [], "truth": []})
        bucket["predicted"].append(bool(result.accepted))
        bucket["truth"].append(row["label"])
        for reason in result.flags:
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        if result.accepted != row["label"]:
            errors.append({
                # Hash the case ID. No raw transcript or author metadata in reports.
                "case_hash": hashlib.sha256(row["id"].encode("utf-8")).hexdigest()[:16],
                "kind": "false_positive" if result.accepted else "false_negative",
                "method": frame.get("interpretation_method", "unknown"),
            })
    return {
        "n": len(rows), "metrics": confusion(predicted, truth),
        "per_language": {lang: confusion(v["predicted"], v["truth"])
                         for lang, v in sorted(languages.items())},
        "model_frames": model_frames,
        "rule_fallback_frames": len(rows) - model_frames,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "rejection_flags": dict(sorted(rejection_reasons.items())),
        "errors": errors,
    }


async def compare(rows: List[Dict[str, Any]], *,
                  interpreter: Optional[OpenAICompatibleContextInterpreter] = None
                  ) -> Dict[str, Any]:
    rules = await evaluate_arm(rows)
    result: Dict[str, Any] = {
        "status": "RULES_ONLY_NO_MODEL_VERDICT",
        "kind": "HUMAN_ANNOTATED_OBSERVATIONAL_NOT_REPRESENTATIVE",
        "n": len(rows),
        "rules": rules,
        "market_demand": "UNKNOWN",
    }
    if interpreter is not None:
        local = await evaluate_arm(rows, interpreter=interpreter)
        # A local request may silently fall back to rules if the model is
        # unavailable, returns malformed JSON, or cannot ground a claim.
        # Do not attribute those predictions to an actual model.
        result["local_model"] = local
        result["status"] = (
            "PAIRED_LOCAL_MODEL_MEASURED"
            if local["model_frames"] == len(rows)
            else "PARTIAL_MODEL_ADOPTION_NO_COMPARATIVE_VERDICT"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--minimum", type=int, default=100)
    parser.add_argument("--local-url", default="")
    parser.add_argument("--local-model", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.minimum < 1:
        parser.error("--minimum must be positive")
    if bool(args.local_url) != bool(args.local_model):
        parser.error("Provide both --local-url and --local-model, or neither")
    rows = load_labeled_cases(args.dataset.resolve(), minimum=args.minimum)
    interpreter = (local_interpreter(args.local_url, args.local_model)
                   if args.local_url else None)
    result = asyncio.run(compare(rows, interpreter=interpreter))
    serialized = json.dumps(result, indent=2, ensure_ascii=False)
    print(serialized)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    if interpreter and result["status"] != "PAIRED_LOCAL_MODEL_MEASURED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
