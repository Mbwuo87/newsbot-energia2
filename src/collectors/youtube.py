"""Colector de YouTube: detecta videos nuevos vía RSS del canal y baja transcripciones."""
from __future__ import annotations
import feedparser
from datetime import datetime, timezone

from src.models import Video

# YouTube expone un RSS oculto por canal, sin API key:
YT_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def _get_transcript(video_id: str, languages: list[str]) -> str:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        try:
            data = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        except Exception:
            data = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(seg["text"] for seg in data).strip()
    except Exception:
        return ""


def collect_youtube(channel: dict) -> list[Video]:
    """Devuelve los videos del canal con su transcripción (si existe)."""
    videos: list[Video] = []
    feed = feedparser.parse(YT_FEED.format(channel_id=channel["channel_id"]))
    languages = channel.get("languages", ["es", "es-419", "en"])

    for entry in feed.entries:
        vid = entry.get("yt_videoid") or entry.get("id", "").split(":")[-1]
        if not vid:
            continue
        published = datetime.now(timezone.utc)
        if entry.get("published_parsed"):
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        transcript = _get_transcript(vid, languages)
        videos.append(
            Video(
                title=(entry.get("title") or "").strip(),
                url=entry.get("link") or f"https://www.youtube.com/watch?v={vid}",
                video_id=vid,
                channel=channel["name"],
                published=published,
                transcript=transcript,
            )
        )
    return videos
