"""Targeted public Hacker News need discovery through Algolia + Firebase.

The Algolia HN Search API discovers candidate *comments*; official Firebase
items verify actor, original text and story membership. We never treat an
index snippet as evidence or silently assign another actor's words to OP.

Limitations: source windows are bounded, not complete actor lifetimes or
entire 1000-comment threads. Search queries prioritize recall candidates,
not proof of need. All candidates still pass ContextQualityGate.
"""
from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.wishcatcher.discovery.sources import (
    ConversationSource, HackerNewsSource, SourceConversation, clean_html,
)


class HackerNewsNeedSearch:
    """Search comments for pain signals; verify via the official HN item API."""

    name = "hackernews"
    SEARCH_API = "https://hn.algolia.com/api/v1/search_by_date"
    # Search is ONLY for discovery, never a judgment about user intent.
    DEFAULT_QUERIES: Tuple[str, ...] = (
        "I wish there was",
        "I'm struggling with",
        "takes me hours",
        "can't find a tool",
        "I need a better way",
        "is there a way to automate",
    )

    # P2 exploration packs: independent search strata, not quality labels.
    # Operators choose a pack explicitly; the historical default remains
    # unchanged until independently annotated coverage comparisons exist.
    QUERY_PACKS: Dict[str, Tuple[str, ...]] = {
        "explicit": DEFAULT_QUERIES,
        "workaround": (
            "I ended up writing a script",
            "we use a spreadsheet instead",
            "doing this by hand",
            "copy and paste every day",
            "we built our own",
            "I have to manually",
        ),
        "friction": (
            "keeps breaking",
            "doesn't integrate with",
            "I spend hours",
            "we had to switch",
            "too many steps",
            "no easy way to",
        ),
        "outcome": (
            "trying to reduce",
            "would save me time",
            "our workflow is",
            "is there a simpler way",
            "we need to track",
            "I wish I could",
        ),
    }

    def __init__(
        self,
        *,
        search_client: Any = None,
        hn_client: Any = None,
        queries: Optional[Sequence[str]] = None,
        query_pack: str = "explicit",
        max_queries: int = 4,
        lookback_days: int = 90,
        max_actor_messages: int = 5,
    ) -> None:
        self.search_client = search_client
        self.hn_client = hn_client
        if query_pack not in self.QUERY_PACKS:
            raise ValueError("Unknown HN query pack; use explicit, workaround, friction or outcome")
        self.query_pack = query_pack
        self.queries = tuple(queries if queries is not None
                             else self.QUERY_PACKS[query_pack])[:6]
        self.max_queries = max(1, min(max_queries, 6))
        self.lookback_days = max(1, min(lookback_days, 365))
        self.max_actor_messages = max(1, min(max_actor_messages, 8))
        self.hn = HackerNewsSource(max_comments_per_story=0, max_authors_per_story=1)
        self.last_query_errors: List[str] = []

    async def _search(self, client: Any, *, query: str, tags: str, count: int) -> List[Dict[str, Any]]:
        response = await client.get(
            self.SEARCH_API,
            params={
                "query": query,
                "tags": tags,
                "hitsPerPage": max(1, min(count, 12)),
                "page": 0,
                "numericFilters": f"created_at_i>{int(time.time()) - self.lookback_days * 86400}",
            },
            headers={"Accept": "application/json", "User-Agent": "WishCatcher/1.3 public-need-research"},
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("hits"), list):
            raise ValueError("HN Search returned invalid hit collection")
        return [hit for hit in data["hits"] if isinstance(hit, dict)]

    @staticmethod
    def _valid_id(value: Any) -> Optional[int]:
        if isinstance(value, bool):
            return None
        try:
            text = str(value)
            if not text.isdigit():
                return None
            numeric = int(text)
            return numeric if 0 < numeric < 2**63 else None
        except (TypeError, ValueError):
            return None

    async def _trace_story(self, client: Any, original: Dict[str, Any],
                           expected_story_id: int) -> Optional[Dict[str, Any]]:
        """Verify comment ancestry: Algolia hit story_id is NOT authority."""
        parent = self._valid_id(original.get("parent"))
        visited: set[int] = set()
        for _ in range(14):
            if parent is None or parent in visited:
                return None
            visited.add(parent)
            item = await self.hn._get(client, f"item/{parent}.json")
            if not isinstance(item, dict) or item.get("dead") or item.get("deleted"):
                return None
            if item.get("type") == "story":
                return item if self._valid_id(item.get("id")) == expected_story_id else None
            if item.get("type") != "comment":
                return None
            parent = self._valid_id(item.get("parent"))
        return None

    async def _conversation(self, search: Any, hn: Any,
                            hit: Dict[str, Any]) -> Optional[SourceConversation]:
        comment_id = self._valid_id(hit.get("objectID"))
        story_id = self._valid_id(hit.get("story_id"))
        actor = str(hit.get("author") or "").strip()
        if (not comment_id or not story_id or not actor
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", actor)):
            return None

        original = await self.hn._get(hn, f"item/{comment_id}.json")
        if not isinstance(original, dict) or original.get("type") != "comment":
            return None
        if original.get("deleted") or original.get("dead") or original.get("by") != actor:
            return None
        own_text = clean_html(original.get("text"), 2400)
        if not own_text:
            return None
        story = await self._trace_story(hn, original, story_id)
        if story is None:
            return None
        title = clean_html(story.get("title"), 220)
        # Reconstruct this actor's other public comments *in this thread*,
        # using the Algolia index only to LOCATE item IDs, and Firebase for text
        # and the actual author. Never insert other speakers' comments into
        # the primary actor's evidence.
        same_author: List[Dict[str, Any]] = [{
            "id": f"hn:{comment_id}", "author": actor,
            "text": own_text, "timestamp": float(original.get("time") or 0),
        }]
        try:
            hits = await self._search(
                search, query="", tags=f"comment,story_{story_id},author_{actor}",
                count=self.max_actor_messages + 2,
            )
        except Exception:
            hits = []
        observed = {comment_id}
        for companion in hits:
            if len(same_author) >= self.max_actor_messages:
                break
            other_id = self._valid_id(companion.get("objectID"))
            if not other_id or other_id in observed:
                continue
            if self._valid_id(companion.get("story_id")) != story_id:
                continue
            observed.add(other_id)
            try:
                candidate = await self.hn._get(hn, f"item/{other_id}.json")
            except Exception:
                continue
            if (not isinstance(candidate, dict)
                    or candidate.get("by") != actor
                    or candidate.get("dead") or candidate.get("deleted")
                    or candidate.get("type") != "comment"):
                continue
            # Search-index story attribution is not an authority, even
            # when the username is verified. Trace every cited companion
            # back to the verified source thread to prevent speaker bleed.
            try:
                related_story = await self._trace_story(hn, candidate, story_id)
            except Exception:
                continue
            if related_story is None:
                continue
            text = clean_html(candidate.get("text"), 2400)
            if text:
                same_author.append({
                    "id": f"hn:{other_id}", "author": actor, "text": text,
                    "timestamp": float(candidate.get("time") or 0),
                })
        same_author.sort(key=lambda m: (m["timestamp"], m["id"]))
        first = same_author[0]
        url = f"https://news.ycombinator.com/item?id={story_id}"
        return SourceConversation(
            source="hackernews", source_id=f"hn:{story_id}:actor:{actor}",
            url=url,
            conversation={
                "post_id": first["id"], "post_author": actor, "post_title": "",
                "post_text": first["text"], "post_timestamp": first["timestamp"],
                "comments": same_author[1:],
                "metadata": {
                    "source": "hackernews", "thread_id": f"hn:{story_id}",
                    "thread_topic": title, "url": url,
                    "coverage": "SEARCH_MATCHED_ACTOR_MESSAGES_PARTIAL_THREAD",
                },
            },
            source_type="public_search_verified",
            license_note="HN Search by Algolia discovery; source messages verified via HN Firebase",
        )

    async def fetch(self, limit: int = 5) -> List[SourceConversation]:
        import httpx
        limit = max(1, min(limit, 10))
        self.last_query_errors = []

        async def execute(search: Any, hn: Any) -> List[SourceConversation]:
            output: List[SourceConversation] = []
            visited: set[Tuple[int, str]] = set()
            hits: List[Dict[str, Any]] = []
            for phrase in self.queries[:self.max_queries]:
                try:
                    hits.extend(await self._search(
                        search, query=phrase, tags="comment",
                        count=min(limit, 5),
                    ))
                except Exception as exc:
                    self.last_query_errors.append(type(exc).__name__)
            for hit in hits:
                if len(output) >= limit:
                    break
                story_id = self._valid_id(hit.get("story_id"))
                actor = str(hit.get("author") or "").strip()
                if not story_id or not actor or (story_id, actor) in visited:
                    continue
                visited.add((story_id, actor))
                try:
                    record = await self._conversation(search, hn, hit)
                except Exception:
                    record = None
                if record is not None:
                    output.append(record)
            if not output and self.last_query_errors:
                raise RuntimeError(
                    "HN Search unavailable: " + ",".join(self.last_query_errors[:4])
                )
            return output

        if self.search_client is not None and self.hn_client is not None:
            return await execute(self.search_client, self.hn_client)
        # Keep both search and HN Firebase read-only and bounded.
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as search:
            async with httpx.AsyncClient(timeout=12, follow_redirects=False) as hn:
                return await execute(search, hn)
