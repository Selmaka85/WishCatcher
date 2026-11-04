"""Evidence-grounded bridge from WishCatcher's ContextFrame to ASTRA Genesis.

A solution brief is a hypothesis to validate, not a forecast or a market
research report. Never call BusinessPlanGenerator's default revenue projections
without verified market data. Preserve the original multi-domain Genesis
intent -> constraints -> components -> dependency graph -> validation contract.
"""
from __future__ import annotations

from itertools import combinations
from math import isfinite
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


    @staticmethod
    def rank_declared_catalog(catalog: List[Dict[str, Any]],
                              required_capabilities: List[str],
                              *, top_n: int = 3) -> Dict[str, Any]:
        """P4 isolated Genesis Rule Composer proof, using declared components.

        No LLM, template-imagined modules, guessed costs or new schema.
        The caller supplies its own domain component catalog and comparable,
        nonnegative cost/effort/maintenance *proxy units*. This does not certify
        the components' existence, make them safe or generate runnable code.
        Default GenesisContextBridge.compose remains unchanged.
        """
        if not isinstance(catalog, list) or not 1 <= len(catalog) <= 10:
            raise ValueError("Component catalog must contain 1..10 entries")
        if not isinstance(required_capabilities, list) or not 1 <= len(required_capabilities) <= 10:
            raise ValueError("Required capabilities must contain 1..10 entries")
        if not isinstance(top_n, int) or isinstance(top_n, bool) or not 1 <= top_n <= 3:
            raise ValueError("top_n must be 1..3")
        if any(not isinstance(v, str) or not v.strip()
               for v in required_capabilities):
            raise ValueError("Required capabilities must be nonempty strings")

        by_id: Dict[str, Dict[str, Any]] = {}
        for component in catalog:
            if not isinstance(component, dict):
                raise ValueError("Each catalog entry must be an object")
            ident = component.get("id")
            provided, depends = component.get("provides"), component.get("requires")
            if (not isinstance(ident, str) or not ident.strip()
                    or ident in by_id or len(ident) > 80):
                raise ValueError("Component IDs must be unique nonempty strings")
            if (not isinstance(provided, list) or not provided
                    or not isinstance(depends, list)
                    or any(not isinstance(s, str) or not s.strip()
                           for s in provided + depends)):
                raise ValueError("Component capabilities/dependencies must be string arrays")
            for metric in ("cost_units", "effort_units", "maintenance_units"):
                raw = component.get(metric)
                if (isinstance(raw, bool) or not isinstance(raw, (int, float))
                        or not isfinite(raw) or raw < 0):
                    raise ValueError("Comparable nonnegative finite proxy units are required")
            by_id[ident] = component

        if any(dep not in by_id or dep == ident
               for ident, item in by_id.items() for dep in item["requires"]):
            raise ValueError("Component dependency refers to a missing/self component")

        required = set(required_capabilities)
        candidates: List[Dict[str, Any]] = []
        ids = sorted(by_id)
        for count in range(1, len(ids) + 1):
            for selected_ids in combinations(ids, count):
                selected = set(selected_ids)
                if not all(set(by_id[x]["requires"]) <= selected for x in selected):
                    continue
                # A dependency cycle cannot define a buildable structure.
                unvisited, ordering = set(selected), []
                while unvisited:
                    ready = sorted(
                        x for x in unvisited if set(by_id[x]["requires"]) <= set(ordering)
                    )
                    if not ready:
                        break
                    ordering.extend(ready)
                    unvisited.difference_update(ready)
                if unvisited:
                    continue
                delivered = set().union(*(set(by_id[x]["provides"]) for x in selected))
                if not required <= delivered:
                    continue
                totals = {
                    metric: round(sum(float(by_id[x][metric]) for x in selected), 6)
                    for metric in ("cost_units", "effort_units", "maintenance_units")
                }
                candidates.append({
                    "component_ids": list(selected_ids),
                    "dependency_order": ordering,
                    "provided_capabilities": sorted(delivered),
                    "proxy_totals": totals,
                    "status": "UNVERIFIED_OPERATOR_DECLARED_STRUCTURE",
                })

        candidates.sort(key=lambda x: (
            x["proxy_totals"]["cost_units"],
            x["proxy_totals"]["effort_units"],
            x["proxy_totals"]["maintenance_units"],
            len(x["component_ids"]), x["component_ids"],
        ))
        return {
            "kind": "genesis_declared_catalog_composition_v0",
            "status": "STRUCTURAL_OPTIONS_ONLY" if candidates else "NO_FEASIBLE_STRUCTURE",
            "input_authority": "OPERATOR_DECLARED_UNVERIFIED",
            "required_capabilities": sorted(required),
            "ranking_rule": "lexicographic_proxy_cost_effort_maintenance_components",
            "candidate_count": len(candidates),
            "top_structures": candidates[:top_n],
            "limitations": [
                "Proxy units are operator-declared, not currency or factual costs",
                "No real-world feasibility or requirement entailment verified",
                "No executable code generated or dispatched",
            ],
        }
