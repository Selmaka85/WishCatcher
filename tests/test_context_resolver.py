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


if __name__ == "__main__":
    unittest.main()
