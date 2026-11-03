"""Permission-conscious discovery adapters for WishCatcher.

Hacker News uses the documented public, read-only Firebase API.
JSONL imports let operators ingest content they have permission to use.
New sources implement ConversationSource; no unknown website scraping, Reddit
anonymous endpoints, direct messages or arbitrary URLs are crawled here.
"""
from __future__ import annotations

import asyncio
import html
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence


class _PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def clean_html(value: Any, max_length: int = 4000) -> str:
    parser = _PlainText()
    parser.feed(str(value or "")[:max_length * 2])
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()[:max_length]


@dataclass
class SourceConversation:
    source: str
    source_id: str
    url: str
    conversation: Dict[str, Any]
    license_note: str = ""
    source_type: str = "public"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationSource(Protocol):
    name: str

    async def fetch(self, limit: int = 5) -> List[SourceConversation]:
        ...


class HackerNewsSource:
    """Small bounded HN Ask/Show discovery with replies and attributed authors."""

    name = "hackernews"
    API = "https://hacker-news.firebaseio.com/v0/"
    FEEDS = {"ask": "askstories.json", "show": "showstories.json", "new": "newstories.json"}

    def __init__(
        self, *, feed: str = "ask", client: Any = None,
        max_comments_per_story: int = 28, max_authors_per_story: int = 6,
    ) -> None:
        if feed not in self.FEEDS:
            raise ValueError("Hacker News feed must be ask, show or new")
        self.feed = feed
        self.client = client
        self.max_comments = max(0, min(max_comments_per_story, 50))
        self.max_authors = max(1, min(max_authors_per_story, 10))

    async def _get(self, client: Any, path: str) -> Any:
        response = await client.get(self.API + path)
        response.raise_for_status()
        return response.json()

    async def _story(self, client: Any, story_id: int) -> List[SourceConversation]:
        post = await self._get(client, f"item/{story_id}.json")
        if not isinstance(post, dict) or post.get("deleted") or post.get("dead"):
            return []
        if post.get("type") != "story":
            return []
        title = clean_html(post.get("title"), 300)
        body = clean_html(post.get("text"), 3000)
        post_author = str(post.get("by") or "").strip()
        if not post_author and not body:
            return []
        url = f"https://news.ycombinator.com/item?id={story_id}"
        comments: List[Dict[str, Any]] = []
        queue = [(kid, 0) for kid in (post.get("kids") or [])[:self.max_comments]]
        # Sequential and deliberately bounded: don't hammer the official API.
        visited: set[int] = set()
        while queue and len(visited) < self.max_comments:
            comment_id, depth = queue.pop(0)
            if not isinstance(comment_id, int) or comment_id in visited:
                continue
            visited.add(comment_id)
            try:
                item = await self._get(client, f"item/{comment_id}.json")
            except Exception:
                continue
            if not isinstance(item, dict) or item.get("deleted") or item.get("dead"):
                continue
            author = str(item.get("by") or "").strip()
            text = clean_html(item.get("text"), 1800)
            if author and text:
                comments.append({
                    "id": f"hn:{comment_id}", "author": author,
                    "text": text, "timestamp": float(item.get("time") or 0),
                    "parent_id": f"hn:{item.get('parent') or story_id}",
                })
            if depth < 2:
                for kid in (item.get("kids") or [])[:5]:
                    if isinstance(kid, int) and kid not in visited and len(queue) < 80:
                        queue.append((kid, depth + 1))
        # OP's own context and separate actor-scoped contexts for other speakers.
        # No user's statements become someone else's first-person claims.
        records: List[SourceConversation] = []
        by_author: Dict[str, List[Dict[str, Any]]] = {}
        for item in comments:
            by_author.setdefault(item["author"], []).append(item)
        original = {
            "post_id": f"hn:{story_id}", "post_author": post_author or "__unknown_root_author__",
            "post_title": title, "post_text": body or title,
            "post_timestamp": float(post.get("time") or 0),
            "comments": comments,
            "metadata": {"thread_topic": title, "url": url, "source": self.name},
        }
        records.append(SourceConversation(
            source="hackernews", source_id=f"hn:{story_id}",
            url=url, conversation=original,
            license_note="Public Hacker News Firebase read API; review site policies before redistribution",
        ))
        actors = sorted(
            (author for author in by_author if author != post_author),
            key=lambda author: (-len(by_author[author]), author),
        )[:self.max_authors]
        for actor in actors:
            own = sorted(by_author[actor], key=lambda m: (m["timestamp"], m["id"]))
            if not own:
                continue
            first, rest = own[0], own[1:]
            records.append(SourceConversation(
                source="hackernews", source_id=f"hn:{story_id}:actor:{actor}",
                url=url,
                conversation={
                    "post_id": first["id"], "post_author": actor,
                    "post_title": "", "post_text": first["text"],
                    "post_timestamp": first["timestamp"],
                    "comments": rest,
                    "metadata": {"thread_topic": title, "thread_id": f"hn:{story_id}",
                                 "url": url, "source": self.name},
                },
                license_note="Public Hacker News Firebase read API; do not redistribute full transcripts",
            ))
        return records

    async def fetch(self, limit: int = 5) -> List[SourceConversation]:
        limit = max(1, min(limit, 10))
        import httpx
        async def collect(client: Any) -> List[SourceConversation]:
            story_ids = await self._get(client, self.FEEDS[self.feed])
            if not isinstance(story_ids, list):
                raise ValueError("Hacker News feed must return a list")
            output: List[SourceConversation] = []
            # Fetch a bounded number of stories so non-text entries do not
            # consume the whole batch.
            for story_id in story_ids[:limit]:
                if not isinstance(story_id, int):
                    continue
                try:
                    output.extend(await self._story(client, story_id))
                except Exception:
                    # One malformed or removed story must not stop the batch.
                    continue
            return output
        if self.client is not None:
            return await collect(self.client)
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            return await collect(client)


class ApprovedJSONLSource:
    """Operator-owned conversation imports; never open arbitrary paths via HTTP."""

    name = "approved_jsonl"

    def __init__(self, file_path: str, *, approved: bool = False) -> None:
        if not approved:
            raise PermissionError("Explicit operator confirmation required for imported data")
        self.path = Path(file_path).expanduser().resolve()
        if self.path.suffix.lower() != ".jsonl":
            raise ValueError("Approved imports must be JSONL")
        if not self.path.is_file():
            raise FileNotFoundError(str(self.path))

    async def fetch(self, limit: int = 5) -> List[SourceConversation]:
        limit = max(1, min(limit, 100))
        result: List[SourceConversation] = []
        with self.path.open("r", encoding="utf-8") as file:
            for number, line in enumerate(file, 1):
                if len(result) >= limit:
                    break
                if not line.strip() or len(line) > 200_000:
                    continue
                try:
                    value = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(value, dict):
                    continue
                conversation = value.get("conversation", value)
                if not isinstance(conversation, dict):
                    continue
                text = conversation.get("post_text") or conversation.get("text")
                if not isinstance(text, str) or not text.strip():
                    continue
                identity = str(conversation.get("post_id") or f"{self.path.name}:{number}")
                conversation = {**conversation, "post_id": identity}
                result.append(SourceConversation(
                    source="approved_jsonl", source_id="import:" + identity,
                    url=str(value.get("url") or ""),
                    conversation=conversation,
                    source_type="operator_supplied",
                    license_note="Operator confirms permission and retention rights",
                ))
        return result


def configured_source(name: str) -> ConversationSource:
    """Fail closed for unknown/contract-restricted sources."""
    if name in {"hackernews", "hn_ask"}:
        return HackerNewsSource(feed="ask")
    if name == "hn_show":
        return HackerNewsSource(feed="show")
    if name == "hn_new":
        return HackerNewsSource(feed="new")
    if name == "approved_jsonl":
        import os
        if os.getenv("WISHCATCHER_IMPORTED_DATA_APPROVED") != "1":
            raise PermissionError("Approved JSONL input requires explicit operator acknowledgement")
        path = os.getenv("WISHCATCHER_IMPORT_JSONL", "")
        if not path:
            raise ValueError("WISHCATCHER_IMPORT_JSONL path is required")
        return ApprovedJSONLSource(path, approved=True)
    if name == "reddit":
        raise PermissionError(
            "Reddit requires documented Data API approval/OAuth and written permission "
            "for commercial use; anonymous scraping is not an authorized source."
        )
    raise ValueError("Source not registered. Available: hn_ask, hn_show, hn_new, approved_jsonl")
