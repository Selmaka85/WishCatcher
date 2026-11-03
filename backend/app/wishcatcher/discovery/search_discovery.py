"""Login-free public discovery through permitted, narrow interfaces.

Web search is index DISCOVERY, not evidence of a complete discussion.
We never fetch Google/Facebook pages, bypass authentication, or scrape
arbitrary discovered URLs. Official-source follow-up is required before a
search lead may become a verified thread for contextual processing.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from app.wishcatcher.discovery.sources import HackerNewsSource, SourceConversation


@dataclass(frozen=True)
class IndexedLead:
    title: str
    url: str
    snippet: str
    indexed_by: str = "brave"
    source_status: str = "INDEX_ONLY_UNVERIFIED"

    def public_view(self, *, include_snippet: bool = False) -> Dict[str, str]:
        # Search API result storage rights are plan-dependent. Never persist
        # snippets by default or promote them to actor-grounded intent.
        output = {"title": self.title[:160], "url": self.url[:1000],
                  "indexed_by": self.indexed_by, "source_status": self.source_status}
        if include_snippet:
            output["snippet"] = self.snippet[:400]
        return output


class BraveIndexDiscovery:
    """Official Brave Search API (no search engine page scraping).

    Explicitly opt-in because API credits and result-storage rights may cost.
    Separate requests are bounded and domain-specific to prioritize public
    discussion rather than arbitrary third-party content.
    """

    QUERIES = {
        "en": [
            '"I wish there was" software forum',
            '"I tried" "but" "too expensive" app forum',
            '"waste hours" "manual" "business" discussion',
            '"does anyone know a tool" forum',
        ],
        "ro": [
            '"am încercat" "nu funcționează" forum',
            '"mi-ar trebui" "aplicație" forum',
            '"pierd ore" "manual" "program"',
            '"nu există" "soluție" forum',
        ],
    }

    def __init__(self, client: Optional[Any] = None, *, api_key: Optional[str] = None,
                 enabled: Optional[bool] = None) -> None:
        self.key = api_key if api_key is not None else os.getenv("WISHCATCHER_BRAVE_API_KEY", "")
        self.enabled = enabled if enabled is not None else (
            os.getenv("WISHCATCHER_SEARCH_DISCOVERY_ENABLED", "0") == "1"
        )
        self.client = client

    async def search(self, *, language: str = "en", max_queries: int = 2,
                     per_query: int = 5) -> List[IndexedLead]:
        if not self.enabled or not self.key:
            return []
        if language not in self.QUERIES:
            raise ValueError("Search language must be en or ro")
        max_queries = max(1, min(max_queries, 4))
        per_query = max(1, min(per_query, 10))
        import httpx

        async def collect(client: Any) -> List[IndexedLead]:
            leads: List[IndexedLead] = []
            seen: set[str] = set()
            for query in self.QUERIES[language][:max_queries]:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers={"X-Subscription-Token": self.key, "Accept": "application/json"},
                    params={"q": query, "count": per_query, "search_lang": language},
                )
                response.raise_for_status()
                data = response.json()
                for item in data.get("web", {}).get("results", [])[:per_query]:
                    if not isinstance(item, dict):
                        continue
                    url = str(item.get("url") or "")
                    parsed = urlparse(url)
                    if parsed.scheme != "https" or not parsed.hostname or url in seen:
                        continue
                    seen.add(url)
                    leads.append(IndexedLead(
                        title=str(item.get("title") or "")[:160],
                        url=url[:1000], snippet=str(item.get("description") or "")[:400],
                    ))
            return leads

        if self.client is not None:
            return await collect(self.client)
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            return await collect(client)


class OfficialThreadHydrator:
    """Resolve only known source URLs using read-only official interfaces.

    Other search hits remain LEADS ONLY; their snippets cannot become
    actor-attributed wants, pains, or market demand.
    """

    @staticmethod
    def hn_item_id(url: str) -> Optional[int]:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "news.ycombinator.com":
            return None
        if parsed.path not in {"/item", "/item/"}:
            return None
        values = parse_qs(parsed.query).get("id", [])
        if len(values) != 1 or not values[0].isdigit():
            return None
        result = int(values[0])
        return result if 0 < result < 2**63 else None

    def __init__(self, hackernews: Optional[HackerNewsSource] = None) -> None:
        self.hackernews = hackernews or HackerNewsSource()

    async def hydrate(self, leads: List[IndexedLead], limit: int = 3) -> List[SourceConversation]:
        output: List[SourceConversation] = []
        visited: set[int] = set()
        import httpx
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            for lead in leads:
                if len(visited) >= max(0, min(limit, 10)):
                    break
                ident = self.hn_item_id(lead.url)
                if ident is None or ident in visited:
                    continue
                visited.add(ident)
                try:
                    output.extend(await self.hackernews._story(client, ident))
                except Exception:
                    continue
        return output
