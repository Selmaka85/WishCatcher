"""Provider-free tests for permissioned discovery, evidence quality and clustering."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.wishcatcher.contextual.context_resolver import ConversationContextResolver
from app.wishcatcher.contextual.quality import ContextQualityGate
from app.wishcatcher.discovery.pipeline import DiscoveryIndex, DiscoveryRunner, similarity
from app.wishcatcher.discovery.sources import (
    ApprovedJSONLSource, HackerNewsSource, SourceConversation, configured_source,
)
from app.wishcatcher.discovery.search_discovery import (
    BraveIndexDiscovery, OfficialThreadHydrator,
)
from app.wishcatcher.discovery.rss_source import PublicRSSSource


def thread(name="owner", post_id="p", *, title="", first=None, second=None):
    return {
        "post_id": post_id, "post_author": name, "post_title": title,
        "post_text": first or "I tried three accounting apps. They are too expensive.",
        "comments": [
            {"id": post_id + ":c1", "author": name,
             "text": second or "I want invoice automation without losing hours every day.",
             "timestamp": 2},
        ],
    }


def record(name="owner", post_id="p", *, source="approved_jsonl", first=None,
           second=None, thread_id=None):
    context = thread(name, post_id, first=first, second=second)
    if thread_id:
        context["metadata"] = {"thread_id": thread_id}
    return SourceConversation(
        source=source, source_id=post_id, url="https://example.org/" + post_id,
        conversation=context, source_type="operator_supplied",
    )


class FakeSource:
    def __init__(self, items):
        self.items = items
        self.calls = 0
    async def fetch(self, limit=5):
        self.calls += 1
        return self.items[:limit]


class BrokenSource:
    async def fetch(self, limit=5):
        raise RuntimeError("source unavailable")


class StubResponse:
    def __init__(self, data):
        self.data = data
        self.content = data.encode() if isinstance(data, str) else b""
        self.text = data if isinstance(data, str) else ""
    def raise_for_status(self):
        pass
    def json(self):
        return self.data


class StubHTTP:
    def __init__(self, values):
        self.values = values
    async def get(self, url, **kwargs):
        for suffix, result in self.values.items():
            if url.endswith(suffix):
                return StubResponse(result)
        raise AssertionError("Unexpected outbound route " + url)


class QualityGateTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.resolver = ConversationContextResolver()
        self.gate = ContextQualityGate()

    async def test_accounting_context_keeps_source_evidence(self):
        conv = thread()
        frame = (await self.resolver.resolve(conv)).to_dict()
        quality = self.gate.assess(conv, frame)
        self.assertTrue(quality.accepted)
        self.assertIn("p", quality.field_evidence["problem"])
        self.assertIn("p:c1", quality.field_evidence["intent"])

    async def test_fiction_rejected_even_if_model_guess_was_actionable(self):
        conv = thread(first="I tried three accounting apps, just kidding, they are expensive.")
        frame = (await self.resolver.resolve(conv)).to_dict()
        self.assertFalse(self.gate.assess(conv, frame).accepted)

    async def test_latest_problem_resolved_overrides_old_complaint(self):
        conv = thread()
        conv["comments"].append({
            "id": "resolved", "author": "owner", "timestamp": 3,
            "text": "Problem solved. It works now.",
        })
        frame = (await self.resolver.resolve(conv)).to_dict()
        outcome = self.gate.assess(conv, frame)
        self.assertFalse(outcome.accepted)
        self.assertIn("superseded_problem_resolved", outcome.flags)

    async def test_third_party_report_not_personal_wish(self):
        conv = thread(first="My friend wants accounting software but it is expensive.")
        frame = (await self.resolver.resolve(conv)).to_dict()
        self.assertFalse(self.gate.assess(conv, frame).accepted)

    async def test_other_authors_evidence_not_attributed(self):
        conv = thread()
        conv["comments"].append({"id": "other", "author": "other",
                                 "text": "I want an expensive different CRM."})
        frame = (await self.resolver.resolve(conv)).to_dict()
        frame["evidence"].append({"message_id": "other", "author": "other",
                                  "excerpt": "I want an expensive different CRM"})
        self.assertFalse(self.gate.assess(conv, frame).accepted)


class ClusterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.index = DiscoveryIndex(str(Path(self.tmp.name) / "discovery.db"))

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def test_independent_threads_promote_corroboration_not_market_validation(self):
        feed = FakeSource([record("owner1", "p1"), record("owner2", "p2")])
        engine = DiscoveryRunner(index=self.index, sources={"hn_ask": feed})
        result = await engine.run(["hn_ask"], max_per_source=5)
        self.assertEqual(result["inserted"], 2, result)
        clusters = self.index.clusters()
        self.assertEqual(len(clusters), 1, clusters)
        self.assertEqual(clusters[0]["known_actors"], 2)
        self.assertEqual(clusters[0]["unique_threads"], 2)
        self.assertEqual(clusters[0]["status"], "CORROBORATED_NEED_HYPOTHESIS")
        self.assertEqual(clusters[0]["market_demand"], "UNKNOWN")
        self.assertEqual(clusters[0]["willingness_to_pay"], "UNKNOWN")
        again = await engine.run(["hn_ask"], max_per_source=5)
        self.assertEqual(again["inserted"], 0)
        self.assertEqual(len(self.index.clusters()), 1)

    async def test_multiple_actors_in_one_thread_not_independent_threads(self):
        a = record("alice", "hn:one:actor:alice", thread_id="hn:one")
        b = record("bob", "hn:one:actor:bob", thread_id="hn:one")
        runner = DiscoveryRunner(index=self.index, sources={"hn_ask": FakeSource([a, b])})
        result = await runner.run(["hn_ask"])
        self.assertEqual(result["inserted"], 2)
        cluster = self.index.clusters()[0]
        self.assertEqual(cluster["known_actors"], 2)
        self.assertEqual(cluster["unique_threads"], 1)
        self.assertEqual(cluster["status"], "SINGLE_SOURCE_HYPOTHESIS")

    async def test_distinct_problems_in_same_domain_remain_separate(self):
        self.assertEqual(similarity(
            {"domain": "accounting", "problem": "Need low tax export overhead", "intent": "tax data"},
            {"domain": "accounting", "problem": "Bank invoice sync missing", "intent": "automated invoice"},
        ), 0.0)

    async def test_source_failure_does_not_stop_healthy_source(self):
        runner = DiscoveryRunner(index=self.index, sources={
            "hn_ask": BrokenSource(), "hn_show": FakeSource([record()]),
        })
        result = await runner.run(["hn_ask", "hn_show"])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["inserted"], 1)
        self.assertTrue(result["errors"])

    async def test_unknown_source_rejected_before_network(self):
        with self.assertRaises(ValueError):
            await DiscoveryRunner(index=self.index).run(["facebook_login"])
        with self.assertRaises(PermissionError):
            configured_source("reddit")

    async def test_fiction_and_resolved_issues_are_not_persisted(self):
        items = [
            record("alice", "fiction", first="Just kidding: these accounting apps are too expensive."),
            record("bob", "solved", second="Problem solved. I want nothing now."),
        ]
        runner = DiscoveryRunner(index=self.index, sources={"hn_ask": FakeSource(items)})
        result = await runner.run(["hn_ask"])
        self.assertEqual(result["inserted"], 0)
        self.assertEqual(self.index.clusters(), [])


class PublicSourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_hacker_news_reader_preserves_replies_and_actor_boundaries(self):
        fake = StubHTTP({
            "item/10.json": {"type": "story", "id": 10, "by": "alice",
                             "title": "My accounting app is expensive",
                             "text": "I need automated invoices", "kids": [11, 12]},
            "item/11.json": {"type": "comment", "id": 11, "by": "alice",
                             "text": "I waste hours doing them", "parent": 10},
            "item/12.json": {"type": "comment", "id": 12, "by": "bob",
                             "text": "I need bank integration", "parent": 10},
        })
        hn = HackerNewsSource(client=fake)
        result = await hn._story(fake, 10)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].conversation["post_author"], "alice")
        self.assertEqual(len(result[0].conversation["comments"]), 2)
        self.assertEqual(result[1].conversation["post_author"], "bob")
        self.assertEqual(result[1].conversation["post_text"], "I need bank integration")
        self.assertEqual(result[1].conversation["metadata"]["thread_id"], "hn:10")

    async def test_search_result_is_not_a_context_until_officially_hydrated(self):
        self.assertEqual(OfficialThreadHydrator.hn_item_id(
            "https://news.ycombinator.com/item?id=3344"), 3344)
        self.assertIsNone(OfficialThreadHydrator.hn_item_id(
            "https://facebook.com/private/discussion"))
        self.assertIsNone(OfficialThreadHydrator.hn_item_id(
            "https://localhost/item?id=3344"))

    async def test_brave_search_mock_collects_index_leads_only(self):
        search = BraveIndexDiscovery(
            api_key="fake", enabled=True,
            client=StubHTTP({
                "/search": {"web": {"results": [
                    {"url": "https://news.ycombinator.com/item?id=4455",
                     "title": "Forum conversation", "description": "I need a tool"},
                    {"url": "http://unsafe.example.com/", "title": "Bad", "description": "bad"},
                ]}},
            })
        )
        leads = await search.search(language="en", max_queries=1)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0].source_status, "INDEX_ONLY_UNVERIFIED")

    async def test_rss_parse_single_entry_not_fake_thread(self):
        xml = '<rss><channel><item><title>Expensive accounting app</title>' + (
            '<description>I want faster invoicing</description>'
            '<link>https://example.org/post/1</link><guid>1</guid>'
            '<author>alice</author></item></channel></rss>'
        )
        reader = PublicRSSSource("https://example.org/feed.xml", approved=True)
        result = reader._parse(xml, 5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].conversation["comments"], [])
        self.assertIn("SINGLE_SYNDICATED_ENTRY", result[0].conversation["metadata"]["coverage"])

    async def test_jsonl_requires_explicit_operator_permission(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.jsonl"
            path.write_text(json.dumps(thread()) + "\n")
            with self.assertRaises(PermissionError):
                ApprovedJSONLSource(str(path), approved=False)
            items = await ApprovedJSONLSource(str(path), approved=True).fetch()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].conversation["post_author"], "owner")


if __name__ == "__main__":
    unittest.main()
