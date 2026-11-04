# WishCatcher — Systemic Root-Causal Debug Audit
Date: 2026-11-04. Branch: feature/contextual-intent-genesis-20261103, PR #1.
No main merge or production migration.

## System -> Functions -> Relationships

Source selection (discovery/sources.py, discovery/need_search.py)
-> source-verified author/comment/parent/timestamp
-> ContextStateBuilder.flatten
-> EvidenceFirstFallback / optional OpenAICompatibleContextInterpreter
-> ContextQualityGate and actor-specific evidence
-> DiscoveryIndex SQLite dedup and conservative clustering
-> local typed-edge GraphRAG + GenesisContextBridge
-> authenticated Studio operator review and source provenance.

The aim is to recover real unmet human needs, not promote search snippets,
questions, quotations or generic dissatisfaction into market demand.

## Causal defects and fixes

### N1 — Source-selection starvation
Observed live: newest HN Ask/Show sampled 52 actor contexts with one FALSE
positive (Google Flights informational business-model question).
Causal root: selecting only recent stories and bounded top-level replies
misses user-expressed pain elsewhere in comment trees.
Fix: HackerNewsNeedSearch searches HN Algolia public comment index,
then fetches author text and verifies story ancestry against public
HN Firebase source items. Same actor comments only, bounded per source.
Search-index snippets NEVER count as customer evidence; API requires no login.
Regression: forged author, wrong thread, verified actor replies and end-to-end
context -> cluster -> Genesis contracts.

### N2 — Genuine single-comment pain lost at SIGNAL stage
Reproduced RED: "I waste two hours manually exporting invoices..." was
recognized as problem but its evidence was empty and actionable=False.
Root: negative regex recognized substring manual inside manually, but SIGNAL
required manual as whole word or exact waste time, not waste two hours.
Fix: signal detection now covers manually and bounded waste-hours phrasing;
specific long enough firsthand operational pain with constraints can yield
an inferred, needs-review candidate without requiring a second message.
Generic short app complaints remain non-actionable.
Regression: single operational-pain positive vs generic-complaint negative.

### N3 — Quoted-person speech becomes a fake first-person goal
Real post in an Azure security discussion was incorrectly marked as need
because a quoted line started "I want to first say thanks".
Root: HTML-to-text collapsed paragraphs and included quoted paragraphs as
the current actor's text. Goal patterns then gave a valid-looking citation.
Fix: preserve paragraph boundaries; remove > quoted paragraphs and HTML
blockquotes from primary claim extraction.
Regression: Azure quotation and authentic Slack migration pain.
Live recheck with targeted search plus feeds: 58 actor contexts, ONE
remaining plausible candidate (Slack alternative and missing provider
integration clarity), ZERO pipeline/source errors.
This is NOT a representative semantic recall/precision measurement.

### N4 — Reply parent relation dropped
HN adapter provided parent_id but ContextStateBuilder.flatten replaced the
explicit parent with the thread root when replies arrived as a flat list.
Fix: keep supplied parent_id; use structural nesting only when absent.
Regression for flat and genuinely nested replies.

### N5 — Generic intent boilerplate overmerged distinct product needs
Bank-record reconciliation and PDF-invoice export shared many generic
words; similarity scored 0.75, higher than merge threshold 0.74.
Fix: remove generic scaffold words from similarity, require specific overlap
and compatible explicit desired outcomes, normalize some RO/EN synonyms.
Tests guard separated bank/PDF needs and equivalent bilingual invoice needs.
This is conservative lexical grouping, NOT embedding-level semantic matching.

### N6 — Evidence disappeared before Genesis/Studio
ContextFrame included evidence; minimal_frame dropped it before cluster
persistence. Studio showed a synthesis without the original supporting
source text. Users could not audit what Genesis was built on.
Fix: bounded source-message excerpts + original public-thread URL,
up to six independent source-thread samples per cluster, obvious email/token
and number redaction. Compose Genesis from the minimized, redacted frame
rather than raw source. Studio renders message IDs and source links.
Caveat: redaction is best effort, not formal anonymization.

### N7 — Silent rejection funnel
DiscoveryRunner only returned total collected/accepted/skipped.
Fix: aggregate and display rejection_reasons without raw text.
In the real 58-context run: 56 model_or_rules_abstained, one
informational_question_not_unmet_need, one accepted.
Historical persisted run rows do not yet store these details (no DB migration).

### N8 — Deployment/default drift
Python worker + .env default targeted sources, while Compose still
defaulted to hn_ask,hn_show. Repaired Compose fallback to
hn_need_search,hn_ask. Worker remains OFF until the operator enables it.

## Verification and ramifications

Provider-free contract tests cover source spoofing, attribution, timeline,
false positives, single-message recall, quote filtering, discovery indexing,
clustering, RAG, Genesis, CLI and authenticated HTTP. Next production
verification must confirm Python tests, Next.js build, Compose validation
and actual Docker HTTP smoke at final PR HEAD, not an earlier commit.
Real HN network smoke and synthetic RO/EN benchmark are separate findings.
The 32-case synthetic benchmark is NOT measured real-world accuracy.

Open causal chains:
1. Accepted source IDs are immutable snapshots: later reply updates are
   not reprocessed; rejected conversations can be repeatedly evaluated.
   A durable versioned source-state table needs separate schema-change review.
2. Search phrases bias coverage and may miss implicit, nontechnical or
   multilingual needs. Audit sampling and retrieval recall separately.
3. Removing quotes prevents attribution errors but can lose reply context;
   future model-backed reasoning must encode foreign quotes as a separate
   attributed channel, not as the primary actor's own speech.
4. GraphRAG remains lexical FTS5 plus typed links, not dense semantic retrieval.
5. No strong local/remote LLM A/B quality benchmark, semantic entailment
   calibration or human-labeled 100+ RO/EN real-thread reference study yet.
6. Market recurrence counts do NOT establish willingness to pay.
7. Public hosting needs privacy/retention and multi-tenant security work.
8. RSS/index rights and source policies require operator review.

Next quality gate: independent real RO/EN labeled threads, evidence-level
factuality, adversarial quotation tests, targeted sampling vs latest feeds,
and comparable optional LLM evaluation without invented product claims.
