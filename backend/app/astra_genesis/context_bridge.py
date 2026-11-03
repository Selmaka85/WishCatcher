"""Evidence-grounded bridge from WishCatcher's ContextFrame to ASTRA Genesis.

A solution brief is a hypothesis to validate, not a forecast or a market
research report. Never call BusinessPlanGenerator's default revenue projections
without verified market data. Preserve the original multi-domain Genesis
intent -> constraints -> components -> dependency graph -> validation contract.
"""
from __future__ import annotations

from typing import Any, Dict, List


class GenesisContextBridge:
    """Create a structural, domain-neutral opportunity draft."""

    @staticmethod
    def compose(frame: Dict[str, Any]) -> Dict[str, Any]:
        if not frame.get("actionable") or not frame.get("intent"):
            raise ValueError("No grounded actionable need. Review context and evidence first.")
        evidence = frame.get("evidence") or []
        if not evidence:
            raise ValueError("Cannot generate solutions without source-message evidence.")
        problem = str(frame.get("problem") or "").strip()
        desired = str(frame.get("desired_outcome") or "").strip()
        intent = str(frame.get("intent") or "").strip()
        domain = str(frame.get("domain") or "other")
        constraints = [
            str(v)[:300] for v in (frame.get("constraints") or [])[:10]
            if isinstance(v, str) and v.strip()
        ]
        attempts = [
            str(v)[:300] for v in (frame.get("attempted_solutions") or [])[:10]
            if isinstance(v, str) and v.strip()
        ]
        source_ids = list(dict.fromkeys(
            str(item.get("message_id")) for item in evidence[:24]
            if isinstance(item, dict) and item.get("message_id")
        ))
        if not source_ids:
            raise ValueError("Evidence must contain traceable source-message IDs.")

        # Alternatives are options to test, not automatically validated
        # implementations. Do not presume a SaaS is always the right answer.
        alternatives: List[Dict[str, Any]] = [
            {
                "id": "process",
                "approach": "Simplify or remove the problematic workflow",
                "rationale": "Reduce friction before building new software",
                "validation": "Observe the workflow and measure the lost time",
                "status": "hypothesis",
            },
            {
                "id": "integrate",
                "approach": "Reconfigure or connect existing tools",
                "rationale": "Prefer a low-maintenance fix if existing tools can meet constraints",
                "validation": "Verify vendor features, pricing, and interoperability",
                "status": "hypothesis",
            },
            {
                "id": "build",
                "approach": "Prototype a minimal tool meeting the documented outcome",
                "rationale": "Consider a new build only if simpler options fail",
                "validation": "Test the smallest prototype with independent users",
                "status": "hypothesis",
            },
        ]
        # Generalizable dependency graph, not imaginary domain components.
        components = [
            {"id": "input", "function": "Capture relevant input data", "depends_on": []},
            {"id": "processor", "function": "Apply the required workflow to reach the outcome", "depends_on": ["input"]},
            {"id": "output", "function": "Deliver and verify the desired outcome", "depends_on": ["processor"]},
            {"id": "verification", "function": "Check constraints against observed usage", "depends_on": ["input", "output"]},
        ]
        return {
            "kind": "genesis_opportunity_brief_v1",
            "status": "UNVALIDATED_HYPOTHESIS",
            "source_id": str(frame.get("source_id") or ""),
            "domain": domain,
            "problem": problem,
            "desired_outcome": desired,
            "intent": intent,
            "constraints": constraints,
            "attempted_solutions": attempts,
            "supporting_message_ids": source_ids,
            "epistemic_status": frame.get("epistemic_status") or "unknown",
            "alternatives": alternatives,
            "solution_architecture": {"components": components},
            "validation_questions": [
                "Is the problem recurring and costly enough to justify a solution?",
                "Which constraints are essential versus preferences?",
                "Can existing tools satisfy the outcome at lower total cost?",
                "Do independent potential users confirm the same unmet need?",
                "What measurable criterion demonstrates that the solution works?",
                "Would anyone pay, and how much? Not established by this context.",
            ],
            "market_demand": "UNKNOWN",
            "willingness_to_pay": "UNKNOWN",
            "financial_forecast": None,
            "next_gate": "Validate market and feasibility before claiming a viable business or shipping generated code.",
        }
