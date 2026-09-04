"""Estructuras de datos compartidas."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    title: str
    url: str
    source: str
    category: str
    published: datetime
    raw_summary: str = ""
    body: str = ""              # cuerpo completo (para resumir)
    summary: str = ""           # resumen final (IA o extractivo), puede tener HTML
    score: float = 0.0          # puntaje de relevancia


@dataclass
class Video:
    title: str
    url: str
    video_id: str
    channel: str
    published: datetime
    transcript: str = ""
    summary: str = ""


@dataclass
class LawRef:
    """Una ley/proyecto detectado que tendrá su propia página resumen."""
    label: str                  # texto tal como apareció, ej "Ley 27.401"
    slug: str                   # identificador para el archivo/URL
    summary_html: str = ""      # resumen generado por IA
    page_url: str = ""          # URL pública en GitHub Pages
