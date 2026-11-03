# WishCatcher Studio — Install & Use

Status: self-hosted, single-operator v1. A functional context plugin, protected
web UI, local SQLite graph-assisted RAG, optional LLM provider, Brave web
search and MCP read/search adapter. No paid provider is required.

This does NOT claim parity with proprietary OpenAI ad systems or proven market
demand. Context-inference quality with a real LLM must be benchmarked.

## Docker Compose: start the product

Requirements: Docker Engine/Desktop with Compose v2, ports 3000/8000 free.

From repository root:

    cp .env.example .env
    python -c "import secrets; print(secrets.token_urlsafe(48))"

Run the Python secret command TWICE, put each result into its separate
WISHCATCHER_PLUGIN_ACCESS_TOKEN and WISHCATCHER_DASHBOARD_ACCESS_TOKEN
variable in .env. Never use the REPLACE_ME placeholders in a real deployment.

    docker compose up -d --build

Open http://127.0.0.1:3000 and enter the DASHBOARD token in the password
field. Click Verifică integrarea. The example four-message accounting thread
is already loaded. Click Analizează conversația, then Generează schița
Genesis. Optionally publish the grounded opportunity into WishStorage with
Publică oportunitatea în Genesis Storage; such opportunities are UNVERIFIED.

Backend health endpoint: http://127.0.0.1:8000/health

    docker compose down

Both ports are explicitly bound to loopback by default. Local data survives
normal stops in the named Docker volume wishcatcher_rag. Do not expose
the service publicly without TLS, robust authentication, quotas, and
multi-tenant isolation if applicable.

## No Docker: Python and Next.js

Requirements: Python 3.11+ and Node.js 20+.

Terminal 1, from repository root:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements-plugin.txt
    export WISHCATCHER_PLUGIN_ACCESS_TOKEN=<strong-random-secret>
    export WISHCATCHER_RAG_DB=./local_data/knowledge.sqlite3
    export WISHCATCHER_WISH_DIR=./local_data/wishes
    python -m uvicorn app.plugin_app:app --app-dir backend --host 127.0.0.1 --port 8000

Terminal 2, from repo root:

    cd frontend
    npm ci
    export WISHCATCHER_INTERNAL_API_URL=http://127.0.0.1:8000
    export WISHCATCHER_PLUGIN_ACCESS_TOKEN=<same-backend-secret>
    export WISHCATCHER_DASHBOARD_ACCESS_TOKEN=<different-random-secret>
    npm run dev

Open http://127.0.0.1:3000. Windows PowerShell uses $env:NAME='value'
instead of export. Do not put secrets in shared shell history or commit them.

## Minimal CLI (no frontend)

    python scripts/wishcatcher_cli.py analyze examples/accounting_thread.json
    python scripts/wishcatcher_cli.py solution examples/accounting_thread.json
    python scripts/wishcatcher_cli.py analyze examples/accounting_thread.json --retrieve

Add approved knowledge:

    python scripts/wishcatcher_cli.py ingest knowledge:mydoc ./my-knowledge.txt
    python scripts/wishcatcher_cli.py link knowledge:mydoc knowledge:otherdoc

Pass --remember only if you want local persistence of a minimized unmet-need
summary. Pass --research only when the external tools have been configured
and you deliberately want them called.

In other Python apps, import WishCatcherPlugin from
app.wishcatcher.integrations.plugin_runtime; see docs/PLUGIN_RUNTIME.md.
Protected API actions: analyze, config, solution, publish, wishes, knowledge,
knowledge/link under /api/context/. All require X-WishCatcher-Key.

## LLM selection: optional provider plugin

Default: WISHCATCHER_CONTEXT_LLM_ENABLED=0. Without an LLM, deterministic
fallback rules approximate intent but cannot match advanced multi-turn
semantic reasoning. Do not interpret a fallback fragment as verified desire.

To use local Ollama on the same machine (outside Docker):

    WISHCATCHER_CONTEXT_LLM_ENABLED=1
    WISHCATCHER_CONTEXT_LLM_URL=http://127.0.0.1:11434/v1/chat/completions
    WISHCATCHER_CONTEXT_MODEL=qwen2.5:3b-instruct

Run and provision the model separately. In Docker, use
http://host.docker.internal:11434/v1/chat/completions (mapped via
host-gateway). The host model server must allow local container connections.
Keep firewall rules restrictive. Running the plugin outside Docker is
simpler when using a private host-local model.

To use OpenAI or another compatible remote provider:

    WISHCATCHER_CONTEXT_LLM_ENABLED=1
    WISHCATCHER_CONTEXT_LLM_URL=https://api.openai.com/v1/chat/completions
    WISHCATCHER_CONTEXT_MODEL=<supported-provider-model>
    WISHCATCHER_CONTEXT_API_KEY=<private-api-key>
    WISHCATCHER_CONTEXT_ALLOW_REMOTE=1

Remote API calls transmit source conversation content and may incur costs.
Use the correct model ID and verify JSON-mode support. Server-side model
timeout is configurable with WISHCATCHER_CONTEXT_LLM_TIMEOUT_SEC.

## RAG, web search, and MCP

Local RAG: SQLite FTS5 textual indexing + typed graph edges, enabled
when requested. It is NOT vector embeddings or neural GraphRAG.
Use the Studio Knowledge tab or CLI to add vetted documents. A new
conversation is NOT automatically saved unless remember=true.

Brave search: set WISHCATCHER_WEB_SEARCH_ENABLED=1 and
WISHCATCHER_BRAVE_API_KEY, then check Research extern in the Studio.
Brave may require a paid subscription; results are untrusted source data.

MCP: for Docker set WISHCATCHER_INSTALL_MCP=true and rebuild. For
non-Docker Python install requirements-plugin-mcp.txt. Configure
WISHCATCHER_MCP_ENABLED=1, WISHCATCHER_MCP_ENDPOINT,
WISHCATCHER_MCP_SEARCH_TOOL and WISHCATCHER_MCP_READ_ONLY_TOOLS.
Tool execution is intentionally limited to a configured search tool.
Only use audited/trusted MCP servers: read-only names alone do not
guarantee harmless behaviour. No provider calls or MCP tool executions
occur by default.

## Interpreting results correctly

The plugin reconstructs a problem, desired outcome, intent, attempted
solutions, constraints and source-message evidence. It separates
explicit statements from inferences and keeps external web/RAG research
distinct from what the original person said.

Genesis gives three alternative solution hypotheses and a dependency
structure. Its MARKET DEMAND and WILLINGNESS TO PAY are UNKNOWN until
verified. It does not invent revenue forecasts.

## Troubleshooting and limits

- 503 on config: missing or example backend secret; rotate placeholders.
- 401 in Studio: the dashboard token is missing/wrong; it differs from
  the backend plugin token.
- 502: backend unavailable, misconfigured host or inference timeout.
- Results look like regex fragments: LLM provider disabled or unavailable.
- Local model unreachable from Docker: check host-gateway, model binding
  and host firewall, or use the non-Docker setup.
- Reddit comments missing: platform may deny access; the collector only
  hydrates a capped number of threads and respects permissions.
- RAG empty: add indexed documents with relevant terms. This first
  implementation is lexical, not dense semantic search.

GitHub Actions verifies actual FastAPI HTTP requests, WishStorage roundtrips,
CLI outputs, mock Reddit thread hydration, frontend build and Compose config.
Live local/remote model and MCP provider connections remain configuration-
dependent and must be tested with your own model/API/provider.

Draft code review: https://github.com/Selmaka85/WishCatcher/pull/1
See also docs/PLUGIN_RUNTIME.md, docs/CONTEXTUAL_INTENT_GENESIS.md,
.ai_ram.md and .scaffold_driven_boilerplate.md.
