"""
Punto de entrada. Se ejecuta una vez por día desde GitHub Actions.

Flujo:
1. Calcula "ayer" en horario argentino.
2. Para cada fuente de noticias: RSS si existe (o se descubre), si no scraping.
   Filtra artículos publicados ayer y no vistos antes.
3. Para cada canal de YouTube: busca videos subidos ayer, baja transcripción.
4. Le pasa cada noticia/video a Claude para relevancia + resúmenes + leyes.
5. Genera resúmenes de las leyes/proyectos detectados.
6. Arma la página del reporte (docs/reports/AAAA-MM-DD.html) y el email.
7. Manda el email y guarda el estado actualizado.
"""
import calendar
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zoneinfo import ZoneInfo

from src import config, state
from src.ai import claude as ai
from src.email_sender import send_email
from src.fetchers import rss_fetcher, scraper_fetcher, youtube_fetcher
from src.report.builder import build_email_html, build_report_page

TZ = ZoneInfo(config.TIMEZONE)


def _yesterday_range():
    now_local = datetime.now(TZ)
    yesterday = (now_local - timedelta(days=1)).date()
    start = datetime.combine(yesterday, datetime.min.time(), tzinfo=TZ)
    end = datetime.combine(yesterday, datetime.max.time(), tzinfo=TZ)
    return yesterday, start, end


def _struct_to_dt(struct_time) -> datetime | None:
    if not struct_time:
        return None
    ts = calendar.timegm(struct_time)  # struct viene en UTC (feedparser/trafilatura normalizan a UTC)
    return datetime.fromtimestamp(ts, tz=ZoneInfo("UTC")).astimezone(TZ)


def collect_news(st: dict, start, end) -> list[dict]:
    collected = []
    for source in config.NEWS_SOURCES:
        name, url, priority = source["name"], source["url"], source["priority"]
        print(f"[news] procesando fuente: {name}")

        feed_url = st["discovered_rss"].get(url) or source.get("rss")
        if feed_url is None:
            feed_url = rss_fetcher.discover_feed_url(url)
            st["discovered_rss"][url] = feed_url or ""

        raw_articles = []
        if feed_url:
            try:
                raw_articles = rss_fetcher.fetch_rss_articles(feed_url)
            except Exception as e:
                print(f"  [!] error leyendo RSS de {name}: {e}")

        if not raw_articles:
            print(f"  sin RSS utilizable, usando scraping para {name}")
            try:
                raw_articles = scraper_fetcher.fetch_scraped_articles(url)
            except Exception as e:
                print(f"  [!] error scrapeando {name}: {e}")

        for art in raw_articles:
            if art["url"] in st["seen_articles"]:
                continue
            pub_dt = _struct_to_dt(art.get("published_struct"))
            # Si no hay fecha confiable, lo incluimos igual (mejor de más que
            # perder noticias) y confiamos en el filtro de "no visto antes".
            if pub_dt and not (start <= pub_dt <= end):
                continue

            full_text = art.get("text") or art.get("summary") or ""
            collected.append({
                "source": name,
                "priority": priority,
                "title": art["title"],
                "url": art["url"],
                "text": full_text,
            })
            st["seen_articles"].append(art["url"])
    return collected


def collect_videos(st: dict, start, end) -> list[dict]:
    collected = []
    for channel in config.YOUTUBE_CHANNELS:
        name, handle = channel["name"], channel["handle"]
        print(f"[youtube] procesando canal: {name}")

        channel_id = st["channel_ids"].get(handle)
        if not channel_id:
            channel_id = youtube_fetcher.resolve_channel_id(handle)
            if not channel_id:
                print(f"  [!] no se pudo resolver el channel_id de {handle}")
                continue
            st["channel_ids"][handle] = channel_id

        try:
            videos = youtube_fetcher.fetch_channel_videos(channel_id)
        except Exception as e:
            print(f"  [!] error leyendo feed de {name}: {e}")
            continue

        for video in videos:
            if video["video_id"] in st["seen_videos"]:
                continue
            pub_dt = _struct_to_dt(video.get("published_struct"))
            if pub_dt and not (start <= pub_dt <= end):
                continue

            transcript = youtube_fetcher.get_transcript(video["video_id"])
            st["seen_videos"].append(video["video_id"])
            if not transcript:
                print(f"  [!] sin transcripción disponible: {video['title']}")
                continue

            collected.append({
                "channel": name,
                "title": video["title"],
                "url": video["url"],
                "transcript": transcript,
            })
    return collected


def analyze_news(raw_news: list[dict]) -> list[dict]:
    analyzed = []
    for art in raw_news:
        result = ai.analyze_article(art["source"], art["priority"], art["title"], art["text"])
        if not result.get("relevant"):
            continue
        analyzed.append({
            "source": art["source"],
            "url": art["url"],
            "one_liner": result.get("one_liner") or art["title"],
            "full_summary": result.get("full_summary", ""),
            "laws_mentioned": result.get("laws_mentioned", []) or [],
            "context_text": art["text"],
        })
        time.sleep(0.3)  # margen prudente frente a rate limits
    return analyzed


def analyze_videos(raw_videos: list[dict]) -> list[dict]:
    analyzed = []
    for vid in raw_videos:
        result = ai.analyze_video(vid["channel"], vid["title"], vid["transcript"])
        analyzed.append({
            "channel": vid["channel"],
            "url": vid["url"],
            "one_liner": result.get("one_liner") or vid["title"],
            "full_summary": result.get("full_summary", ""),
        })
        time.sleep(0.3)
    return analyzed


def build_law_summaries(st: dict, news_items: list[dict]) -> dict:
    laws = {}
    for item in news_items:
        for law_name in item["laws_mentioned"]:
            if law_name in laws:
                continue
            cached = st["law_summaries"].get(law_name)
            if cached:
                laws[law_name] = cached
                continue
            summary = ai.summarize_law(law_name, item["context_text"])
            laws[law_name] = summary
            st["law_summaries"][law_name] = summary
            time.sleep(0.3)
    return laws


def update_reports_index(reports_dir: str):
    """Genera un índice simple de todos los reportes publicados."""
    files = sorted(
        [f for f in os.listdir(reports_dir) if f.endswith(".html") and f != "index.html"],
        reverse=True,
    )
    items = "".join(f'<li><a href="reports/{f}">{f.replace(".html", "")}</a></li>' for f in files)
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Novedades de energía — reportes</title></head>
<body style="font-family:sans-serif;max-width:600px;margin:40px auto;">
<h1>Reportes diarios</h1><ul>{items}</ul></body></html>"""
    with open(os.path.join(reports_dir, "..", "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def main():
    st = state.load_state()
    yesterday, start, end = _yesterday_range()
    date_str = yesterday.strftime("%d/%m/%Y")
    file_date = yesterday.strftime("%Y-%m-%d")

    print(f"=== Procesando novedades del {date_str} ===")

    raw_news = collect_news(st, start, end)
    raw_videos = collect_videos(st, start, end)

    print(f"{len(raw_news)} artículos candidatos, {len(raw_videos)} videos con transcripción")

    news_items = analyze_news(raw_news)
    video_items = analyze_videos(raw_videos)
    laws = build_law_summaries(st, news_items)

    print(f"{len(news_items)} noticias relevantes, {len(video_items)} videos, {len(laws)} leyes/proyectos")

    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    reports_dir = os.path.join(docs_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    report_html = build_report_page(date_str, news_items, video_items, laws)
    report_filename = f"{file_date}.html"
    with open(os.path.join(reports_dir, report_filename), "w", encoding="utf-8") as f:
        f.write(report_html)

    update_reports_index(reports_dir)

    base_url = config.SITE_BASE_URL.rstrip("/")
    report_url = f"{base_url}/reports/{report_filename}" if base_url else f"reports/{report_filename}"

    email_html = build_email_html(date_str, news_items, video_items, report_url)
    subject = f"{config.EMAIL_SUBJECT_PREFIX} — {date_str}"

    if news_items or video_items:
        send_email(subject, email_html)
        print("Email enviado.")
    else:
        send_email(subject + " (sin novedades)", email_html)
        print("No hubo novedades; se envió igual un email breve.")

    state.save_state(st)
    print("Listo.")


if __name__ == "__main__":
    main()
