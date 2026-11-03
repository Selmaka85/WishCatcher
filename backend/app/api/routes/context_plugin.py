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
