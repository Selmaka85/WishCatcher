# Autonomous Discovery — WishCatcher / ASTRA Genesis

Implemented on branch feature/contextual-intent-genesis-20261103. The goal is
to discover **real unmet human needs from broad conversations**, not build an
advertising audience or scrape accounts. No third-party platform login is
required by the built-in public sources. Search snippets are leads, NOT
person-specific evidence or validated market demand.

## Implemented pipeline

Source adapters -> normalized conversation with authors, timestamps and
thread parenthood -> ContextStateBuilder -> rule-based or opt-in LLM intent
resolver -> quality/evidence gate -> atomic SQLite deduplication -> conservative
problem similarity clustering -> source/actor/thread independence checks ->
Genesis evidence-backed solution hypotheses -> persisted discovery index ->
optional local SQLite typed-edge GraphRAG.

The new pipeline is separate from the historical legacy scraper; the latter
still exists but is not silently activated by Context Studio.

## Sources

| Name | Network/data | Account login | Limits |
| --- | --- | --- | --- |
| hn_ask / hn_show / hn_new | Public Hacker News Firebase read API | None | Up to 10 stories per source, 28 comments per story and 6 other speakers |
| search_hn | Brave official Search API leads -> official HN thread hydration | No forum login; Brave API key | Opt-in; only known HN URLs become conversation evidence |
| public_rss | Operator-approved HTTPS RSS/Atom source | None | 25 syndicated entries maximum per request; typically no replies |
| approved_jsonl | Operator-owned/authorized UTF-8 JSONL | None | Explicit permission acknowledgement + path; local only |

Unknown site sources and Reddit anonymous endpoints are deliberately not
enabled. Official Reddit access/commercial rights require approval; do not
circumvent those constraints. Facebook accounts, DMs, private groups, login
walls, CAPTCHAs and paywalled pages are not scraped.

Google/Bing index results can help discover public page URLs, but indiscriminate
direct search-engine HTML scraping is fragile and creates compliance issues.
The Brave Search adapter is a pluggable provider; it is optional and may cost
money. Future connectors can resolve additional INDEX_ONLY_UNVERIFIED leads
through their permitted official API, RSS feeds or authorized public endpoints.

## Start manually from Context Studio

Run the regular app using docs/QUICKSTART_CONTEXT_STUDIO.md.
At http://127.0.0.1:3000:
1. Enter the dashboard access token.
2. Open **Autonomous Discovery**.
3. Choose HN Ask/Show/New, or enabled approved sources.
4. Choose stories per source (1-10).
5. Click **Pornește descoperirea**.
6. Inspect candidates with independent actor/thread counts and Genesis briefs.
7. Use **Istoric execuții** to inspect partial failures.

All server access is protected by the plugin token; the browser only sends
its separate dashboard token to a Next.js same-origin proxy.

## Start CLI, no frontend

From repository root with requirements-plugin.txt installed:

    python scripts/discover.py run --sources hn_ask hn_show --limit 3
    python scripts/discover.py clusters
    python scripts/discover.py runs

With a permitted, user-provided JSONL file:

    export WISHCATCHER_IMPORT_JSONL=/path/to/approved.jsonl
    export WISHCATCHER_IMPORTED_DATA_APPROVED=1
    python scripts/discover.py run --sources approved_jsonl

One JSON object per line. Each record must contain a conversation object
or the root post fields post_id, post_author, post_text, comments (list of
{id,author,text,timestamp,parent_id,replies}). You are responsible for having
rights to store and use this content.

Docker container files must be mounted explicitly when using approved_jsonl.
Never supply an arbitrary user-controlled filesystem path through the HTTP API.

## Optional autonomous scheduling

The periodic worker is OFF by default and isolated from the API process.
In .env:

    WISHCATCHER_AUTODISCOVERY_ENABLED=1
    WISHCATCHER_DISCOVERY_SOURCES=hn_ask,hn_show
    WISHCATCHER_DISCOVERY_INTERVAL_SEC=21600
    WISHCATCHER_DISCOVERY_PER_SOURCE=3
    WISHCATCHER_DISCOVERY_MAX_CONTEXTS=20

Start only the optional Compose profile:

    docker compose --profile autodiscovery up -d --build

This starts the normal Studio + API and the separate Discovery worker.
The minimum scheduled period is 3600 seconds (one hour), default six hours.
No SaaS-wide unattended crawling or unlimited requests. The sources are a
strict allowlist; manual and scheduled jobs share a SQLite lock to prevent
overlapping runs. Network timeouts, bounded per-source errors and run journal
avoid silent failures. To disable, stop the profile and set ENABLED=0.

For a public RSS/Atom feed you are authorized to use:

    WISHCATCHER_RSS_APPROVED=1
    WISHCATCHER_APPROVED_RSS_URL=https://your-permitted-site.example/feed.xml

The feed URL is configured on the server, not accepted from arbitrary
untrusted browser requests. Retrieval rejects non-HTTPS and obvious local
network addresses; a full production deployment should also enforce DNS/IP
network egress policies to prevent DNS rebinding.

For search discovery:

    WISHCATCHER_SEARCH_DISCOVERY_ENABLED=1
    WISHCATCHER_BRAVE_API_KEY=your_server_side_key

This is provider search, not forum logins. Search snippets are not persisted
by default and are not promoted into real author statements. Only known HN
item links are hydrated in this initial search connector.

## Independence, deduplication, clustering

SQLite discovery journal uses WAL, a single-run mutex and transactional
unique keys per source + source-id. Author identities and thread IDs are
represented by keyed HMAC pseudonyms for local independence counting.
Raw speaker identifiers and full discussions are not stored in the journal.

A cluster uses a conservative lexical/RO-EN alias-based similarity score
(minimum 0.74 by default); it is NOT a high-quality semantic vector index.
True multilingual embeddings and reranking remain optional future work.
Potentially related but distinct problems should remain separate rather
than inflating counts.

A cluster reaches CORROBORATED_NEED_HYPOTHESIS only after >=2 distinct
known actors AND >=2 distinct threads; 100 comments from one actor or one
discussion are not counted as 100 independent customers. Other clusters are
SINGLE_SOURCE_HYPOTHESIS. Both have market_demand UNKNOWN and
willingness_to_pay UNKNOWN. Scores rank observed evidence only.

Results include supported messages, domain, problem, desired outcome,
Genesis alternative approaches, explicit uncertainty, signal counts and
run history. No automatic publication as a verified business.

## Quality: explicit vs implicit vs fiction

ContextQualityGate checks:
- source-message references belong to the intended actor
- a problem or goal was actually inferred
- last-message corrections ("problem solved"/"am rezolvat")
- obvious hypothetical/sarcastic examples or third-party reports
- evidence of inferred versus explicit needs
- per-field references when provided by the optional LLM
- claims with real-but-irrelevant citations, using a conservative lexical
  falsification guard (not full semantic entailment)

No LLM can prove a person will purchase something just by interpretation.
Without a model, the rules fallback is coarse and limited. The model
response must be reviewed and matched to supporting evidence; a reported
confidence is NOT a calibrated probability.

Reproduce synthetic evaluation:

    python scripts/evaluate_context.py --dataset benchmarks/context_gold_v1.jsonl

The benchmark contains 32 constructed RO/EN cases and compares baseline
vs quality gate confusion matrices; it is NOT an independent real-world
performance study. A separate >=100 naturally occurring, independently
labeled conversation set plus strong model ablations remains the next gate.

## Repository landmarks

- backend/app/wishcatcher/discovery/sources.py — HN + permitted JSONL
- backend/app/wishcatcher/discovery/rss_source.py — approved RSS/Atom
- backend/app/wishcatcher/discovery/search_discovery.py — Brave index leads
- backend/app/wishcatcher/discovery/pipeline.py — evidence/cluster journal
- backend/app/wishcatcher/discovery/worker.py — opt-in scheduler
- backend/app/wishcatcher/contextual/quality.py — grounded candidate gate
- backend/app/wishcatcher/contextual/context_resolver.py — baseline and LLM
- backend/app/api/routes/context_plugin.py — authenticated discovery APIs
- frontend/components/DiscoveryStudio.tsx — operator console
- scripts/discover.py — direct CLI
- benchmarks/context_gold_v1.jsonl + scripts/evaluate_context.py — evaluation
- tests/test_discovery_pipeline.py + tests/test_discovery_cli.py — regressions

Do not merge to main solely because tests pass. Test actual selected provider,
permissions, accuracy, data retention and real Genesis usefulness first.
