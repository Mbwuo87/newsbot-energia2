"""Puntuación de relevancia de noticias."""
from __future__ import annotations
import re

from src.models import Article
from src.processing.ai_client import AIClient


def _keyword_score(text: str, cfg: dict) -> float:
    text_low = text.lower()
    score = 0.0
    for group in ("keywords_high", "keywords_medium", "keywords_low", "keywords_negative"):
        block = cfg.get(group)
        if not block:
            continue
        weight = block.get("weight", 0)
        for word in block.get("words", []):
            if word.lower() in text_low:
                score += weight
    return score


def _llm_score(article: Article, ai: AIClient) -> float:
    system = (
        "Sos un editor de noticias. Evaluá qué tan relevante e importante es una "
        "noticia para un lector interesado en política, economía y legislación. "
        "Respondé SOLO con un número entero del 0 (irrelevante) al 5 (muy relevante)."
    )
    user = f"Título: {article.title}\nResumen: {article.raw_summary[:500]}"
    out = ai.complete(system, user, max_tokens=5)
    m = re.search(r"[0-5]", out)
    return float(m.group()) if m else 0.0


def score_articles(articles: list[Article], cfg: dict, ai: AIClient) -> list[Article]:
    rel = cfg.get("relevance", {})
    use_llm = rel.get("use_llm_scoring", False) and ai.enabled
    for a in articles:
        text = f"{a.title} {a.raw_summary}"
        a.score = _keyword_score(text, rel)
        if use_llm:
            a.score += _llm_score(a, ai)
    return articles


def select_relevant(articles: list[Article], cfg: dict) -> list[Article]:
    rel = cfg.get("relevance", {})
    min_score = rel.get("min_score", 0)
    max_items = rel.get("max_items", 12)
    filtered = [a for a in articles if a.score >= min_score]
    filtered.sort(key=lambda x: (x.score, x.published), reverse=True)
    return filtered[:max_items]
