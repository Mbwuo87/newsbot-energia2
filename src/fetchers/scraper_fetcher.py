"""
Scraper genérico para sitios sin RSS.
1) Baja el home y saca los links que parecen notas (dentro de <article>,
   o con pinta de URL de noticia).
2) Para cada link, usa trafilatura para extraer título, texto y fecha.

No es tan preciso como un adaptador hecho a medida por sitio, pero funciona
razonablemente bien en la mayoría de los sitios de noticias. Si notás que a
un sitio en particular le cuesta, avisame y le hago un adaptador específico.
"""
import re
from urllib.parse import urljoin, urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com/)"
}

# Palabras en la URL que casi seguro indican que NO es una nota (son secciones,
# tags, páginas fijas, etc.)
SKIP_PATTERNS = re.compile(
    r"(/tag/|/category/|/author/|/page/|/wp-content/|/feed|\.jpg$|\.png$|\.pdf$|/contacto|/quienes-somos|#)",
    re.IGNORECASE,
)


def _same_domain(base_url: str, link: str) -> bool:
    return urlparse(base_url).netloc == urlparse(link).netloc


def discover_article_links(site_url: str, limit: int = 40) -> list[str]:
    try:
        resp = requests.get(site_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(site_url, href)
        if not _same_domain(site_url, full):
            continue
        if SKIP_PATTERNS.search(full):
            continue
        # Heurística: las notas suelen tener un slug largo con guiones
        path = urlparse(full).path
        if path.count("-") >= 3 or re.search(r"/\d{4}/\d{1,2}/", path):
            links.add(full.split("?")[0])
        if len(links) >= limit:
            break
    return list(links)


def extract_article(url: str) -> dict | None:
    """Devuelve {title, url, published_struct (o None), summary, text} o None
    si no se pudo extraer contenido útil."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    result = trafilatura.extract(
        downloaded,
        include_comments=False,
        output_format="json",
        with_metadata=True,
    )
    if not result:
        return None

    import json as _json
    data = _json.loads(result)

    title = data.get("title") or ""
    text = data.get("text") or ""
    date_str = data.get("date")  # formato "YYYY-MM-DD" normalmente

    published_struct = None
    if date_str:
        import time
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                published_struct = time.strptime(date_str[: len(fmt) + 2], fmt)
                break
            except ValueError:
                continue

    if not title or not text:
        return None

    return {
        "title": title.strip(),
        "url": url,
        "published_struct": published_struct,
        "summary": text[:500],
        "text": text,
    }


def fetch_scraped_articles(site_url: str) -> list[dict]:
    links = discover_article_links(site_url)
    articles = []
    for link in links:
        article = extract_article(link)
        if article:
            articles.append(article)
    return articles
