#!/usr/bin/env python3
"""No-secret P1 transport/JSON grounding probe on a tracked SYNTHETIC case.

Shows *why* Ollama model output was not adopted by ConversationContextResolver.
No real user content, external network, paid provider or persistence.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.wishcatcher.contextual.context_resolver import (
    ContextStateBuilder, ConversationContextResolver, OpenAICompatibleContextInterpreter,
)
from app.wishcatcher.contextual.quality import ContextQualityGate


async def main() -> None:
    import httpx
    fixture = next(
        json.loads(line)
        for line in (ROOT / "benchmarks/context_gold_v1.jsonl").read_text(
            encoding="utf-8"
        ).splitlines() if line.strip()
    )
    ctx = fixture["conversation"]
    messages = ContextStateBuilder.flatten(ctx)
    model = OpenAICompatibleContextInterpreter()
    model.enabled = True
    model.allow_remote = False
    model.endpoint = "http://127.0.0.1:11434/v1/chat/completions"
    model.model = "qwen2.5:1.5b"
    raw_messages = [{
        "id": m.message_id, "source_id": m.message_id,
        "author": m.author, "parent_id": m.parent_id,
        "timestamp": m.timestamp, "text": m.text,
    } for m in messages]
    request = {
        "model": model.model,
        "messages": [
            {"role": "system", "content": model.SYSTEM},
            {"role": "user", "content": json.dumps({
                "primary_actor": messages[0].author,
                "previous_state": {},
                "messages": raw_messages,
            }, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
    }
    started = time.monotonic()
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(model.endpoint, json=request)
    duration = round(time.monotonic() - started, 2)
    diagnostic = {
        "status_code": response.status_code, "elapsed_sec": duration,
        "synthetic_source": fixture.get("id"),
    }
    if response.status_code != 200:
        diagnostic["response_preview"] = response.text[:500]
    else:
        parsed = response.json()
        message = parsed.get("choices", [{}])[0].get("message", {})
        value = message.get("content")
        try:
            outcome = json.loads(value) if isinstance(value, str) else None
        except ValueError:
            outcome = None
        diagnostic.update({
            "finish_reason": parsed.get("choices", [{}])[0].get("finish_reason"),
            "usage": parsed.get("usage"),
            "raw_length": len(value) if isinstance(value, str) else None,
            # Input contains only a tracked synthetic fixture. No real authors.
            "synthetic_raw_preview": value[:2400] if isinstance(value, str) else None,
            "json_object": isinstance(outcome, dict),
            "json_keys": sorted(outcome) if isinstance(outcome, dict) else [],
            "returned_evidence_ids": (
                outcome.get("evidence_ids") if isinstance(outcome, dict) else None
            ),
        })
    resolved = (await ConversationContextResolver(interpreter=model).resolve(ctx)).to_dict()
    quality = ContextQualityGate().assess(ctx, resolved)
    diagnostic.update({
        "interpreter_method": resolved.get("interpretation_method"),
        "adopted_actionable": resolved.get("actionable"),
        "quality_status": quality.status,
        "quality_flags": quality.flags,
    })
    print("P1_OLLAMA_DIAGNOSTIC=" + json.dumps(diagnostic, ensure_ascii=False))
    if response.status_code != 200:
        raise SystemExit(2)


if __name__ == "__main__":
    asyncio.run(main())
