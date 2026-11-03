"""Optional authenticated plugin API for contextual intent + local GraphRAG.

Safe by default: endpoints return 503 until WISHCATCHER_PLUGIN_ACCESS_TOKEN is set.
Use direct WishCatcherPlugin imports for in-process, CLI or another agent.
"""
from __future__ import annotations

import os
import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.wishcatcher.integrations.plugin_runtime import SQLiteGraphRAG, WishCatcherPlugin
from app.astra_genesis.context_bridge import GenesisContextBridge

router = APIRouter()


def require_plugin_token(x_wishcatcher_key: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("WISHCATCHER_PLUGIN_ACCESS_TOKEN", "")
    if not expected:
        raise HTTPException(503, detail="Plugin API disabled: configure access token")
    if not x_wishcatcher_key or not secrets.compare_digest(x_wishcatcher_key, expected):
        raise HTTPException(401, detail="Unauthorized")


class ContextAnalysisRequest(BaseModel):
    conversation: Dict[str, Any]
    retrieve_knowledge: bool = False
    research: bool = False
    remember: bool = False  # Explicit local persistence, never on by default


class SolutionRequest(BaseModel):
    conversation: Dict[str, Any]


class KnowledgeDocument(BaseModel):
    id: str = Field(min_length=1, max_length=180)
    text: str = Field(min_length=1, max_length=100000)
    source: str = Field(default="local", max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeLink(BaseModel):
    source_id: str
    target_id: str
    relation: str = "related"


@router.post("/analyze", dependencies=[Depends(require_plugin_token)])
async def analyze_context(request: ContextAnalysisRequest) -> Dict[str, Any]:
    raw_length = len(str(request.conversation))
    if raw_length > 200_000:
        raise HTTPException(413, detail="Thread too large; split into smaller batches")
    plugin = WishCatcherPlugin()
    return (await plugin.analyze(
        request.conversation,
        retrieve_knowledge=request.retrieve_knowledge,
        research=request.research,
        remember=request.remember,
    )).to_dict()


@router.post("/knowledge", dependencies=[Depends(require_plugin_token)])
async def add_knowledge(doc: KnowledgeDocument) -> Dict[str, Any]:
    try:
        store = SQLiteGraphRAG()
        store.put(doc.id, doc.text, source=doc.source, metadata=doc.metadata)
        return {"stored": True, "id": doc.id}
    except (ValueError, OSError) as exc:
        raise HTTPException(400, detail=str(exc)) from exc


@router.post("/knowledge/link", dependencies=[Depends(require_plugin_token)])
async def link_knowledge(link: KnowledgeLink) -> Dict[str, Any]:
    try:
        store = SQLiteGraphRAG()
        store.link(link.source_id, link.target_id, link.relation)
        return {"linked": True}
    except (ValueError, OSError) as exc:
        raise HTTPException(400, detail=str(exc)) from exc


@router.get("/config", dependencies=[Depends(require_plugin_token)])
def plugin_config() -> Dict[str, Any]:
    """Return capabilities, never provider keys, tokens or private endpoints."""
    from urllib.parse import urlparse
    enabled = os.getenv("WISHCATCHER_CONTEXT_LLM_ENABLED", "0") == "1"
    endpoint = os.getenv("WISHCATCHER_CONTEXT_LLM_URL", "http://127.0.0.1:11434/v1/chat/completions")
    host = urlparse(endpoint).hostname
    endpoint_type = (
        "local" if host in {"localhost", "127.0.0.1", "::1"}
        else "remote" if enabled else "none"
    ) if enabled else "none"
    return {
        "version": "1.0.0",
        "interpreter": "openai-compatible" if enabled else "rules",
        "llm_enabled": enabled,
        "llm_endpoint_type": endpoint_type,
        "rag": "sqlite-fts5-graph",
        "web_search_enabled": os.getenv("WISHCATCHER_WEB_SEARCH_ENABLED", "0") == "1",
        "mcp_enabled": os.getenv("WISHCATCHER_MCP_ENABLED", "0") == "1",
    }


@router.post("/solution", dependencies=[Depends(require_plugin_token)])
async def compose_solution(request: SolutionRequest) -> Dict[str, Any]:
    """Generate a traceable Genesis brief, not a fabricated financial plan."""
    if len(str(request.conversation)) > 200_000:
        raise HTTPException(413, detail="Thread too large")
    frame = (await WishCatcherPlugin().analyze(request.conversation)).frame
    try:
        return GenesisContextBridge.compose(frame)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
