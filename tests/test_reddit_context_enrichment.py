"""Provider-free verification of Reddit thread enrichment and deduplication."""
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.wishcatcher.scraper.context_collector import ContextCollector, RedditContext


def post(identifier: str, *, comments=None) -> RedditContext:
    return RedditContext(
        post_id=identifier, post_title="Test", post_text="I wish there were better tools",
        post_author="owner", post_timestamp=1.0, post_upvotes=3,
        subreddit="test", comments=comments or [],
        metadata={"source_type": "reddit_search", "url": "/r/test/" + identifier},
    )


class RedditEnrichmentTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetches_full_thread_and_preserves_search_provenance(self):
        collector = ContextCollector()
        collector._collect_reddit_post_context = AsyncMock(return_value=post(
            "id1", comments=[{"id": "reply", "author": "owner",
                               "text": "I need automatic invoices"}]
        ))
        result = await collector._enrich_reddit_threads([post("id1")], max_threads=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].comments[0]["id"], "reply")
        self.assertEqual(result[0].metadata["source_type"], "reddit_search")
        collector._collect_reddit_post_context.assert_awaited_once_with("id1", "test")

    async def test_deduplicates_search_new_and_respects_fetch_cap(self):
        collector = ContextCollector()
        collector._collect_reddit_post_context = AsyncMock(return_value=None)
        contexts = [post("id1"), post("id1"), post("id2"), post("id3")]
        result = await collector._enrich_reddit_threads(contexts, max_threads=1)
        self.assertEqual([x.post_id for x in result], ["id1", "id2", "id3"])
        self.assertEqual(collector._collect_reddit_post_context.await_count, 1)

    async def test_fallback_retains_original_when_provider_fails(self):
        collector = ContextCollector()
        collector._collect_reddit_post_context = AsyncMock(side_effect=RuntimeError("blocked"))
        original = post("one")
        result = await collector._enrich_reddit_threads([original], max_threads=1)
        self.assertEqual(result, [original])


if __name__ == "__main__":
    unittest.main()
