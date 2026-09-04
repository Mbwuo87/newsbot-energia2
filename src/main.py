"""
Orquestador principal del News Bot.
Flujo: colectar -> filtrar 7 días -> puntuar -> resumir -> detectar leyes ->
       publicar páginas -> renderizar email -> enviar.
"""
from __future__ import annotations
import os
import sys
import yaml
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.rss import collect_rss
from src.collectors.scraper import collect_scrape, fetch_article_text
from src.collectors.youtube import collect_youtube
from src.processing.ai_client import AIClient
from src.processing.relevance import score_articles, select_relevant
from src.processing.summarize import summarize_article, one_line, summarize_video
from src.processing.laws import LawRegistry
from src.render.render import render_email
from src.publish.pages import write_law_pages, write_webview
from src.notify.email_sender import send_email


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def within_window(dt: datetime, days: int) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    sources = load_yaml("config/sources.yaml")
    settings = load_yaml("config/settings.yaml")
    window = settings.get("window_days", 7)

    ai = AIClient(settings)
    print(f"[Init] IA {'ACTIVA' if ai.enabled else 'desactivada (fallback extractivo)'}")

    pages_base = os.getenv("PAGES_BASE_URL", settings.get("pages_base_url", ""))
    laws = LawRegistry(settings, ai, pages_base)

    # ---------- 1. COLECTA NOTICIAS ----------
    articles = []
    for src in sources.get("rss", []):
        try:
            got = collect_rss(src)
            print(f"[RSS] {src['name']}: {len(got)} items")
            articles += got
        except Exception as e:
            print(f"[RSS] ERROR en {src.get('name')}: {e}")

    for src in sources.get("scrape", []):
        if not src.get("enabled", True):
            continue
        try:
            got = collect_scrape(src)
            print(f"[Scrape] {src['name']}: {len(got)} items")
            articles += got
        except Exception as e:
            print(f"[Scrape] ERROR en {src.get('name')}: {e}")

    articles = [a for a in articles if within_window(a.published, window)]
    print(f"[Filtro] {len(articles)} noticias en los últimos {window} días")

    # ---------- 2. PUNTUAR Y SELECCIONAR ----------
    score_articles(articles, settings, ai)
    relevant = select_relevant(articles, settings)
    print(f"[Relevancia] {len(relevant)} noticias seleccionadas")

    # ---------- 3. RESUMIR NOTICIAS + LEYES ----------
    news_ctx = []
    for a in relevant:
        if not a.raw_summary or len(a.raw_summary) < 120:
            a.body = fetch_article_text(a.url)
        a.summary = summarize_article(a, settings, ai)
        summary_html = laws.process(a.summary)
        news_ctx.append({
            "one_line": one_line(a, ai),
            "summary_html": summary_html,
            "score": a.score,
            "source": a.source,
            "url": a.url,
            "date": a.published.strftime("%d/%m/%Y"),
        })

    # ---------- 4. YOUTUBE ----------
    videos = []
    for ch in sources.get("youtube", []):
        if not ch.get("enabled", True):
            continue
        try:
            got = collect_youtube(ch)
            got = [v for v in got if within_window(v.published, window)]
            print(f"[YT] {ch['name']}: {len(got)} videos nuevos")
            videos += got
        except Exception as e:
            print(f"[YT] ERROR en {ch.get('name')}: {e}")

    videos_ctx = []
    for v in videos:
        v.summary = summarize_video(v, settings, ai)
        summary_html = laws.process(v.summary)
        videos_ctx.append({
            "title": v.title,
            "summary_html": summary_html,
            "channel": v.channel,
            "url": v.url,
            "date": v.published.strftime("%d/%m/%Y"),
        })

    # ---------- 5. PÁGINAS DE LEYES (GitHub Pages) ----------
    write_law_pages(laws.all_refs())

    # ---------- 6. RENDER EMAIL ----------
    now = datetime.now(timezone.utc)
    context = {
        "subject": f"{settings['email']['subject_prefix']} · {now.strftime('%d/%m/%Y')}",
        "period_start": (now - timedelta(days=window)).strftime("%d/%m/%Y"),
        "period_end": now.strftime("%d/%m/%Y"),
        "total_news": len(news_ctx),
        "total_videos": len(videos_ctx),
        "window_days": window,
        "news": news_ctx,
        "videos": videos_ctx,
        "generated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
        "webview_url": f"{pages_base.rstrip('/')}/index.html" if pages_base else "",
    }
    email_html = render_email(context)
    write_webview(email_html)

    # ---------- 7. ENVIAR ----------
    if dry_run:
        with open("preview.html", "w", encoding="utf-8") as f:
            f.write(email_html)
        print("[Dry-run] Email guardado en preview.html (no se envió).")
    else:
        send_email(context["subject"], email_html)


if __name__ == "__main__":
    main()
