"""
Intenta encontrar y leer el feed RSS de un sitio. Si lo encuentra, devuelve
sus artículos. Si no, devuelve None y el orquestador cae al scraper genérico.
"""
import feedparser
import requests
from bs4 import BeautifulSoup

COMMON_FEED_PATHS = ["/feed/", "/feed", "/rss/", "/rss", "/rss.xml", "/atom.xml", "/feeds/posts/default"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com/)"
}


def discover_feed_url(site_url: str) -> str | None:
    """Busca un <link rel="alternate" type="application/rss+xml"> en el home,
    y si no lo encuentra prueba rutas comunes tipo /feed/."""
    try:
        resp = requests.get(site_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        link = soup.find("link", attrs={"type": "application/rss+xml"})
        if link and link.get("href"):
            href = link["href"]
            if href.startswith("/"):
                base = site_url.rstrip("/")
                href = base + href
            return href
    except Exception:
        pass

    base = site_url.rstrip("/")
    for path in COMMON_FEED_PATHS:
        candidate = base + path
        try:
            resp = requests.get(candidate, headers=HEADERS, timeout=10)
            if resp.status_code == 200 and ("<rss" in resp.text[:500] or "<feed" in resp.text[:500]):
                return candidate
        except Exception:
            continue
    return None


def fetch_rss_articles(feed_url: str) -> list[dict]:
    """Devuelve una lista de dicts: {title, url, published, summary}."""
    parsed = feedparser.parse(feed_url)
    articles = []
    for entry in parsed.entries:
        published = None
        if getattr(entry, "published_parsed", None):
            published = entry.published_parsed
        elif getattr(entry, "updated_parsed", None):
            published = entry.updated_parsed

        articles.append({
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", "").strip(),
            "published_struct": published,
            "summary": BeautifulSoup(entry.get("summary", ""), "html.parser").get_text().strip(),
        })
    return articles
