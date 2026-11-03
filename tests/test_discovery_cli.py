"""Real CLI smoke for login-free, operator-permitted JSONL discovery."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.wishcatcher.discovery.worker import schedule_config


class DiscoveryCLITests(unittest.TestCase):
    def test_import_run_and_cluster_cli_without_external_network(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            document = folder / "approved.jsonl"
            document.write_text("\n".join(json.dumps({
                "post_id": f"case-{i}",
                "post_author": f"person-{i}",
                "post_text": "I tried several accounting apps. They are too expensive.",
                "comments": [{"id": f"reply-{i}", "author": f"person-{i}",
                              "text": "I want invoice automation without wasting hours each day."}],
            }) for i in (1, 2)) + "\n", encoding="utf-8")
            env = {
                **os.environ,
                "WISHCATCHER_CONTEXT_LLM_ENABLED": "0",
                "WISHCATCHER_IMPORTED_DATA_APPROVED": "1",
                "WISHCATCHER_IMPORT_JSONL": str(document),
                "WISHCATCHER_DISCOVERY_DB": str(folder / "discovery.db"),
                "WISHCATCHER_RAG_DB": str(folder / "knowledge.db"),
            }
            script = ROOT / "scripts" / "discover.py"
            outcome = subprocess.run(
                [sys.executable, str(script), "run", "--sources", "approved_jsonl",
                 "--limit", "5"], env=env, text=True, capture_output=True,
                cwd=ROOT, timeout=30,
            )
            self.assertEqual(outcome.returncode, 0, outcome.stderr)
            result = json.loads(outcome.stdout)
            self.assertEqual(result["inserted"], 2, result)
            self.assertEqual(result["clusters"][0]["known_actors"], 2)
            self.assertEqual(result["clusters"][0]["market_demand"], "UNKNOWN")

            listing = subprocess.run(
                [sys.executable, str(script), "clusters"], env=env,
                text=True, capture_output=True, cwd=ROOT, timeout=10,
            )
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertEqual(len(json.loads(listing.stdout)["clusters"]), 1)

    def test_unapproved_imports_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "approved.jsonl"
            file.write_text('{"post_id":"x","post_text":"Hello"}\n')
            env = {
                **os.environ,
                "WISHCATCHER_IMPORTED_DATA_APPROVED": "0",
                "WISHCATCHER_IMPORT_JSONL": str(file),
                "WISHCATCHER_DISCOVERY_DB": str(Path(directory) / "discovery.db"),
            }
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "discover.py"),
                 "run", "--sources", "approved_jsonl"],
                env=env, text=True, capture_output=True, cwd=ROOT, timeout=10,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("failed", result.stdout)

    def test_worker_does_not_enable_arbitrary_platforms(self):
        with patch.dict(os.environ, {"WISHCATCHER_DISCOVERY_SOURCES": "facebook_private"}):
            with self.assertRaises(ValueError):
                schedule_config()
        with patch.dict(os.environ, {
            "WISHCATCHER_DISCOVERY_SOURCES": "hn_ask,hn_show",
            "WISHCATCHER_DISCOVERY_INTERVAL_SEC": "10",
            "WISHCATCHER_DISCOVERY_PER_SOURCE": "100",
        }):
            names, interval, limit, contexts = schedule_config()
            self.assertEqual(names, ["hn_ask", "hn_show"])
            self.assertEqual(interval, 3600)
            self.assertEqual(limit, 10)


if __name__ == "__main__":
    unittest.main()
