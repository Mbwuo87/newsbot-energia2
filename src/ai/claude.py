"""
Todas las llamadas a la API de Anthropic (Claude) viven acá.
Requiere la variable de entorno ANTHROPIC_API_KEY.
"""
import json
import os
import re

import anthropic

from src.config import CLAUDE_MODEL, RELEVANCE_CRITERIA

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _ask_json(prompt: str, max_tokens: int = 1000) -> dict:
    """Le pide a Claude que responda SOLO con JSON y lo parsea, con un
    fallback tolerante por si viene con texto de más alrededor."""
    resp = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    text = text.strip()
    # Por si Claude devuelve el JSON envuelto en ```json ... ```
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def analyze_article(source_name: str, is_priority_source: bool, title: str, text: str) -> dict:
    """Devuelve:
    {
      "relevant": bool,
      "one_liner": "...",          # resumen en 1 renglón para la lista
      "full_summary": "...",       # resumen más completo, 2-4 frases
      "laws_mentioned": ["nombre de ley/proyecto 1", ...]
    }
    """
    prompt = f"""Sos un editor de un newsletter diario especializado en energía y economía argentina.

CRITERIOS DE RELEVANCIA:
{RELEVANCE_CRITERIA}

Fuente: {source_name} {"(fuente prioritaria/muy confiable)" if is_priority_source else ""}
Título: {title}
Texto de la nota (puede estar truncado):
\"\"\"{text[:6000]}\"\"\"

Analizá la nota y respondé ÚNICAMENTE con un objeto JSON (sin texto adicional, sin backticks) con este formato exacto:
{{
  "relevant": true o false,
  "one_liner": "resumen del asunto en una sola línea corta, concreto y en español neutro rioplatense",
  "full_summary": "resumen de 2 a 4 frases con lo más importante de la nota",
  "laws_mentioned": ["nombres de leyes, decretos o proyectos legislativos mencionados explícitamente en la nota, si hay alguno; lista vacía si no hay ninguno"]
}}
"""
    try:
        return _ask_json(prompt)
    except Exception:
        return {"relevant": False, "one_liner": title, "full_summary": "", "laws_mentioned": []}


def analyze_video(channel_name: str, title: str, transcript: str) -> dict:
    """Devuelve {"one_liner": "...", "full_summary": "..."}"""
    prompt = f"""Sos un editor de un newsletter diario especializado en energía y economía argentina.

Canal: {channel_name}
Título del video: {title}
Transcripción del video (puede estar truncada):
\"\"\"{transcript[:8000]}\"\"\"

Respondé ÚNICAMENTE con un objeto JSON (sin texto adicional, sin backticks) con este formato exacto:
{{
  "one_liner": "resumen del contenido del video en una sola línea corta",
  "full_summary": "resumen de 3 a 6 frases con los puntos más importantes que se dicen en el video"
}}
"""
    try:
        return _ask_json(prompt, max_tokens=800)
    except Exception:
        return {"one_liner": title, "full_summary": ""}


def summarize_law(law_name: str, context_snippet: str) -> str:
    """Genera un resumen corto y claro de una ley/proyecto mencionado en una noticia."""
    prompt = f"""Te doy el nombre de una ley, decreto o proyecto legislativo argentino y un fragmento de
una noticia donde se lo menciona. Escribí un resumen breve (4 a 8 frases) explicando de qué se trata,
qué cambia o busca cambiar, y su estado actual (proyecto, sancionada, vigente, etc.) según lo que
se pueda inferir del contexto. Si el contexto no alcanza para saber algo con certeza, decilo en vez
de inventarlo.

Nombre: {law_name}
Contexto: \"\"\"{context_snippet[:3000]}\"\"\"

Respondé solo con el texto del resumen, sin JSON ni encabezados.
"""
    resp = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in resp.content if block.type == "text").strip()
