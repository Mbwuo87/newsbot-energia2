"""
Estado persistente entre corridas. Se guarda como JSON en data/state.json y
se commitea de vuelta al repo desde el workflow de GitHub Actions, así el
bot 'recuerda' qué noticias/videos ya procesó y qué feeds RSS descubrió.
"""
import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "state.json")


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {"seen_articles": [], "seen_videos": [], "discovered_rss": {}, "channel_ids": {}, "law_summaries": {}}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("seen_articles", [])
    data.setdefault("seen_videos", [])
    data.setdefault("discovered_rss", {})
    data.setdefault("channel_ids", {})
    data.setdefault("law_summaries", {})
    return data


def save_state(state: dict) -> None:
    # Evita que estas listas crezcan para siempre: nos quedamos con las
    # últimas 3000 entradas de cada una.
    state["seen_articles"] = state["seen_articles"][-3000:]
    state["seen_videos"] = state["seen_videos"][-1000:]
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
