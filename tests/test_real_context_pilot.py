"""No-provider tests for small real-source observational pilot contracts."""
import argparse
import asyncio
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pilot_real_context import (
    evaluate, run, select_balanced, summary_case,
)
sys.path.insert(0, str(ROOT / "backend"))
from app.wishcatcher.discovery.sources import SourceConversation


def example(ident, *, actor="author"):
    return SourceConversation(
        source="hackernews", source_id=ident,
        url="https://news.ycombinator.com/item?id=900",
        conversation={
            "post_id": ident, "post_author": actor, "post_title": "",
            "post_text": "I waste two hours every day manually exporting invoices.",
            "comments": [{
                "id": ident + "-reply", "author": actor, "timestamp": 2,
                "text": "I want simpler invoice automation to finish faster.",
            }],
        },
    )


class SourceSelectionTests(unittest.TestCase):
    def test_round_robin_keeps_exploratory_strata_and_dedupes(self):
        same = example("hn:900:actor:a")
        samples = {
            "explicit": [same, example("e2")],
            "workaround": [same, example("w2")],
            "friction": [example("f1")],
            "outcome": [example("o1")],
            "hn_ask_neutral": [example("n1")],
        }
        selected = select_balanced(samples, 5)
        self.assertEqual(len(selected), 5)
        self.assertEqual(
            [source.source_id for _, source in selected],
            ["hn:900:actor:a", "f1", "o1", "n1", "e2"],
        )

    def test_unregistered_source_url_cannot_be_published_in_pilot(self):
        unsafe = example("odd")
        unsafe.url = "https://some-other-forum.example.org/"
        self.assertEqual(
            select_balanced({"explicit": [unsafe]}, 3), []
        )


class PilotOutputTests(unittest.IsolatedAsyncioTestCase):
    async def test_unavailable_model_reports_fallback_and_no_gold_accuracy(self):
        class NoModel:
            async def resolve(self, messages):
                return None
        source = example("verified")
        result = await evaluate([("explicit", source)], NoModel())
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["model_adopted"], 0)
        self.assertEqual(result["fallback"], 1)
        self.assertEqual(result["cases"][0]["review_status"],
                         "UNLABELED_REAL_PUBLIC_SOURCE")
        self.assertEqual(result["cases"][0]["willingness_to_pay"], "UNKNOWN")
        self.assertNotIn("I waste", str(result))

    async def test_dry_injected_sources_do_not_fabricate_precision(self):
        class Feed:
            async def fetch(self, limit=4):
                return [example("hn:900:actor:real")]
        class NoModel:
            async def resolve(self, messages):
                return None
        args = argparse.Namespace(
            maximum=2, per_pack=2, local_url="",
            local_model="not_used"
        )
        # No external request: all source strata are injected.
        result = await run(
            args, sources={name: Feed() for name in (
                "explicit", "workaround", "friction", "outcome", "hn_ask_neutral"
            )},
            interpreter=NoModel(),
        )
        self.assertEqual(result["status"], "NO_MODEL_ADOPTION_DIAGNOSTIC")
        self.assertEqual(result["sample"]["n"], 1)
        self.assertIsNone(result["precision"])
        self.assertIsNone(result["recall"])
        self.assertEqual(result["human_gold_label_count"], 0)


if __name__ == "__main__":
    unittest.main()
