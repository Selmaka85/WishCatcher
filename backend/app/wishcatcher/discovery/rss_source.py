"""Operator-selected public RSS/Atom syndication without login or site scraping.

The operator must supply an approved HTTPS feed URL. Only feed content that
a site intentionally syndicates is consumed. A feed post with no replies
carries limited context and should be independently validated before
an opportunity is promoted.
"""
from __future__ import annotations

import hashlib
import os
import re
import xml.etree.ElementTree as ET
from typing import Any, List, Optional
from urllib.parse import urlparse

from app.wishcatcher.discovery.sources import SourceConversation, clean_html


class PublicRSSSource:
    name = "public_rss"
    def __init__(self, url: str, *, approved: bool = False, client: Optional[Any] = None) -> None:
        if not approved:
            raise PermissionError("RSS feed must be explicitly approved by operator")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Only approved public HTTPS feed URLs are supported")
        # Avoid SSRF: the connector is configured outside HTTP, but still
        # reject obvious internal addresses and common metadata targets.
        import ipaddress
        host = parsed.hostname.lower()
        if host in {"localhost", "metadata.google.internal"} or host.endswith(".internal"):
            raise ValueError("Private RSS destinations are not permitted")
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_global:
                raise ValueError("Private RSS destinations are not permitted")
        except ValueError as exc:
            if "not permitted" in str(exc):
                raise
        self.url = url
        self.client = client

    @staticmethod
    def _tag(value: str) -> str:
        return value.rsplit("}", 1)[-1].lower()

    def _parse(self, text: str, limit: int) -> List[SourceConversation]:
        if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
            raise ValueError("DTD/entity-based RSS documents are disallowed")
        root = ET.fromstring(text)
        out: List[SourceConversation] = []
        records = [x for x in root.iter() if self._tag(x.tag) in {"item", "entry"}]
        for entry in records[:max(1, min(limit, 25))]:
            fields = {self._tag(child.tag): child for child in list(entry)}
            def value(name: str) -> str:
                node = fields.get(name)
                return "".join(node.itertext()).strip() if node is not None else ""
            title = clean_html(value("title"), 220)
            body = clean_html(value("description") or value("summary") or value("encoded") or value("content"), 2400)
            identifier = value("guid") or value("id")
            url = value("link")
            link_node = fields.get("link")
            if not url and link_node is not None:
                url = link_node.attrib.get("href", "")
            p = urlparse(url)
            if p.scheme != "https" or not p.hostname:
                url = self.url
            identifier = identifier or url + ":" + title
            source_id = "rss:" + hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:24]
            author = clean_html(value("creator") or value("author"), 80)
            if not body and not title:
                continue
            out.append(SourceConversation(
                source=self.name, source_id=source_id, url=url,
                conversation={
                    "post_id": source_id, "post_author": author or "__unknown_root_author__",
                    "post_title": title, "post_text": body or title,
                    "comments": [], "metadata": {
                        "source": self.name, "feed_url": self.url,
                        "coverage": "SINGLE_SYNDICATED_ENTRY_NO_REPLIES",
                    },
                },
                source_type="syndicated_public",
                license_note="Operator-selected public RSS; respect publisher reuse rights",
            ))
        return out

    async def fetch(self, limit: int = 5) -> List[SourceConversation]:
        import httpx
        async def collect(client: Any) -> List[SourceConversation]:
            r = await client.get(self.url, headers={
                "Accept": "application/rss+xml,application/atom+xml,application/xml",
                "User-Agent": "WishCatcher/1.2 feed-reader",
            })
            r.raise_for_status()
            if len(r.content) > 2_000_000:
                raise ValueError("RSS feed is larger than maximum allowed")
            return self._parse(r.text, limit)
        if self.client is not None:
            return await collect(self.client)
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            return await collect(client)
