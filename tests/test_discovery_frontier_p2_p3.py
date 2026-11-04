"""P2/P3 source coverage and revision contracts (provider-free, no migration)."""
from __future__ import annotations

import copy
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.wishcatcher.discovery.need_search import HackerNewsNeedSearch
from app.wishcatcher.discovery.pipeline import (
    DiscoveryIndex, DiscoveryRunner, conversation_revision_fingerprint,
)
from app.wishcatcher.discovery.sources import SourceConversation


def sample() -> SourceConversation:
    return SourceConversation(
        source="hackernews", source_id="hn:900:actor:speaker",
        url="https://news.ycombinator.com/item?id=900",
        conversation={
            "post_id": "hn:101", "post_author": "speaker",
            "post_title": "",
            "post_text": "I waste hours manually exporting invoices.",
            "post_timestamp": 123,
            "comments": [
                {"id": "hn:102", "author": "speaker",
                 "text": "I need a simpler workflow.", "parent_id": "hn:101",
                 "timestamp": 124},
            ],
        },
    )


class QueryPackTests(unittest.TestCase):
    def test_p2_default_does_not_drift(self):
        self.assertEqual(HackerNewsNeedSearch().query_pack, "explicit")
        self.assertEqual(HackerNewsNeedSearch().queries,
                         HackerNewsNeedSearch.DEFAULT_QUERIES)
        for pack in ("workaround", "friction", "outcome"):
            with self.subTest(pack=pack):
                scout = HackerNewsNeedSearch(query_pack=pack)
                self.assertEqual(scout.query_pack, pack)
                self.assertGreaterEqual(len(scout.queries), 4)
                self.assertLessEqual(scout.max_queries, 6)
                self.assertNotEqual(scout.queries, HackerNewsNeedSearch.DEFAULT_QUERIES)
        with self.assertRaises(ValueError):
            HackerNewsNeedSearch(query_pack="unapproved-network-source")

    def test_explicit_custom_search_queries_preserve_existing_contract(self):
        scout = HackerNewsNeedSearch(queries=["I wish there was"], max_queries=1)
        self.assertEqual(scout.queries, ("I wish there was",))
        self.assertEqual(scout.max_queries, 1)


class RevisionTests(unittest.TestCase):
    def test_p3_fingerprint_is_stable_and_changes_on_edit(self):
        first = sample()
        first_hash = conversation_revision_fingerprint(first)
        self.assertEqual(len(first_hash), 64)
        self.assertEqual(conversation_revision_fingerprint(copy.deepcopy(first)),
                         first_hash)
        next_version = copy.deepcopy(first)
        next_version.conversation["comments"][0]["text"] = "I need a NEW workflow."
        self.assertNotEqual(conversation_revision_fingerprint(next_version),
                            first_hash)

    def test_p3_different_actors_never_share_source_identity(self):
        first = sample()
        next_actor = copy.deepcopy(first)
        next_actor.source_id = "hn:900:actor:someone_else"
        self.assertNotEqual(conversation_revision_fingerprint(next_actor),
                            conversation_revision_fingerprint(first))


class RunnerSelectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_env_pack_only_selects_a_registered_query_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            index = DiscoveryIndex(str(Path(directory) / "discovery.db"))
            runner = DiscoveryRunner(index=index)
            with (patch.dict(os.environ, {"WISHCATCHER_HN_QUERY_PACK": "friction"}),
                  patch("app.wishcatcher.discovery.pipeline.HackerNewsNeedSearch") as ctor):
                ctor.return_value.fetch = AsyncMock(return_value=[])
                self.assertEqual(await runner._get_source("hn_need_search", 2), [])
                ctor.assert_called_once_with(query_pack="friction")
                ctor.return_value.fetch.assert_awaited_once_with(limit=2)


if __name__ == "__main__":
    unittest.main()
