"""Provider-free tests for permissioned discovery, evidence quality and clustering."""
import json
import os
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

    async def test_live_google_flights_business_model_question_is_not_a_need(self):
        # Observed false positive in real public HN feed on 2026-11-04.
        # This test does not pretend we have the original full HN thread.
        conv = {
            "post_id": "hn:50358924", "post_author": "original",
            "post_title": "Ask HN: What is Google Flights' business model and has it changed recently?",
            "post_text": (
                "I'm wondering if anyone has any more info than I do regarding "
                "why Google offers Google Flights? As far as I know there's no "
                "paid version of the software and Google doesn't take a cut of sales."
            ),
            "comments": [],
        }
        # Gate must veto an over-permissive fallback interpretation, even
        # when it has a real message citation and a domain classification.
        fake_frame = {
            "actionable": True, "domain": "software",
            "intent": "How does Google Flights make money?",
            "problem": "What is Google Flights' business model?",
            "desired_outcome": "Understand the business model",
            "interpretation_method": "rules",
            "evidence": [{"message_id": "hn:50358924", "author": "original",
                          "excerpt": conv["post_text"]}],
        }
        outcome = self.gate.assess(conv, fake_frame)
        self.assertFalse(outcome.accepted)
        self.assertIn("informational_question_not_unmet_need", outcome.flags)

    async def test_how_do_i_fix_real_workflow_problem_is_not_rejected_as_curiosity(self):
        conv = {
            "post_id": "fix", "post_author": "owner",
            "post_title": "How can I automate manual invoicing?",
            "post_text": "I waste hours every day entering invoices manually.",
            "comments": [{"id": "c1", "author": "owner",
                          "text": "I want to automate invoicing to finish earlier."}],
        }
        frame = {
            "actionable": True, "domain": "accounting",
            "intent": "Automate manual invoicing",
            "problem": "I waste hours every day entering invoices manually.",
            "desired_outcome": "I want to automate invoicing to finish earlier.",
            "interpretation_method": "rules",
            "evidence": [
                {"message_id": "fix", "author": "owner", "excerpt": conv["post_text"]},
                {"message_id": "c1", "author": "owner",
                 "excerpt": conv["comments"][0]["text"]},
            ],
        }
        self.assertTrue(self.gate.assess(conv, frame).accepted)

    async def test_other_authors_evidence_not_attributed(self):
        conv = thread()
        conv["comments"].append({"id": "other", "author": "other",
                                 "text": "I want an expensive different CRM."})
        frame = (await self.resolver.resolve(conv)).to_dict()
        frame["evidence"].append({"message_id": "other", "author": "other",
                                  "excerpt": "I want an expensive different CRM"})
        self.assertFalse(self.gate.assess(conv, frame).accepted)



class TargetedNeedSearchTests(unittest.IsolatedAsyncioTestCase):
    """Search index finds a comment; only Firebase can prove its author."""

    class SearchStub:
        def __init__(self, *, tampered=False, wrong_story=False):
            self.calls = []
            self.tampered = tampered
            self.wrong_story = wrong_story

        async def get(self, url, **kwargs):
            self.calls.append((url, kwargs.get("params", {})))
            tags = kwargs.get("params", {}).get("tags", "")
            if tags == "comment":
                return StubResponse({"hits": [{
                    "objectID": "101", "story_id": 900,
                    "author": "attacker" if self.tampered else "speaker",
                    "comment_text": "I wish there was a simple invoice app.",
                }]})
            if tags == "comment,story_900,author_speaker":
                return StubResponse({"hits": [
                    {"objectID": "101", "story_id": 900, "author": "speaker"},
                    {"objectID": "102", "story_id": 900, "author": "speaker"},
                    {"objectID": "103", "story_id": 900, "author": "another"},
                ]})
            raise AssertionError("Unexpected search request: " + tags)

    class HNStub:
        def __init__(self, *, wrong_story=False):
            self.paths = []
            self.wrong_story = wrong_story

        async def get(self, url, **kwargs):
            self.paths.append(url)
            if url.endswith("item/101.json"):
                return StubResponse({
                    "id": 101, "type": "comment", "by": "speaker",
                    "parent": 900, "time": 30,
                    "text": "I spend hours manually checking invoice imports. Every app fails."
                })
            if url.endswith("item/102.json"):
                return StubResponse({
                    "id": 102, "type": "comment", "by": "speaker",
                    "parent": 900, "time": 40,
                    "text": "I want faster invoice automation so I can finish before evening."
                })
            if url.endswith("item/103.json"):
                return StubResponse({
                    "id": 103, "type": "comment", "by": "another",
                    "parent": 900, "time": 20,
                    "text": "I demand something unrelated, a different product."
                })
            if url.endswith("item/900.json"):
                return StubResponse({
                    "id": 901 if self.wrong_story else 900, "type": "story",
                    "title": "Ask HN: What invoicing problems are unsolved?",
                    "by": "thread_original"
                })
            raise AssertionError("Unexpected official HN route " + url)

    async def test_search_hydrates_original_author_and_followups_not_index_text(self):
        from app.wishcatcher.discovery.need_search import HackerNewsNeedSearch
        search, hn = self.SearchStub(), self.HNStub()
        adapter = HackerNewsNeedSearch(
            search_client=search, hn_client=hn, queries=["I wish there was"],
            max_queries=1,
        )
        records = await adapter.fetch(limit=3)
        self.assertEqual(len(records), 1)
        item = records[0]
        self.assertEqual(item.source, "hackernews")
        self.assertEqual(item.source_id, "hn:900:actor:speaker")
        self.assertEqual(item.conversation["post_author"], "speaker")
        self.assertEqual(item.conversation["post_id"], "hn:101")
        self.assertIn("checking invoice imports", item.conversation["post_text"])
        self.assertEqual(len(item.conversation["comments"]), 1)
        self.assertIn("faster invoice automation", item.conversation["comments"][0]["text"])
        self.assertNotIn("another", str(item.conversation["comments"]))
        self.assertEqual(item.conversation["metadata"]["thread_id"], "hn:900")
        self.assertEqual(item.conversation["metadata"]["coverage"],
                         "SEARCH_MATCHED_ACTOR_MESSAGES_PARTIAL_THREAD")
        self.assertTrue(all("hn.algolia.com/api/" in url
                            for url, _ in search.calls))
        self.assertTrue(all("hacker-news.firebaseio.com/v0/" in url for url in hn.paths))

    async def test_forged_index_author_fails_closed(self):
        from app.wishcatcher.discovery.need_search import HackerNewsNeedSearch
        adapter = HackerNewsNeedSearch(
            search_client=self.SearchStub(tampered=True),
            hn_client=self.HNStub(), queries=["I wish there was"], max_queries=1)
        self.assertEqual(await adapter.fetch(limit=1), [])

    async def test_forged_story_membership_fails_closed(self):
        from app.wishcatcher.discovery.need_search import HackerNewsNeedSearch
        adapter = HackerNewsNeedSearch(
            search_client=self.SearchStub(),
            hn_client=self.HNStub(wrong_story=True), queries=["I wish there was"], max_queries=1)
        self.assertEqual(await adapter.fetch(limit=1), [])

    async def test_targeted_source_end_to_end_to_genesis(self):
        from app.wishcatcher.discovery.need_search import HackerNewsNeedSearch
        with tempfile.TemporaryDirectory() as directory:
            from unittest.mock import patch
            with patch.dict(os.environ, {
                "WISHCATCHER_DISCOVERY_DB": str(Path(directory) / "need.db"),
                "WISHCATCHER_RAG_DB": str(Path(directory) / "knowledge.db"),
            }):
                adapter = HackerNewsNeedSearch(
                    search_client=self.SearchStub(), hn_client=self.HNStub(),
                    queries=["I wish there was"], max_queries=1,
                )
                index = DiscoveryIndex()
                runner = DiscoveryRunner(
                    index=index, sources={"hn_need_search": adapter})
                result = await runner.run(["hn_need_search"])
                self.assertEqual(result["collected"], 1, result)
                self.assertEqual(result["inserted"], 1, result)
                self.assertEqual(result["clusters"][0]["market_demand"], "UNKNOWN")
                self.assertEqual(result["clusters"][0]["unique_threads"], 1)
                self.assertEqual(result["clusters"][0]["known_actors"], 1)
                rerun = await runner.run(["hn_need_search"])
                self.assertEqual(rerun["inserted"], 0)
                self.assertEqual(rerun["rejection_reasons"]["already_indexed"], 1)

class ClusterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = unittest.mock.patch.dict(os.environ, {
            "WISHCATCHER_RAG_DB": str(Path(self.tmp.name) / "local-knowledge.sqlite3"),
            "WISHCATCHER_DISCOVERY_PERSIST_RAG": "1",
        })
        self.env_patch.start()
        self.index = DiscoveryIndex(str(Path(self.tmp.name) / "discovery.db"))

    async def asyncTearDown(self):
        self.env_patch.stop()
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
        self.assertEqual(len(clusters[0]["supporting_sources"]), 2)
        for source in clusters[0]["supporting_sources"]:
            self.assertTrue(source["evidence"])
            self.assertTrue(source["url"].startswith("https://"))
            self.assertTrue(source["evidence"][0]["message_id"])

        from app.wishcatcher.integrations.plugin_runtime import SQLiteGraphRAG
        rag = SQLiteGraphRAG()
        hit_ids = [h["id"] for h in rag.retrieve("accounting invoice", graph_hops=1)]
        self.assertTrue(any(id.startswith("wish:") for id in hit_ids), hit_ids)
        self.assertIn(clusters[0]["cluster_id"], hit_ids)

        again = await engine.run(["hn_ask"], max_per_source=5)
        self.assertEqual(again["inserted"], 0)
        self.assertEqual(len(self.index.clusters()), 1)

    async def test_minimal_audit_evidence_redacts_contacts(self):
        from app.wishcatcher.discovery.pipeline import minimal_frame
        frame = minimal_frame({
            "domain": "accounting", "problem": "Time-consuming bookkeeping",
            "intent": "Reduce reconciliation work",
            "evidence": [{
                "message_id": "m12",
                "excerpt": "Contact alice@example.org or token=abcdef123456 "
                           "to discuss the manual invoice issue."
            }],
            "quality_status": "CANDIDATE_NEEDS_REVIEW",
        })
        self.assertEqual(frame["evidence"][0]["message_id"], "m12")
        self.assertNotIn("alice@example.org", frame["evidence"][0]["excerpt"])
        self.assertNotIn("abcdef123456", frame["evidence"][0]["excerpt"])
        self.assertEqual(frame["quality_status"], "CANDIDATE_NEEDS_REVIEW")

    async def test_second_poll_skips_existing_context_before_llm_inference(self):
        class SpyResolver:
            def __init__(self):
                self.calls = 0
                self.base = ConversationContextResolver()
            async def resolve(self, context):
                self.calls += 1
                return await self.base.resolve(context)

        source = FakeSource([record("alice", "once")])
        spy = SpyResolver()
        runner = DiscoveryRunner(index=self.index, resolver=spy,
                                 sources={"hn_ask": source})
        first = await runner.run(["hn_ask"])
        second = await runner.run(["hn_ask"])
        self.assertEqual(first["inserted"], 1)
        self.assertEqual(second["inserted"], 0)
        self.assertEqual(second["skipped"], 1)
        self.assertEqual(spy.calls, 1)

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

    async def test_boilerplate_does_not_merge_distinct_workflows(self):
        # Real similarity bug: legacy score 0.75 >= old merge threshold 0.74
        bank = {
            "domain": "accounting",
            "problem": "I spend hours manually reconciling bank records; the software is slow.",
            "intent": "Need inferred from repeated problem statements: "
                      "spend hours reconciling bank records",
        }
        pdf = {
            "domain": "accounting",
            "problem": "I spend hours manually exporting invoices to PDF; the software is slow.",
            "intent": "Need inferred from repeated problem statements: "
                      "spend hours exporting invoices to PDF",
        }
        self.assertLess(similarity(bank, pdf), 0.74)

    async def test_equivalent_invoice_need_in_ro_en_can_match(self):
        ro = {
            "domain": "accounting",
            "problem": "Pierd ore la facturi manual.",
            "intent": "Vreau să termin facturile rapid.",
            "desired_outcome": "Vreau să termin facturile rapid.",
        }
        en = {
            "domain": "accounting",
            "problem": "I waste hours on manual invoices.",
            "intent": "I want to finish invoices fast.",
            "desired_outcome": "I want to finish invoices fast.",
        }
        self.assertGreaterEqual(similarity(ro, en), 0.74)

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
    async def test_public_comment_does_not_promote_quoted_third_party_goals(self):
        from app.wishcatcher.discovery.sources import clean_html
        from app.wishcatcher.contextual.quality import ContextQualityGate
        raw = (
            "<p>&gt; I want to first say thanks for engaging directly"
            "<p>Of course :)"
            "<p>&gt; As I said earlier, I want to thank you again"
            "<p>Could you explain why this Azure callback is forgeable?"
        )
        text = clean_html(raw)
        self.assertNotIn("I want to first say thanks", text)
        self.assertNotIn("I want to thank", text)
        self.assertIn("Could you explain", text)
        context = {
            "post_id": "hn:azure:comment", "post_author": "actor",
            "post_text": text, "comments": [],
        }
        frame = (await ConversationContextResolver().resolve(context)).to_dict()
        self.assertFalse(ContextQualityGate().assess(context, frame).accepted)

    async def test_real_first_person_pain_not_removed_by_quote_filter(self):
        from app.wishcatcher.discovery.sources import clean_html
        text = clean_html(
            "<p>&gt; Why not just keep using Slack?"
            "<p>I absolutely despise what Slack has become and would "
            "love to replace it, but I cannot see how to connect my old messages."
        )
        self.assertIn("despise", text)
        self.assertIn("connect my old messages", text)
        self.assertNotIn("Why not just keep using Slack", text)

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
