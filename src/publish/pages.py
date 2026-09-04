"""Escribe las páginas HTML en docs/ para que GitHub Pages las sirva."""
from __future__ import annotations
import os

from src.models import LawRef
from src.render.render import render_law_page

DOCS_DIR = "docs"
LAWS_DIR = os.path.join(DOCS_DIR, "laws")


def write_law_pages(refs: list[LawRef]) -> None:
    os.makedirs(LAWS_DIR, exist_ok=True)
    for ref in refs:
        html = render_law_page(ref.label, ref.summary_html)
        path = os.path.join(LAWS_DIR, f"{ref.slug}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
    print(f"[Pages] {len(refs)} páginas de leyes escritas en {LAWS_DIR}/")


def write_webview(email_html: str) -> str:
    """Guarda la edición actual como index.html navegable. Devuelve la ruta."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    path = os.path.join(DOCS_DIR, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(email_html)
    return path
