"""Colector de fuentes RSS."""
from __future__ import annotations
import feedparser
from datetime import datetime, timezone
from dateutil import parser as dateparser

from src.models import Article


def _parse_date(entry) -> datetime:
    for key in ("published", "updated", "created"):
        val = entry.get(key)
        if val:
            try:
                return dateparser.parse(val)
            except (ValueError, TypeError):
                pass
    for key in ("published_parsed", "updated_parsed"):
        st = entry.get(key)
        if st:
            return datetime(*st[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def collect_rss(source: dict) -> list[Article]:
    """Descarga y parsea un feed RSS/Atom."""
    articles: list[Article] = []
    feed = feedparser.parse(source["url"])
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        link = entry.get("link") or ""
        if not title or not link:
            continue
        summary = (entry.get("summary") or entry.get("description") or "").strip()
        articles.append(
            Article(
                title=title,
                url=link,
                source=source["name"],
                category=source.get("category", "general"),
                published=_parse_date(entry),
                raw_summary=summary,
            )
        )
    return articles
