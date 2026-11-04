"""Provider-free regression contracts for full-thread WishCatcher context resolution.

Run: python -m unittest discover -s tests -v
"""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.wishcatcher.contextual.context_resolver import (
    ContextStateBuilder,
    ConversationContextResolver,
    OpenAICompatibleContextInterpreter,
)


class DisabledInterpreter:
    async def resolve(self, messages):
        return None


class StubInterpreter:
    def __init__(self, response):
        self.response = response

    async def resolve(self, messages):
        return self.response


def accounting_thread():
    return {
        "post_id": "t1", "post_author": "owner", "post_timestamp": 1.0,
        "post_title": "Programe de contabilitate",
        "post_text": "Am încercat trei programe de contabilitate. Toate sunt o porcărie.",
        "comments": [
            {"id": "c1", "author": "owner", "timestamp": 2.0,
             "text": "Primul era scump, al doilea complicat, iar al treilea nu se conecta cu banca."},
            {"id": "c2", "author": "owner", "timestamp": 3.0,
             "text": "Eu vreau doar să termin facturile seara, fără să stau două ore."},
            {"id": "c3", "author": "owner", "timestamp": 4.0,
             "text": "Dacă ar face cineva unul simplu, l-aș încerca imediat."},
        ]
    }


class ContextResolverTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.resolver = ConversationContextResolver(interpreter=DisabledInterpreter())

    async def test_composes_four_turns_into_one_problem(self):
        frame = await self.resolver.resolve(accounting_thread())
        self.assertTrue(frame.actionable)
        self.assertEqual(frame.domain, "accounting")
        self.assertEqual(frame.message_count, 4)
        self.assertIn("facturile", frame.desired_outcome)
        self.assertIn("contabilitate", frame.problem)
        self.assertIn("scump", " ".join(frame.constraints))
        self.assertEqual(frame.primary_actor, "owner")
        self.assertTrue({"t1", "c1", "c2"}.issubset(
            {item["message_id"] for item in frame.evidence}
        ))
        self.assertEqual(frame.epistemic_status, "explicit")

    async def test_other_persons_goal_not_assigned_to_original_poster(self):
        data = {
            "post_id": "x", "post_author": "alex",
            "post_text": "Am încercat un program, dar e o porcărie.",
            "comments": [
                {"id": "p", "author": "pat", "text": "Vreau un CRM scump și complex!"},
                {"id": "p2", "author": "pat", "text": "Am nevoie de integrare bancară."},
            ],
        }
        frame = await self.resolver.resolve(data)
        self.assertFalse(frame.actionable)
        self.assertFalse(any("pat" == e["author"] for e in frame.evidence))
        self.assertTrue(frame.other_actor_signals)

    async def test_unknown_original_poster_cannot_own_anonymous_replies(self):
        data = {
            "post_id": "x", "post_text": "E scump programul.",
            "comments": [{"text": "Vreau o aplicație pentru facturi."}],
        }
        frame = await self.resolver.resolve(data)
        self.assertEqual(frame.primary_actor, "__unknown_root_author__")
        self.assertEqual(len(frame.evidence), 1)

    async def test_hypothetical_post_not_a_real_market_signal(self):
        data = {
            "post_id": "hyp", "post_author": "owner",
            "post_text": "Imaginează-ți o lume fictivă: vreau o aplicație care face magie.",
        }
        frame = await self.resolver.resolve(data)
        self.assertFalse(frame.actionable)
        self.assertEqual(frame.confidence, 0)

    async def test_latest_clarification_supersedes_old_goal(self):
        data = accounting_thread()
        data["comments"].append({
            "id": "c4", "author": "owner", "timestamp": 5.0,
            "text": "De fapt, vreau să fie offline, nu mă interesează integrarea cu banca.",
        })
        frame = await self.resolver.resolve(data)
        self.assertIn("offline", frame.desired_outcome)
        self.assertIn("c4", {e["message_id"] for e in frame.evidence})

    async def test_nested_replies_are_not_dropped(self):
        data = accounting_thread()
        data["comments"] = [
            {"id": "c0", "author": "someone", "text": "I think it is easy.",
             "replies": [{"id": "nested", "author": "owner", "text":
                          "Vreau ceva simplu pentru facturi, că pierd două ore zilnic."}]}
        ]
        frame = await self.resolver.resolve(data)
        self.assertEqual(frame.message_count, 3)
        self.assertIn("nested", {e["message_id"] for e in frame.evidence})

    async def test_llm_evidence_references_must_exist(self):
        data = accounting_thread()
        interpreter = StubInterpreter({
            "actionable": True, "confidence": 0.99,
            "evidence_ids": ["completely_invented"],
            "intent": "Buy a flying car",
            "problem": "Teleportation",
            "epistemic_status": "explicit",
        })
        frame = await ConversationContextResolver(interpreter).resolve(data)
        self.assertEqual(frame.interpretation_method, "rules")
        self.assertNotIn("flying car", frame.intent)

    async def test_llm_grounded_multi_turn_interpretation(self):
        data = accounting_thread()
        interpreter = StubInterpreter({
            "actionable": True, "confidence": 0.82,
            "evidence_ids": ["t1", "c1", "c2", "c3"],
            "intent": "Reduce invoicing time using simple bank-connected accounting tools",
            "problem": "Three accounting tools failed the owner's constraints",
            "desired_outcome": "Finish invoices quickly",
            "constraints": ["low cost", "easy to use", "bank integration"],
            "attempted_solutions": ["three existing tools"],
            "rejected_alternatives": ["first tool", "second tool", "third tool"],
            "unmet_needs": ["less administrative work"],
            "epistemic_status": "inferred",
            "domain": "accounting",
        })
        frame = await ConversationContextResolver(interpreter).resolve(data)
        self.assertTrue(frame.actionable)
        self.assertEqual(frame.interpretation_method, "llm_contextual")
        self.assertIn("bank-connected", frame.intent)
        self.assertEqual(frame.confidence, 0.82)
        self.assertEqual(len(frame.evidence), 4)
        self.assertEqual(frame.epistemic_status, "inferred")

    async def test_llm_abstention_overrides_permissive_rule_guess(self):
        data = accounting_thread()
        model = StubInterpreter({
            "actionable": False,
            "confidence": 0.8,
            "evidence_ids": ["t1", "c1", "c2"],
            "intent": "No reliable commercial intent",
            "problem": "The discussion is ambiguous",
            "epistemic_status": "inferred",
        })
        frame = await ConversationContextResolver(model).resolve(data)
        self.assertFalse(frame.actionable)
        self.assertEqual(frame.confidence, 0.0)
        self.assertTrue(frame.needs_review)
        self.assertEqual(frame.interpretation_method, "llm_contextual")

    async def test_clarification_respects_timestamps_over_thread_display_order(self):
        data = accounting_thread()
        data["comments"].extend([
            {"id": "latest", "author": "owner", "timestamp": 100.0,
             "text": "De fapt, vreau un program offline; nu vreau integrare cu banca."},
            {"id": "earlier", "author": "owner", "timestamp": 6.0,
             "text": "Vreau integrare bancara automatizata."},
        ])
        frame = await self.resolver.resolve(data)
        self.assertIn("offline", frame.desired_outcome)

    async def test_llm_real_citation_cannot_ground_unrelated_flying_car_claim(self):
        data = accounting_thread()
        model = StubInterpreter({
            "actionable": True, "confidence": 0.98,
            "evidence_ids": ["t1", "c1", "c2"],
            "intent": "Buy a flying car",
            "problem": "Accounting programs are expensive",
            "desired_outcome": "Finish invoices quickly",
            "epistemic_status": "inferred",
        })
        frame = await ConversationContextResolver(model).resolve(data)
        self.assertEqual(frame.interpretation_method, "rules")
        self.assertNotIn("flying car", frame.intent)

    async def test_llm_field_evidence_rejects_other_author(self):
        data = accounting_thread()
        data["comments"].append({
            "id": "outsider", "author": "other",
            "text": "I also need invoicing tools",
        })
        model = StubInterpreter({
            "actionable": True, "confidence": 0.84,
            "evidence_ids": ["t1", "c1", "c2", "outsider"],
            "field_evidence": {
                "problem": ["t1"],
                "desired_outcome": ["outsider"],
                "intent": ["c2"],
            },
            "problem": "Accounting apps fail",
            "desired_outcome": "Finish invoices quickly",
            "intent": "Faster invoicing for accounting",
            "epistemic_status": "inferred",
        })
        frame = await ConversationContextResolver(model).resolve(data)
        self.assertEqual(frame.interpretation_method, "rules")
        self.assertFalse(frame.field_evidence)

    async def test_llm_accepts_valid_per_field_source_ids(self):
        data = accounting_thread()
        model = StubInterpreter({
            "actionable": True, "confidence": 0.84,
            "evidence_ids": ["t1", "c1", "c2"],
            "field_evidence": {
                "problem": ["t1", "c1"],
                "desired_outcome": ["c2"],
                "intent": ["c2"],
            },
            "problem": "Accounting apps are expensive",
            "desired_outcome": "Finish invoices quickly",
            "intent": "Faster invoice processing with bank integration",
            "epistemic_status": "inferred",
        })
        frame = await ConversationContextResolver(model).resolve(data)
        self.assertEqual(frame.interpretation_method, "llm_contextual")
        self.assertEqual(frame.field_evidence["desired_outcome"], ["c2"])
        self.assertEqual(frame.grounding_status, "message_ids_checked_not_entailment")

    async def test_llm_cannot_assert_other_speakers_intent(self):
        data = {
            "post_id": "t1", "post_author": "alex",
            "post_text": "I saw a product yesterday.",
            "comments": [{"id": "other", "author": "lee",
                          "text": "I want my business accounting automated."}],
        }
        interpreter = StubInterpreter({
            "actionable": True, "confidence": 0.95,
            "evidence_ids": ["other"],
            "intent": "Alex wants accounting software",
            "problem": "Software problem", "epistemic_status": "explicit",
        })
        frame = await ConversationContextResolver(interpreter).resolve(data)
        self.assertFalse(frame.actionable)
        self.assertEqual(frame.interpretation_method, "rules")

    def test_chunking_processes_long_conversations_without_dropping_messages(self):
        from app.wishcatcher.contextual.context_resolver import ContextMessage
        messages = [
            ContextMessage(str(i), "owner", "Need something useful " + "z" * 400)
            for i in range(90)
        ]
        chunks = OpenAICompatibleContextInterpreter._chunks(messages, 900)
        flattened = [part for chunk in chunks for part in chunk]
        self.assertEqual(len(flattened), len(messages))
        self.assertEqual({item["source_id"] for item in flattened},
                         {str(i) for i in range(90)})




class ParentChainCausalContractTests(unittest.TestCase):
    def test_flat_comments_keep_explicit_parent_relation_from_source(self):
        from app.wishcatcher.contextual.context_resolver import ContextStateBuilder
        conversation = {
            "post_id": "hn:root", "post_author": "first",
            "post_text": "Original question",
            "comments": [
                {"id": "hn:reply-one", "author": "second",
                 "text": "Why would you change that?", "parent_id": "hn:root"},
                {"id": "hn:reply-two", "author": "first",
                 "text": "Because I spend hours doing it manually.",
                 "parent_id": "hn:reply-one"},
            ],
        }
        messages = ContextStateBuilder.flatten(conversation)
        self.assertEqual(messages[1].parent_id, "hn:root")
        self.assertEqual(messages[2].parent_id, "hn:reply-one")

    def test_nested_comments_without_parent_id_still_use_nesting(self):
        from app.wishcatcher.contextual.context_resolver import ContextStateBuilder
        conversation = {
            "post_id": "root", "post_author": "owner", "post_text": "My problem",
            "comments": [{"id": "a", "author": "other", "text": "What problem?",
                          "replies": [{"id": "b", "author": "owner", "text": "The export."}]}],
        }
        messages = ContextStateBuilder.flatten(conversation)
        self.assertEqual(messages[2].parent_id, "a")

class ImplicitSingleActorNeedTests(unittest.IsolatedAsyncioTestCase):
    """A credible single comment must not disappear solely for having no reply."""

    async def test_grounded_single_comment_operational_pain_survives(self):
        from app.wishcatcher.contextual.quality import ContextQualityGate
        from app.wishcatcher.contextual.context_resolver import ConversationContextResolver
        sample = {
            "post_id": "hn:comment-1",
            "post_author": "person",
            "post_text": (
                "I waste two hours manually exporting invoice rows from our "
                "software every morning, and none of the apps connect to the bank."
            ),
            "comments": [],
        }
        frame = (await ConversationContextResolver().resolve(sample)).to_dict()
        self.assertTrue(frame["actionable"], frame)
        self.assertEqual(frame["epistemic_status"], "inferred")
        self.assertTrue(frame["problem"])
        self.assertTrue(frame["intent"])
        self.assertTrue(ContextQualityGate().assess(sample, frame).accepted)

    async def test_generic_product_complaint_is_not_sufficient(self):
        from app.wishcatcher.contextual.context_resolver import ConversationContextResolver
        sample = {
            "post_id": "hn:comment-2",
            "post_author": "person",
            "post_text": "I tried this accounting app and it is expensive.",
            "comments": [],
        }
        frame = (await ConversationContextResolver().resolve(sample)).to_dict()
        self.assertFalse(frame["actionable"], frame)

class ProviderTransportContracts(unittest.IsolatedAsyncioTestCase):
    async def test_real_openai_compatible_request_contract_uses_local_mock(self):
        import json
        import os
        from unittest.mock import patch
        from app.wishcatcher.contextual.context_resolver import (
            ContextMessage, OpenAICompatibleContextInterpreter,
        )

        class MockResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": json.dumps({
                    "problem": "Accounting applications fail user constraints",
                    "desired_outcome": "Finish invoicing quickly",
                    "intent": "Reduce administrative time",
                    "epistemic_status": "inferred",
                    "confidence": 0.85,
                    "actionable": True,
                    "evidence_ids": ["p1", "c1"],
                })}}]}

        class MockHTTPClient:
            def __init__(self):
                self.calls = []

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def post(self, url, **kwargs):
                self.calls.append((url, kwargs))
                return MockResponse()

        fake = MockHTTPClient()
        with patch.dict(os.environ, {
            "WISHCATCHER_CONTEXT_LLM_ENABLED": "1",
            "WISHCATCHER_CONTEXT_LLM_URL": "http://127.0.0.1:11434/v1/chat/completions",
            "WISHCATCHER_CONTEXT_MODEL": "test-model",
            "WISHCATCHER_CONTEXT_LLM_TIMEOUT_SEC": "180",
            "WISHCATCHER_CONTEXT_ALLOW_REMOTE": "0",
        }):
            interpreter = OpenAICompatibleContextInterpreter()
            with patch("httpx.AsyncClient", return_value=fake) as transport:
                result = await interpreter.resolve([
                    ContextMessage("p1", "owner", "I tried 3 accounting programs"),
                    ContextMessage("c1", "owner", "I want to finish invoices faster"),
                ])
            self.assertTrue(result["actionable"])
            self.assertEqual(result["intent"], "Reduce administrative time")
            self.assertEqual(len(fake.calls), 1)
            request = fake.calls[0][1]["json"]
            self.assertEqual(request["model"], "test-model")
            self.assertEqual(request["temperature"], 0)
            self.assertEqual(request["response_format"], {"type": "json_object"})
            self.assertEqual(request["messages"][0]["role"], "system")
            self.assertEqual(transport.call_args.kwargs["timeout"], 180.0)

    async def test_remote_provider_cannot_run_without_explicit_opt_in(self):
        import os
        from unittest.mock import patch
        from app.wishcatcher.contextual.context_resolver import (
            ContextMessage, OpenAICompatibleContextInterpreter,
        )
        with patch.dict(os.environ, {
            "WISHCATCHER_CONTEXT_LLM_ENABLED": "1",
            "WISHCATCHER_CONTEXT_LLM_URL": "https://api.external.example/v1/chat/completions",
            "WISHCATCHER_CONTEXT_ALLOW_REMOTE": "0",
        }):
            result = await OpenAICompatibleContextInterpreter().resolve([
                ContextMessage("a", "owner", "I want automatic bookkeeping")
            ])
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
