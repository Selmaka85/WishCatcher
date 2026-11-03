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
    if not expected or expected.startswith("REPLACE_ME"):
        raise HTTPException(503, detail="Plugin API disabled: configure a strong access token")
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


class PublishRequest(BaseModel):
    conversation: Dict[str, Any]
    source: str = Field(default="manual", min_length=1, max_length=100)


@router.post("/publish", dependencies=[Depends(require_plugin_token)])
async def publish_context(request: PublishRequest) -> Dict[str, Any]:
    """Publish a grounded opportunity into the original WishStorage contract.

    Publishing is explicit. Unverified opportunity remains unverified; this
    endpoint does not fabricate prices, market sizes or financial projections.
    """
    import hashlib
    from datetime import datetime, timezone
    from app.api.models import WishData
    from app.storage.wish_storage import WishStorage

    if len(str(request.conversation)) > 200_000:
        raise HTTPException(413, detail="Thread too large")
    frame = (await WishCatcherPlugin().analyze(request.conversation)).frame
    if not frame.get("actionable") or not frame.get("evidence"):
        raise HTTPException(422, detail="A grounded, actionable intent is required before publishing")
    seed = "|".join(str(frame.get(k) or "") for k in (
        "source_id", "primary_actor", "intent",
    ))
    ident = "ctx_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    structured = {
        "what": frame.get("desired_outcome") or frame["intent"],
        "why": frame.get("problem") or "",
        "who": "unknown",
        "when": "unknown",
        "how": "requires_solution_validation",
        "problem": frame.get("problem") or "",
        "desired_outcome": frame.get("desired_outcome") or "",
        "constraints": frame.get("constraints") or [],
        "attempted_solutions": frame.get("attempted_solutions") or [],
        "evidence": frame["evidence"],
        "epistemic_status": frame.get("epistemic_status") or "unknown",
    }
    wish = WishData(
        id=ident,
        intent=str(frame["intent"])[:500],
        intent_full=str(frame["intent"])[:1000],
        structured=structured,
        context_frame=frame,
        domain=str(frame.get("domain") or "other"),
        score=float(frame.get("confidence") or 0.0),
        business_score=0.0,
        feasibility="unverified",
        technologies=[],
        source=request.source,
        timestamp=datetime.now(timezone.utc),
        market_analysis=None,
        monetization=None,
        market_readiness="not_validated",
    )
    store = WishStorage()
    store.save_wishes([wish])
    return {
        "published": True, "wish_id": ident,
        "validation_status": "UNVERIFIED",
        "source_evidence_count": len(frame["evidence"]),
    }


@router.get("/wishes", dependencies=[Depends(require_plugin_token)])
def published_wishes(limit: int = 25, offset: int = 0) -> Dict[str, Any]:
    """Read published opportunities. Access limited to operator token."""
    from app.storage.wish_storage import WishStorage
    limit = max(1, min(limit, 100))
    offset = max(0, min(offset, 100000))
    items = WishStorage().list_wishes(limit=limit, offset=offset)
    return {"total_returned": len(items), "wishes": [
        item.model_dump(mode="json") for item in items
    ]}
