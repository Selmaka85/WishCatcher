# WishCatcher: Contextual Intent Resolution (CIR) → ASTRA Genesis

Status: experimental, provider-free baseline + opt-in semantic model. Implemented on
'feature/contextual-intent-genesis-20261103'. Do not claim OpenAI's proprietary ad
context-identification system is reproduced or that inference accuracy is validated.

## Product doctrine

WishCatcher is a **latent human-needs radar**, not an advertising system.
It reconstructs a person's underlying problem and desired outcome from an entire
discussion — including follow-ups, workarounds, alternatives, failures, constraints,
counterexamples and later corrections. It then passes a *traceable need* to the
existing market/opportunity/gap detectors and to ASTRA Genesis. Genesis's original
vision is a rules-driven, domain-agnostic structural solution composer, not only
a chatbot or a business-plan text generator; preserve that boundary.

Primary goal: DISCOVER problem → RECONSTRUCT context → DISTINGUISH observed
evidence from inferred need → VALIDATE → RANK opportunity → COMPOSE
solution in Genesis. No implicit conversion of negative sentiment into paid demand.

## The causal bug repaired

Previously 'backend/app/api/routes/wishes.py' could reject the original post
through 'RobustIntentDetector' and 'PreciseContextExtractor' **before** running
Proactive/Implicit/Conversational/Workaround/Comparison detectors. Those
detectors thus could not rescue genuine problems whose details appeared only
in replies. 'ConversationalAnalyzer' mostly extracts regex matches per comment
and counts identical strings, not a participant-specific evolving world state.

Now:
1. 'ConversationContextResolver.resolve(context.to_dict())' runs before any
   hard skip, including all nested replies.
2. Author IDs, chronological information, parent links and evidence message
   IDs are preserved in a 'ContextFrame'.
3. A conservative no-provider fallback groups signals from the *same*
   original author, detecting recurrent pains, alternatives, constraints
   and the latest explicit goal.
4. When opted in, a separate OpenAI-compatible local-first LLM interprets
   the whole conversation in 9k-character rolling windows. Its previous
   state is carried forward, citations are checked against known IDs,
   and third-party citations alone cannot ground first-person intent.
5. Strong contextual needs bypass premature post-specific filtering.
   The final *selected* intent still goes through the existing reality
   checker, trigger analyzer, business scoring and market validation.
6. The frame is carried through to 'WishData.context_frame' and to the
   reformulator's structured problem/desired outcome/constraints/attempts/
   evidence fields, then to storage and Genesis's consumers.

This is a targeted change to the data flow, not a forked detector universe.

## Contract: ContextFrame

- source_id, primary_actor, message_count
- language, domain
- problem: explicitly described issue (not a product guess)
- desired_outcome: goal from original author
- intent: final candidate description
- constraints, attempted_solutions, rejected_alternatives, unmet_needs
- evidence: source message ID, author and excerpt
- other_actor_signals: contextual corroboration ONLY, not the author's wishes
- epistemic_status: explicit / inferred / unknown
- interpretation_method: rules / llm_contextual
- actionable, confidence, needs_review

Every claim about a person is a hypothesis until grounded; a market opportunity
requires independent market research. A confidence score is NOT a calibrated
probability or proof of customer willingness to pay.

## Example (RO)

1. OP: "Am încercat trei programe de contabilitate. Toate sunt o porcărie."
2. OP: "Primul era scump, al doilea complicat, al treilea nu se conecta cu banca."
3. OP: "Vreau doar să termin facturile seara, fără să stau două ore."
4. OP: "Dacă ar face cineva unul simplu, l-aș încerca imediat."

One **combined** context yields accounting, a multi-alternative mismatch,
constraints of time/usability/cost/bank integration, the goal of quick
invoicing, and willingness to TRY a new alternative. It does NOT establish
willingness to PAY or a concrete MVP specification.

## Inference configuration (no surprise API expenses)

Default: no LLM calls; simple, explainable, conservative rules. To use a
running local Ollama OpenAI-compatible API:

    export WISHCATCHER_CONTEXT_LLM_ENABLED=1
    export WISHCATCHER_CONTEXT_LLM_URL=http://127.0.0.1:11434/v1/chat/completions
    export WISHCATCHER_CONTEXT_MODEL=qwen2.5:3b-instruct

Install and run the model locally separately. For remote or paid providers,
explicitly set 'WISHCATCHER_CONTEXT_ALLOW_REMOTE=1' and configure
'WISHCATCHER_CONTEXT_API_KEY' and URL, knowing content is sent to that provider.
Remote is disallowed by default; model errors fall back to rules.

The LLM uses structured JSON, temperature 0, a grounding system prompt and
incremental rolling context across oversized threads. Model outputs with no
valid evidence for the original speaker are rejected. This is not a proof of
truth; human-reviewed benchmarks are necessary, especially for implicit needs,
long-term reference resolution, irony and mixed-speaker discussions.

The collector should only fetch lawfully accessible, permitted content. Keep
raw input access limited, data retention bounded and original authors separate.

## Verification plan

- Tests: 'python -m unittest discover -s tests -v'
- CI: '.github/workflows/contextual-intent-tests.yml' (provider-free).
- GOLD benchmark: label >=100 RO and EN conversations as explicit / implicit /
  hypothetical / negative / changed-intent / no opportunity, with ground-truth
  actor IDs, supporting evidence spans, problem and desired outcome.
- Compare baseline against CIR on recall, precision, false discovery rate,
  actor attribution, contradiction correction, grounding coverage, latency
  and CPU/API cost. Do not treat raw number of wishes as success.
- E2E: mock collectors and paid providers; verify '/collect' -> WishData ->
  persistent storage -> Genesis BusinessPlan/MVP consumers. Add production
  DB migration and telemetry only after proving semantic quality.

## Known limitations / debts

- Rules fallback cannot achieve model-level semantic or anaphora resolution.
- Current confidence values are heuristics; no calibrated accuracy claim.
- A cited LLM hypothesis may still be semantically unsupported even if the
  cited message ID exists. Future validators should check per-field entailment
  and contradiction by independent tests.
- Only original-speaker intent is published as a Wish; other actors' needs
  would require separate, independent ContextFrames.
- Some collectors omit author IDs and full comments, reducing attribution
  confidence. Data quality gates should track this.
- Genesis remains more business-plan and template oriented than original
  universal component-composition spec. This patch improves the upstream
  intent contract; it does not close that downstream architectural gap.
- Tests are provider-free contracts; passing them alone does not imply
  production-quality extraction or scientific evidence of accuracy.
