"""Conservative evidence and negation checks, independent of LLM confidence.

These guards do not claim semantic entailment. Their role is to catch obvious
false positives, attribution leaks and superseded intentions, while making
uncertainty visible to the operator and evaluation suite.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from app.wishcatcher.contextual.context_resolver import ContextStateBuilder


@dataclass
class QualityResult:
    accepted: bool
    status: str
    flags: List[str] = field(default_factory=list)
    field_evidence: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextQualityGate:
    """Strict defaults for autonomous *publication*, not interactive inspection."""

    FICTION = re.compile(
        r"(?i)\b(?:just kidding|just a joke|hypothetical(?:ly)?|"
        r"fictional (?:story|example)|not a real problem|"
        r"glumesc|doar o glumă|doar o gluma|exemplu fictiv|"
        r"imagine(?:ază|aza).?(?:ți|ti)|/s)\b"
    )
    RESOLVED = re.compile(
        r"(?i)\b(?:problem (?:is )?(?:solved|resolved|fixed)|"
        r"never mind.{0,24}solved|found (?:the|a) solution|"
        r"it works now|no longer an issue|"
        r"am rezolvat|problema (?:este |e )?rezolvată|"
        r"problema (?:este |e )?rezolvata|"
        r"nu mai am (?:problema|nevoie)|nu mai e o problemă)\b"
    )
    THIRD_PARTY_REPORT = re.compile(
        r"(?i)^\s*(?:my friend|a friend|someone i know|"
        r"my colleague|prietenul meu|un prieten|colegul meu)"
        r".{0,80}\b(?:wants?|needs?|vre[a-zăâîșț]*|are nevoie)\b"
    )
    NEGATED_REQUEST = re.compile(
        r"(?i)\b(?:i (?:do not|don't|never) want|"
        r"i (?:do not|don't) need|nu (?:mai )?vreau|"
        r"nu (?:mai )?am nevoie|"
        r"i am not looking for|not looking for)\b"
    )
    INFORMATIONAL_ASK = re.compile(
        r"(?i)\b(?:i(?:'m| am) wondering|i (?:just )?(?:want|need) to "
        r"(?:know|understand|learn|find out)|curious (?:about|why)|"
        r"can someone explain|could someone explain|"
        r"what(?:'s| is) .{0,75} business model|"
        r"what(?:'s| is) the reason|how does .{0,60} work|"
        r"de ce (?:este|face|funcționează)|vreau (?:să|sa) (?:știu|stiu|înțeleg|inteleg))\b"
    )
    PERSONAL_FRICTION = re.compile(
        r"(?i)\b(?:i|we|my|our)\b[^\n.!?]{0,120}\b"
        r"(?:tried|struggl\w*|stuck|wast\w*|manual|problem|"
        r"fail\w*|slow|complicated|too expensive|cannot|can't|"
        r"doesn't work|does not work|doesn't connect)\b|"
        r"\b(?:am încercat|am incercat|mă chinui|ma chinui|"
        r"pier[dt] ore|pierd timp|nu funcționează|nu functioneaza|"
        r"nu se conectează|nu se conecteaza|m-am săturat|m-am saturat)\b"
    )
    OPERATIONAL_GOAL = re.compile(
        r"(?i)\b(?:i|we) (?:want|need|wish)(?: to)? "
        r"(?:finish|automate|reduce|fix|replace|build|connect|save|"
        r"integrate|simplify|stop|manage|track|organize|streamline)\b|"
        r"\b(?:vreau|mi-ar trebui|aș vrea|as vrea)\b.{0,90}"
        r"\b(?:aplicație|aplicatie|automat|termin|reduce|simpl|"
        r"conect|integra|soluție|solutie|rapid|fără|fara)\b"
    )
    POSITIVE_GOAL = re.compile(
        r"(?i)\b(?:i want|i need|i wish|i would use|"
        r"i'd try|aș vrea|as vrea|vreau|am nevoie|mi-ar trebui)\b"
    )

    def assess(self, conversation: Dict[str, Any], frame: Dict[str, Any]) -> QualityResult:
        messages = ContextStateBuilder.flatten(conversation)
        own = ContextStateBuilder.primary_messages(messages)
        flags: List[str] = []
        if not own:
            return QualityResult(False, "NO_VERDICT", ["no_source_messages"])
        original = own[0].author
        evidence = frame.get("evidence") or []
        original_ids = {m.message_id for m in own}
        evidence_ids = [
            str(e.get("message_id")) for e in evidence if isinstance(e, dict)
        ]
        if not frame.get("actionable"):
            return QualityResult(False, "NO_VERDICT", ["model_or_rules_abstained"])
        if not evidence_ids or any(ident not in original_ids for ident in evidence_ids):
            return QualityResult(False, "REJECT", ["evidence_missing_or_wrong_actor"])
        if (not frame.get("problem") and not frame.get("desired_outcome")):
            return QualityResult(False, "NO_VERDICT", ["no_problem_or_goal"])
        # Unknown actors cannot support cross-comment independent corroboration.
        if original.startswith("__unknown"):
            flags.append("unknown_actor_attribution")

        latest = own[-1].text.strip()
        all_own = "\n".join(m.text for m in own)
        if self.FICTION.search(all_own):
            return QualityResult(False, "REJECT", flags + ["explicit_fiction_or_sarcasm"])
        if self.THIRD_PARTY_REPORT.search(own[0].text):
            return QualityResult(False, "REJECT", flags + ["third_party_report_not_first_person"])
        if self.RESOLVED.search(latest):
            return QualityResult(False, "REJECT", flags + ["superseded_problem_resolved"])
        # Live-source regression (2026-11-04): a question about Google
        # Flights' BUSINESS MODEL was treated as a demand for software.
        # Asking "how does X work?" is informational curiosity unless
        # the same actor also describes operational friction or a concrete
        # outcome. Apply this guard only to the rule fallback: an LLM may
        # reconstruct a genuine implicit need from richer evidence.
        if (frame.get("interpretation_method") == "rules"
                and self.INFORMATIONAL_ASK.search(all_own)
                and not self.PERSONAL_FRICTION.search(all_own)
                and not self.OPERATIONAL_GOAL.search(all_own)):
            return QualityResult(
                False, "NO_VERDICT", flags + ["informational_question_not_unmet_need"]
            )
        if (self.NEGATED_REQUEST.search(latest)
                and not self.POSITIVE_GOAL.search(
                    self.NEGATED_REQUEST.sub("", latest))
                and not frame.get("problem")):
            return QualityResult(False, "REJECT", flags + ["negated_request_only"])
        if len(evidence_ids) == 1:
            flags.append("single_message_evidence")
        if frame.get("epistemic_status") == "inferred":
            flags.append("inferred_not_explicit")
        if frame.get("interpretation_method") == "rules":
            flags.append("rules_only_no_semantic_entailment")
        if frame.get("interpretation_method") == "llm_contextual" and not frame.get("field_evidence"):
            flags.append("llm_global_ids_only_no_field_entailment")
        if len(own) > 1 and any(self.NEGATED_REQUEST.search(m.text) for m in own[1:]):
            flags.append("possible_superseded_constraint_review")
        # These references identify which *messages* inform a field. They do
        # not prove semantic entailment of a generated field's wording.
        frame_fields = frame.get("field_evidence") or {}
        mapped = {}
        for field_name in ("problem", "desired_outcome", "intent"):
            claims = frame_fields.get(field_name) if isinstance(frame_fields, dict) else None
            mapped[field_name] = (
                [str(i) for i in claims if str(i) in original_ids][:12]
                if isinstance(claims, list) and claims else evidence_ids[:12]
            )
        return QualityResult(
            True, "CANDIDATE_NEEDS_REVIEW", flags,
            field_evidence=mapped,
        )
