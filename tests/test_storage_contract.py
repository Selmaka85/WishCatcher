"""Persistent evidence and plugin->Genesis bridge contract regression."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.api.models import WishData
from app.storage.wish_storage import WishStorage


class PersistentWishTests(unittest.TestCase):
    def test_evidence_roundtrips_through_json_storage(self):
        with tempfile.TemporaryDirectory() as d:
            store = WishStorage(d)
            frame = {
                "source_id": "thread-a", "primary_actor": "owner",
                "intent": "Finish invoicing quickly",
                "evidence": [{"message_id": "c1", "author": "owner",
                              "excerpt": "The third app cannot sync bank data"}],
                "actionable": True,
            }
            wish = WishData(
                id="wish-a", intent=frame["intent"], source="manual",
                domain="accounting", score=0.7, business_score=0.0,
                feasibility="unverified", technologies=[],
                timestamp=datetime.now(timezone.utc), context_frame=frame,
                structured={"problem": "Too much manual bookkeeping"},
            )
            store.save_wishes([wish])
            result = store.get_wish("wish-a")
            self.assertIsNotNone(result)
            self.assertEqual(result.context_frame, frame)
            self.assertEqual(result.structured["problem"], "Too much manual bookkeeping")
            store.save_wishes([wish])
            self.assertEqual(len(store.load_all_wishes()), 1)

    def test_configurable_storage_dir(self):
        with tempfile.TemporaryDirectory() as d:
            original = os.environ.get("WISHCATCHER_WISH_DIR")
            try:
                os.environ["WISHCATCHER_WISH_DIR"] = d
                self.assertEqual(WishStorage().storage_dir, Path(d))
            finally:
                if original is None:
                    os.environ.pop("WISHCATCHER_WISH_DIR", None)
                else:
                    os.environ["WISHCATCHER_WISH_DIR"] = original

    def test_cli_analyzes_example_without_credentials(self):
        script = ROOT / "scripts" / "wishcatcher_cli.py"
        example = ROOT / "examples" / "accounting_thread.json"
        p = subprocess.run(
            [sys.executable, str(script), "analyze", str(example)],
            cwd=ROOT, capture_output=True, text=True, timeout=20,
            env={**os.environ, "WISHCATCHER_CONTEXT_LLM_ENABLED": "0"},
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertTrue(result["frame"]["actionable"])
        self.assertEqual(result["frame"]["domain"], "accounting")
        self.assertIn("facturile", result["frame"]["desired_outcome"])

    def test_cli_genesis_brief_has_no_fabricated_revenue(self):
        script = ROOT / "scripts" / "wishcatcher_cli.py"
        example = ROOT / "examples" / "accounting_thread.json"
        p = subprocess.run(
            [sys.executable, str(script), "solution", str(example)],
            cwd=ROOT, capture_output=True, text=True, timeout=20,
            env={**os.environ, "WISHCATCHER_CONTEXT_LLM_ENABLED": "0"},
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(result["status"], "UNVALIDATED_HYPOTHESIS")
        self.assertIsNone(result["financial_forecast"])


if __name__ == "__main__":
    unittest.main()
