"""Actual HTTP contract tests for standalone WishCatcher context server.

No provider credentials, network access, spaCy or historical backend needed.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import httpx

from app.plugin_app import app
from app.astra_genesis.context_bridge import GenesisContextBridge


def sample():
    return {
        "post_id": "acct1",
        "post_author": "person1",
        "post_text": "Am incercat trei programe de contabilitate. Toate sunt o porcarie.",
        "comments": [
            {"id": "a", "author": "person1",
             "text": "Primul era scump, al doilea complicat, al treilea nu se conecta cu banca."},
            {"id": "b", "author": "person1",
             "text": "Vreau sa termin facturile seara fara sa pierd doua ore."},
            {"id": "c", "author": "friend",
             "text": "Eu vreau ceva total diferit pentru o alta firma."},
        ],
    }


class ActualPluginAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch_env = patch.dict(os.environ, {
            "WISHCATCHER_PLUGIN_ACCESS_TOKEN": "test_only_secret_from_env",
            "WISHCATCHER_RAG_DB": str(Path(self.temp.name) / "rag.sqlite3"),
            "WISHCATCHER_WISH_DIR": str(Path(self.temp.name) / "wishes"),
            "WISHCATCHER_CONTEXT_LLM_ENABLED": "0",
            "WISHCATCHER_WEB_SEARCH_ENABLED": "0",
            "WISHCATCHER_MCP_ENABLED": "0",
        })
        self.patch_env.start()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        )
        self.auth = {"X-WishCatcher-Key": "test_only_secret_from_env"}

    async def asyncTearDown(self):
        await self.client.aclose()
        self.patch_env.stop()
        self.temp.cleanup()

    async def test_health_does_not_expose_configuration(self):
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("secret", str(response.json()).lower())

    async def test_missing_or_incorrect_token_rejected(self):
        self.assertEqual((await self.client.get("/api/context/config")).status_code, 401)
        self.assertEqual((await self.client.get(
            "/api/context/config", headers={"X-WishCatcher-Key": "wrong"}
        )).status_code, 401)

    async def test_server_fails_closed_when_no_token_configured(self):
        with patch.dict(os.environ, {"WISHCATCHER_PLUGIN_ACCESS_TOKEN": ""}):
            resp = await self.client.post(
                "/api/context/analyze", headers=self.auth, json={"conversation": sample()}
            )
            self.assertEqual(resp.status_code, 503)

    async def test_config_reports_capabilities_without_secret(self):
        result = await self.client.get("/api/context/config", headers=self.auth)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["rag"], "sqlite-fts5-graph")
        self.assertFalse(result.json()["llm_enabled"])
        self.assertNotIn("test_only_secret", result.text)
        self.assertFalse(result.json()["web_search_enabled"])

    async def test_end_to_end_api_analysis_evidence_and_genesis(self):
        payload = {"conversation": sample(), "retrieve_knowledge": True,
                   "research": False, "remember": True}
        resp = await self.client.post("/api/context/analyze", headers=self.auth, json=payload)
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertTrue(body["frame"]["actionable"])
        self.assertEqual(body["frame"]["primary_actor"], "person1")
        self.assertNotIn("friend", [e["author"] for e in body["frame"]["evidence"]])
        self.assertTrue(body["memory_record_id"].startswith("wish:"))

        genesis = await self.client.post(
            "/api/context/solution", headers=self.auth, json={"conversation": sample()}
        )
        self.assertEqual(genesis.status_code, 200, genesis.text)
        result = genesis.json()
        self.assertEqual(result["kind"], "genesis_opportunity_brief_v1")
        self.assertEqual(result["market_demand"], "UNKNOWN")
        self.assertIsNone(result["financial_forecast"])
        self.assertEqual(len(result["alternatives"]), 3)
        self.assertTrue(result["supporting_message_ids"])

    async def test_nonactionable_genesis_abstains(self):
        response = await self.client.post(
            "/api/context/solution", headers=self.auth,
            json={"conversation": {"post_id": "no", "post_text": "Hello world"}}
        )
        self.assertEqual(response.status_code, 422)

    async def test_document_ingestion_graph_and_search(self):
        for item in (
            {"id": "a", "text": "Accounting invoice banking integration", "source": "approved"},
            {"id": "b", "text": "Time-consuming reconciliation", "source": "approved"},
        ):
            added = await self.client.post("/api/context/knowledge", headers=self.auth, json=item)
            self.assertEqual(added.status_code, 200, added.text)
        linked = await self.client.post(
            "/api/context/knowledge/link", headers=self.auth,
            json={"source_id": "a", "target_id": "b", "relation": "related"}
        )
        self.assertEqual(linked.status_code, 200, linked.text)
        analysis = await self.client.post("/api/context/analyze", headers=self.auth,
            json={"conversation": sample(), "retrieve_knowledge": True}
        )
        self.assertEqual(analysis.status_code, 200)
        found = analysis.json()["knowledge"]
        self.assertTrue(found)
        self.assertIn("a", {hit["id"] for hit in found})

    async def test_invalid_or_huge_document_rejected(self):
        response = await self.client.post(
            "/api/context/knowledge", headers=self.auth, json={"id": "a", "text": ""}
        )
        self.assertEqual(response.status_code, 422)
        huge = await self.client.post(
            "/api/context/analyze", headers=self.auth,
            json={"conversation": {"post_id": "huge", "post_text": "X" * 200001}}
        )
        self.assertEqual(huge.status_code, 413)


class GenesisContracts(unittest.TestCase):
    def test_requires_source_evidence_and_actionable(self):
        with self.assertRaises(ValueError):
            GenesisContextBridge.compose({"actionable": True, "intent": "Test"})
        with self.assertRaises(ValueError):
            GenesisContextBridge.compose({
                "actionable": False, "intent": "Test",
                "evidence": [{"message_id": "m1"}],
            })


if __name__ == "__main__":
    unittest.main()
