"""Generación de resúmenes para noticias y videos."""
from __future__ import annotations
import re

from src.models import Article, Video
from src.processing.ai_client import AIClient


def _extractive(text: str, n_sentences: int) -> str:
    """Fallback sin IA: primeras N oraciones limpias."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(parts[:n_sentences]).strip()


def summarize_article(article: Article, cfg: dict, ai: AIClient) -> str:
    source_text = article.body or article.raw_summary or article.title
    if ai.enabled and (article.body or len(article.raw_summary) > 120):
        system = (
            "Sos un periodista. Resumí la noticia en 2-3 oraciones claras y objetivas "
            "en español. No inventes datos que no estén en el texto."
        )
        out = ai.complete(system, source_text[:6000], max_tokens=220)
        if out:
            return out
    n = cfg.get("ai", {}).get("news_summary_sentences", 3)
    return _extractive(source_text, n) or article.title


def one_line(article: Article, ai: AIClient) -> str:
    """Asunto resumido en 1 renglón para la lista de la parte 1."""
    if ai.enabled:
        system = (
            "Resumí el título de esta noticia en UNA sola línea corta (máx 90 caracteres), "
            "clara y sin comillas, en español."
        )
        out = ai.complete(system, article.title, max_tokens=40)
        if out:
            return out.strip().strip('"')[:120]
    return article.title[:120]


def summarize_video(video: Video, cfg: dict, ai: AIClient) -> str:
    if not video.transcript:
        return "(Sin transcripción disponible para este video.)"
    if ai.enabled:
        system = (
            "Sos un analista. Resumí la transcripción de este video de YouTube en "
            "4-6 puntos clave en español, en prosa breve. Enfocate en hechos y datos."
        )
        out = ai.complete(system, video.transcript[:8000], max_tokens=350)
        if out:
            return out
    n = cfg.get("ai", {}).get("video_summary_sentences", 5)
    return _extractive(video.transcript, n)
