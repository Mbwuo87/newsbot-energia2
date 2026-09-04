"""Colector por web scraping para páginas sin RSS."""
from __future__ import annotations
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin
from dateutil import parser as dateparser

from src.models import Article

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def _extract(node, selector: str, attr: str | None = None) -> str:
    if not selector:
        return ""
    el = node.select_one(selector)
    if not el:
        return ""
    if attr:
        return (el.get(attr) or "").strip()
    return el.get_text(strip=True)


def collect_scrape(source: dict) -> list[Article]:
    """Scrapea una página HTML según los selectores CSS definidos en sources.yaml."""
    articles: list[Article] = []
    resp = requests.get(source["url"], headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    for node in soup.select(source["item_selector"]):
        title = _extract(node, source.get("title_selector", ""))
        link = _extract(node, source.get("link_selector", ""), "href")
        if not title or not link:
            continue
        link = urljoin(source["url"], link)

        published = datetime.now(timezone.utc)
        date_sel = source.get("date_selector")
        if date_sel:
            raw_date = _extract(node, date_sel, source.get("date_attr") or None)
            if raw_date:
                try:
                    published = dateparser.parse(raw_date)
                except (ValueError, TypeError):
                    pass

        articles.append(
            Article(
                title=title,
                url=link,
                source=source["name"],
                category=source.get("category", "general"),
                published=published,
                raw_summary="",
            )
        )
    return articles


def fetch_article_text(url: str) -> str:
    """Baja el cuerpo de una nota para resumirla. Usa trafilatura si está disponible."""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False)
            if text:
                return text.strip()
    except Exception:
        pass
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(resp.text, "lxml")
        paras = [p.get_text(strip=True) for p in soup.find_all("p")]
        return "\n".join(paras[:20])
    except Exception:
        return ""
