# WishCatcher as a provider-neutral context-intelligence plugin

Updated 2026-11-03. Implementation branch:
feature/contextual-intent-genesis-20261103

## Objective

WishCatcher is a plug-in semantic radar for *broad conversational context*.
It should collect clues spread across posts, comments and replies, reconstruct
one actor's problem and actual desired outcome, preserve evidence, and feed
actionable, traceable unmet needs to the existing WishCatcher -> ASTRA Genesis
opportunity and structural-solution pipeline.

It is NOT a marketing/advertising engine, and it does not reproduce OpenAI's
internal advertising systems. It can be embedded as a Python module, called
from another AI agent, or consumed through its optional FastAPI endpoints.

## Plug-in surfaces

| Capability | Built-in implementation | Default state |
| --- | --- | --- |
| Context state and provenance | ContextStateBuilder, ContextFrame | On |
| Deterministic fallback | EvidenceFirstFallback | On |
| LLM semantic resolver | OpenAI-compatible Chat Completions | Off |
| Local semantic memory | SQLite FTS5 + explicit graph links | On demand |
| Web search | Brave Search API adapter | Off |
| MCP tool search | Optional official Python MCP SDK over HTTP | Off |
| HTTP plugin interface | /api/context/* endpoints | Disabled until token configured |
| Third-party adapters | SearchAdapter, ToolAdapter protocol | Injection only |

**Important:** SQLite FTS5 is lexical indexing, NOT vector embeddings.
The graph extension follows explicit document links; it is not a GNN.
True embedding-based dense retrieval / semantic GraphRAG, reranking and
provider-specific tokenizer budgets remain future extensions and should be
validated separately. None of the tool outputs become the user's asserted
intent automatically.

## Python plugin usage

From the backend working directory (with 'backend' on PYTHONPATH):

\`\`\`python
import asyncio
from app.wishcatcher.integrations.plugin_runtime import WishCatcherPlugin

thread = {
    "post_id": "case_1",
    "post_author": "person_1",
    "post_text": "Am incercat 3 programe de contabilitate; sunt complicate.",
    "comments": [
        {
            "id": "c1", "author": "person_1",
            "text": "Vreau sa termin facturile rapid, fara 2 ore pierdute.",
        }
    ],
}

async def main():
    plugin = WishCatcherPlugin()
    analysis = await plugin.analyze(thread, retrieve_knowledge=True, research=False)
    print(analysis.frame["problem"])
    print(analysis.frame["desired_outcome"])
    print(analysis.frame["evidence"])
    print(analysis.knowledge)

asyncio.run(main())
\`\`\`

With real LLM semantics turned off, the rules baseline is only a conservative
filter and context assembler. For strong coreference, contradiction handling,
irony and implicit-intent inference enable an appropriate capable model.

## LLM adapters: Ollama, LM Studio, OpenAI-compatible providers

The built-in interpreter uses a Chat Completions compatible HTTP endpoint.
It is deliberately OFF unless explicitly configured.

Local Ollama example:

\`\`\`shell
export WISHCATCHER_CONTEXT_LLM_ENABLED=1
export WISHCATCHER_CONTEXT_LLM_URL=http://127.0.0.1:11434/v1/chat/completions
export WISHCATCHER_CONTEXT_MODEL=qwen2.5:3b-instruct
# Run Ollama and ensure the model is available separately.
\`\`\`

For LM Studio or another local compatible server, replace URL and model.
For OpenAI or a compatible remote provider, explicitly set:

\`\`\`shell
export WISHCATCHER_CONTEXT_LLM_ENABLED=1
export WISHCATCHER_CONTEXT_LLM_URL=https://api.openai.com/v1/chat/completions
export WISHCATCHER_CONTEXT_MODEL=<model-you-have-access-to>
export WISHCATCHER_CONTEXT_API_KEY=<YOUR_PRIVATE_API_KEY>
export WISHCATCHER_CONTEXT_ALLOW_REMOTE=1
\`\`\`

Never commit API keys. The API is not free by default; check provider
prices/quotas before enabling remote calls. No endpoint is auto-called merely
because an API key exists. A compatible endpoint may support a subset of
response_format='json_object'; provider integration must be tested per model.

## Local graph RAG (no GPU required)

The default store is
'backend/data/context_graph_rag.sqlite3'. Override with
'WISHCATCHER_RAG_DB=/secure/path/knowledge.sqlite3'.

\`\`\`python
from app.wishcatcher.integrations.plugin_runtime import SQLiteGraphRAG

rag = SQLiteGraphRAG()
rag.put("pain_1", "Accounting software too costly for small firms",
        source="approved-public-source",
        metadata={"evidence_url": "https://example.org/thread"})
rag.put("pain_2", "Invoice reconciliation needs banking integration",
        source="approved-public-source")
rag.link("pain_1", "pain_2", "related_problem")
for hit in rag.retrieve("accounting costs", graph_hops=1):
    print(hit["id"], hit["matched_via"], hit["excerpt"])
\`\`\`

Source texts must be lawfully obtained, cleared for storage and preferably
pseudonymized. Use only trusted knowledge sources for persistent RAG.
Preserve 'source', evidence URL and validation status in metadata.
Avoid persisting private chat histories by default.

## Optional web research

\`\`\`shell
export WISHCATCHER_WEB_SEARCH_ENABLED=1
export WISHCATCHER_BRAVE_API_KEY=<YOUR_PRIVATE_KEY>
\`\`\`

Only 'plugin.analyze(..., research=True)' attempts a web search.
'False' is the default. Treat retrieved search snippets as untrusted evidence,
never as reliable proof that the original person will pay for a product.

## Optional MCP search tools

Current adapter uses the 2026 Python MCP SDK (install optional dependency
'mcp' in the chosen virtual environment). It supports Streamable HTTP,
not arbitrary subprocess launch. Example for a *trusted locally running*
read-only MCP search server:

\`\`\`shell
export WISHCATCHER_MCP_ENABLED=1
export WISHCATCHER_MCP_ENDPOINT=http://127.0.0.1:9000/mcp
export WISHCATCHER_MCP_SEARCH_TOOL=search
export WISHCATCHER_MCP_READ_ONLY_TOOLS=search,search_web
\`\`\`

To connect a remote TLS endpoint, separately set
'WISHCATCHER_MCP_ALLOW_REMOTE=1'. Do not enable write/destructive tools.
An allowlisted tool name is NOT a guarantee of read-only implementation:
trust and audit the MCP server before connection. No MCP tools run on the
default execution path.

Custom search adapters may be injected:

\`\`\`python
plugin = WishCatcherPlugin(web_search=my_search, mcp_search=my_mcp)
\`\`\`

Each adapter implements 'async search(query: str, *, limit: int)' and
returns a list of dictionaries. Retrieval and tool results enrich research;
they cannot be used as first-party conversation evidence.

## Token-protected HTTP endpoints

Configure 'WISHCATCHER_PLUGIN_ACCESS_TOKEN' (random secret) before exposing
plugin routes to any network. The legacy application's other routes keep
their pre-existing security configuration; this token only protects the
new '/api/context/*' endpoints.

- POST /api/context/analyze
  JSON: {"conversation": {...}, "retrieve_knowledge": true, "research": false}
  Reply: {frame, knowledge, external_research, warnings}
- POST /api/context/knowledge
  JSON: {"id": "d1", "text": "...", "source": "approved", "metadata": {}}
- POST /api/context/knowledge/link
  JSON: {"source_id": "d1", "target_id": "d2", "relation": "related"}

All requests need the 'X-WishCatcher-Key' header matching the configured
secret. Missing server configuration fails closed (HTTP 503). Authentication
to these endpoints is not a substitute for TLS, tenant isolation, request
quotas or server-wide access controls in an exposed production deployment.

## End-to-end implementation and scientific status

Implemented: provider-neutral ContextFrame, long-thread rolling LLM context,
conservative fallback, SQLite local graph-assisted retrieval, opt-in Brave
search, allowlisted MCP research adapter, protected plugin API, integration
to original WishCatcher collection and WishData.

Verified: provider-free tests and syntax checks in GitHub Actions.

NOT YET VERIFIED: actual Ollama model quality on hundreds of messages;
production MCP server; live Brave search; remote OpenAI API; actual
WishCatcher -> Genesis production run with all original providers;
semantic precision/recall, paid willingness-to-pay inference and business ROI.

Gate for proving the vision: independent, bilingual gold conversations;
strong baseline comparison; per-field evidence entailment; practical
market validation of resulting needs; and meaningful Genesis solution
generation. Merely finding more "wish" strings is not success.
