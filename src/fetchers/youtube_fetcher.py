"""
Para cada canal (dado por @handle):
1. Resuelve el channel_id real (se cachea en state para no repetir el paso).
2. Lee el feed RSS público de YouTube para ese canal (no requiere API key).
3. Filtra los videos subidos el día anterior.
4. Intenta bajar la transcripción con youtube-transcript-api.
"""
import re

import feedparser
import requests

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com/)"
}


def resolve_channel_id(handle: str) -> str | None:
    handle = handle.lstrip("@")
    url = f"https://www.youtube.com/@{handle}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception:
        return None

    match = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', resp.text)
    if match:
        return match.group(1)
    match = re.search(r'channel/(UC[0-9A-Za-z_-]{22})', resp.text)
    if match:
        return match.group(1)
    return None


def fetch_channel_videos(channel_id: str) -> list[dict]:
    """Devuelve [{video_id, title, url, published_struct}]"""
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    parsed = feedparser.parse(feed_url)
    videos = []
    for entry in parsed.entries:
        video_id = entry.get("yt_videoid") or entry.get("id", "").split(":")[-1]
        videos.append({
            "video_id": video_id,
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", "").strip(),
            "published_struct": entry.get("published_parsed"),
        })
    return videos


def get_transcript(video_id: str) -> str | None:
    """Intenta español primero, después cualquier idioma disponible."""
    try:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["es", "es-419", "es-ES"])
        except NoTranscriptFound:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = next(iter(transcript_list)).fetch()
        return " ".join(chunk["text"] for chunk in transcript)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception:
        return None
