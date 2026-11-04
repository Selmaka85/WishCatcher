"""No-network regression tests for the P1 human-annotation evaluation gate."""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_context_ab import compare, load_labeled_cases, local_interpreter


def example(case_id: str, label: bool) -> dict:
    return {
        "id": case_id, "label": label, "language": "en",
        "annotation": {
            "reviewer_id": "human-review-1",
            "source_url": "https://news.ycombinator.com/item?id=1",
            "evidence_ids": [case_id] if label else [],
        },
        "conversation": {
            "post_id": case_id,
            "post_author": "author",
            "post_title": "",
            "post_text": (
                "I waste hours manually exporting invoices and need automation."
                if label else
                "I wonder what Google's business model is."
            ),
            "comments": [],
        },
    }


class RealEvaluationTests(unittest.TestCase):
    def test_requires_annotation_and_minimum(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "human.jsonl"
            file.write_text(json.dumps(example("one", True)) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "at least 2"):
                load_labeled_cases(file, minimum=2)
            self.assertEqual(len(load_labeled_cases(file, minimum=1)), 1)

    def test_refuses_fake_evidence_and_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "human.jsonl"
            altered = example("one", True)
            altered["annotation"]["evidence_ids"] = ["someone_else"]
            file.write_text(json.dumps(altered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Human evidence"):
                load_labeled_cases(file, minimum=1)
            proper = example("one", True)
            file.write_text("\n".join([json.dumps(proper)] * 2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_labeled_cases(file, minimum=1)

    def test_remote_model_never_admitted(self):
        for bad in (
            "https://api.openai.com/v1/chat/completions",
            "https://127.0.0.1.evil.test/v1/chat/completions",
            "file:///v1/chat/completions",
            "http://localhost.evil:11434/v1/chat/completions",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                local_interpreter(bad, "qwen2.5:3b")
        local = local_interpreter(
            "http://127.0.0.1:11434/v1/chat/completions", "qwen2.5:3b"
        )
        self.assertTrue(local.enabled)
        self.assertFalse(local.allow_remote)

    def test_partial_local_model_never_claims_comparative_verdict(self):
        class UnavailableModel:
            async def resolve(self, messages):
                return None
        rows = [example("one", True), example("two", False)]
        report = asyncio.run(compare(rows, interpreter=UnavailableModel()))
        self.assertEqual(report["status"], "PARTIAL_MODEL_ADOPTION_NO_COMPARATIVE_VERDICT")
        self.assertEqual(report["local_model"]["model_frames"], 0)
        self.assertEqual(report["local_model"]["rule_fallback_frames"], 2)
        self.assertEqual(report["rules"]["n"], 2)
        self.assertEqual(report["market_demand"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
