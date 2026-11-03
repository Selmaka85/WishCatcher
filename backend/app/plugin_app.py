"""Standalone WishCatcher context plugin (no spaCy or scraper dependencies).

Start: python -m pip install -r requirements-plugin.txt
       uvicorn app.plugin_app:app --app-dir backend --host 127.0.0.1
"""
from fastapi import FastAPI

from app.api.routes.context_plugin import router as context_router

app = FastAPI(
    title="WishCatcher Context Intelligence Plugin",
    version="1.0.0",
    description="Evidence-grounded conversation understanding, opt-in AI/RAG/search/MCP",
)
app.include_router(context_router, prefix="/api/context", tags=["Context Intelligence"])


@app.get("/health")
def health() -> dict[str, str]:
    """No secrets or provider configuration in the public health response."""
    return {"status": "ok", "component": "wishcatcher-context-plugin", "version": "1.0.0"}
