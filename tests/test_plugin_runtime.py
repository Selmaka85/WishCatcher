"""Provider-free plugin API / local graph RAG / optional research regression tests."""
import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.wishcatcher.integrations.plugin_runtime import (
    BraveWebSearch, MCPResearchBridge, SQLiteGraphRAG, WishCatcherPlugin,
)


class FakeSearch:
    def __init__(self):
        self.calls = []

    async def search(self, query, *, limit=5):
        self.calls.append((query, limit))
        return [{"source_type": "fake_research", "snippet": "Unverified external information"}]


def sample():
    return {
        "post_id": "thread1", "post_author": "original",
        "post_text": "Am incercat trei programe de contabilitate. Toate sunt o porcarie.",
        "comments": [
            {"id": "c1", "author": "original", "text":
             "Primul era scump, al doilea complicat, iar al treilea nu se conecta cu banca."},
            {"id": "c2", "author": "original", "text":
             "Vreau sa termin facturile fara sa pierd doua ore seara."},
        ],
    }


class GraphRAGTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = SQLiteGraphRAG(str(Path(self.tmp.name) / "rag.sqlite3"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_index_search_and_metadata(self):
        self.db.put(
            "docA", "Small firms need automated invoice synchronization and accounting",
            source="test", metadata={"verified": False}
        )
        hits = self.db.retrieve("invoice accounting automation")
        self.assertEqual(hits[0]["id"], "docA")
        self.assertEqual(hits[0]["source"], "test")
        self.assertFalse(hits[0]["metadata"]["verified"])
        self.assertEqual(hits[0]["matched_via"], "lexical")

    def test_graph_link_expands_relevant_document(self):
        self.db.put("a", "Accounting invoices")
        self.db.put("b", "Bank integration connection issues")
        self.db.link("a", "b", "depends_on")
        hits = self.db.retrieve("accounting", graph_hops=1)
        self.assertIn("a", [h["id"] for h in hits])
        self.assertIn("b", [h["id"] for h in hits])
        expanded = next(h for h in hits if h["id"] == "b")
        self.assertEqual(expanded["matched_via"], "graph")

    def test_replace_document_index_without_duplicates(self):
        self.db.put("a", "Old billing problem")
        self.db.put("a", "New logistics problem")
        self.assertFalse(self.db.retrieve("billing"))
        self.assertEqual(len(self.db.retrieve("logistics")), 1)

    def test_reject_invalid_document(self):
        with self.assertRaises(ValueError):
            self.db.put("", "some data")


class PluginSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_default_does_not_call_remote_tools(self):
        web = FakeSearch()
        mcp = FakeSearch()
        plugin = WishCatcherPlugin(web_search=web, mcp_search=mcp)
        out = await plugin.analyze(sample())
        self.assertTrue(out.frame["actionable"])
        self.assertEqual(out.external_research, [])
        self.assertEqual(web.calls, [])
        self.assertEqual(mcp.calls, [])

    async def test_explicit_research_uses_only_registered_adapters(self):
        web = FakeSearch()
        mcp = FakeSearch()
        plugin = WishCatcherPlugin(web_search=web, mcp_search=mcp)
        out = await plugin.analyze(sample(), research=True)
        self.assertEqual(len(web.calls), 1)
        self.assertEqual(len(mcp.calls), 1)
        self.assertEqual(len(out.external_research), 2)
        self.assertEqual(out.frame["primary_actor"], "original")

    async def test_no_research_for_nonactionable_person(self):
        web = FakeSearch()
        plugin = WishCatcherPlugin(web_search=web)
        out = await plugin.analyze({"post_id": "x", "post_text": "Hello"}, research=True)
        self.assertEqual(web.calls, [])
        self.assertFalse(out.frame["actionable"])

    async def test_local_rag_knowledge_is_separate_from_author_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            rag = SQLiteGraphRAG(str(Path(d) / "rag.sqlite3"))
            rag.put("accounting-guide", "Accounting bank invoice problems are common")
            plugin = WishCatcherPlugin(rag=rag)
            out = await plugin.analyze(sample(), retrieve_knowledge=True)
            self.assertTrue(out.knowledge)
            self.assertEqual(out.knowledge[0]["source"], "local")
            self.assertFalse(any(
                e["message_id"] == "accounting-guide" for e in out.frame["evidence"]
            ))

    async def test_opt_in_memory_persists_problem_without_raw_personal_profile(self):
        with tempfile.TemporaryDirectory() as d:
            rag = SQLiteGraphRAG(str(Path(d) / "rag.sqlite3"))
            plugin = WishCatcherPlugin(rag=rag)
            empty = await plugin.analyze(sample())
            self.assertIsNone(empty.memory_record_id)
            self.assertEqual(rag.retrieve("accounting"), [])

            saved = await plugin.analyze(sample(), remember=True)
            self.assertTrue(saved.memory_record_id.startswith("wish:"))
            records = rag.retrieve("accounting", graph_hops=1)
            doc = next(x for x in records if x["id"] == saved.memory_record_id)
            self.assertEqual(doc["source"], "wishcatcher_context")
            self.assertNotIn("original", doc["excerpt"])
            self.assertIn("Goal:", doc["excerpt"])
            self.assertFalse(doc["metadata"]["needs_review"] is False)

    async def test_no_network_with_default_web_adapter(self):
        with patch.dict(os.environ, {
            "WISHCATCHER_WEB_SEARCH_ENABLED": "0",
            "WISHCATCHER_BRAVE_API_KEY": "secret",
        }):
            self.assertEqual(await BraveWebSearch().search("accounting"), [])

    async def test_unallowlisted_mcp_tool_never_called(self):
        with patch.dict(os.environ, {
            "WISHCATCHER_MCP_ENABLED": "1",
            "WISHCATCHER_MCP_ENDPOINT": "http://127.0.0.1:9000/mcp",
            "WISHCATCHER_MCP_SEARCH_TOOL": "delete_all_files",
            "WISHCATCHER_MCP_READ_ONLY_TOOLS": "search",
        }):
            tool = MCPResearchBridge()
            self.assertFalse(tool._permitted())
            self.assertEqual(await tool.search("test"), [])

    async def test_remote_mcp_requires_tls_and_explicit_optin(self):
        with patch.dict(os.environ, {
            "WISHCATCHER_MCP_ENABLED": "1",
            "WISHCATCHER_MCP_ENDPOINT": "https://mcp.example.org/mcp",
            "WISHCATCHER_MCP_SEARCH_TOOL": "search",
            "WISHCATCHER_MCP_READ_ONLY_TOOLS": "search",
            "WISHCATCHER_MCP_ALLOW_REMOTE": "0",
        }):
            self.assertFalse(MCPResearchBridge()._permitted())


if __name__ == "__main__":
    unittest.main()
