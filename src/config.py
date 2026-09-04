"""
Configuración central del robot de noticias.
Editá este archivo para agregar/sacar fuentes, canales de YouTube o cambiar los criterios.
"""

TIMEZONE = "America/Argentina/Buenos_Aires"

# --- Fuentes de noticias -----------------------------------------------
# Si "rss" es None, el bot intenta descubrirlo solo la primera vez que corre
# y guarda el resultado en data/state.json. Si sabés el feed exacto, ponelo
# vos directamente para ahorrar tiempo.
NEWS_SOURCES = [
    {"name": "EconoJournal", "url": "https://econojournal.com.ar", "rss": None, "priority": True},
    {"name": "Energía Estratégica", "url": "https://www.energiaestrategica.com/energiaestrategica/es", "rss": None, "priority": False},
    {"name": "Run Run Energético", "url": "https://runrunenergetico.com", "rss": None, "priority": False},
    {"name": "Vaca Muerta News", "url": "https://vacamuertanews.com", "rss": None, "priority": False},
    {"name": "Energy Intelligence", "url": "https://www.energyintel.com", "rss": None, "priority": False},
]

# --- Canales de YouTube --------------------------------------------------
YOUTUBE_CHANNELS = [
    {"name": "EconoJournal", "handle": "@EconoJournal"},
    {"name": "Joven Inversor", "handle": "@JovenInversor"},
    {"name": "Vaca Muerta News", "handle": "@vacamuertanewsarg"},
    {"name": "Ciudadano News", "handle": "@ciudadanonews"},
    {"name": "Todo Noticias", "handle": "@todonoticias"},
    {"name": "La Nación", "handle": "@lanacion"},
]

# --- Criterios de relevancia (se le pasan a la IA tal cual) --------------
RELEVANCE_CRITERIA = """
Priorizá noticias sobre:
- Energía (petróleo, gas, electricidad, renovables), con foco especial en Vaca Muerta y Argentina.
- Macroeconomía argentina relacionada al sector energético.
- Proyectos de generación de energía y energías renovables.
- Leyes, decretos o proyectos legislativos que modifiquen el marco energético argentino.
- Noticias internacionales relevantes del mercado energético mundial (geopolítica, OPEP, precios
  del crudo/gas, grandes acuerdos, fusiones) SOLO si tienen impacto real en el mercado o en Argentina.

Reglas de priorización:
1. Las noticias de Argentina van primero. Las internacionales solo si son realmente relevantes
   para el mercado energético global o argentino.
2. EconoJournal es la fuente más confiable del set: ante cobertura similar de un mismo hecho,
   preferí su versión y su nivel de detalle.
3. Cualquier noticia sobre una ley, decreto o proyecto legislativo energético es automáticamente
   relevante, sin importar la fuente.
4. Description muy genérica, notas de opinión sin datos nuevos, o contenido publicitario/sponsoreado
   NO son relevantes.
"""

# --- Envío de email -------------------------------------------------------
EMAIL_TO = "axelcwaik@gmail.com"
EMAIL_FROM = "axelcwaik@gmail.com"
EMAIL_SUBJECT_PREFIX = "Novedades de energía"

# --- Modelo de IA a usar ---------------------------------------------------
CLAUDE_MODEL = "claude-sonnet-4-6"

# --- Publicación del reporte web (GitHub Pages) ----------------------------
# Se completa automáticamente en el workflow de GitHub Actions con el nombre
# real del repo. No hace falta tocarlo a mano salvo que quieras forzarlo.
import os
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "")  # ej: https://usuario.github.io/newsbot
