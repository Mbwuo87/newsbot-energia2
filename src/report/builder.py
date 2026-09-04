"""
Arma dos cosas:
1. report_page(): la página HTML completa que se publica en GitHub Pages,
   con acordeones reales (<details>) y links a los resúmenes de leyes.
2. email_html(): el HTML liviano que se manda por mail, con las dos listas
   pedidas y links hacia la página del punto 1.
"""
import re


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9áéíóúñ\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text[:80]


def _law_anchor(law_name: str) -> str:
    return "ley-" + _slugify(law_name)


def build_report_page(date_str: str, news_items: list[dict], video_items: list[dict], laws: dict) -> str:
    """
    news_items: [{"source", "title", "url", "one_liner", "full_summary", "laws_mentioned"}]
    video_items: [{"channel", "title", "url", "one_liner", "full_summary"}]
    laws: {law_name: summary_text}
    """

    def linkify_laws(text: str, laws_mentioned: list[str]) -> str:
        for law in laws_mentioned:
            if law in laws:
                anchor = _law_anchor(law)
                text = text.replace(
                    law,
                    f'<a href="#{anchor}" class="law-link">{law}</a>',
                    1,
                )
        return text

    news_blocks = []
    for idx, item in enumerate(news_items):
        summary_linked = linkify_laws(item["full_summary"], item.get("laws_mentioned", []))
        news_blocks.append(f"""
        <details class="item" id="news-{idx}">
          <summary>{item['one_liner']} <span class="source">— {item['source']}</span></summary>
          <div class="item-body">
            <p>{summary_linked}</p>
            <a class="original-link" href="{item['url']}" target="_blank" rel="noopener">Ver nota original →</a>
          </div>
        </details>""")

    video_blocks = []
    for idx, item in enumerate(video_items):
        video_blocks.append(f"""
        <details class="item" id="video-{idx}">
          <summary>{item['one_liner']} <span class="source">— {item['channel']}</span></summary>
          <div class="item-body">
            <p>{item['full_summary']}</p>
            <a class="original-link" href="{item['url']}" target="_blank" rel="noopener">Ver video →</a>
          </div>
        </details>""")

    law_blocks = []
    for law_name, summary in laws.items():
        anchor = _law_anchor(law_name)
        law_blocks.append(f"""
        <div class="law" id="{anchor}">
          <h3>{law_name}</h3>
          <p>{summary}</p>
        </div>""")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Novedades de energía — {date_str}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; max-width: 780px;
          margin: 0 auto; padding: 24px; color: #1a1a1a; background: #fafafa; }}
  h1 {{ font-size: 22px; }}
  h2 {{ font-size: 18px; margin-top: 36px; border-bottom: 2px solid #ddd; padding-bottom: 6px; }}
  .item {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 10px;
           padding: 10px 14px; }}
  .item summary {{ cursor: pointer; font-weight: 600; }}
  .item .source {{ font-weight: 400; color: #777; font-size: 0.9em; }}
  .item-body {{ margin-top: 10px; line-height: 1.5; }}
  .original-link {{ font-size: 0.9em; }}
  .law-link {{ color: #b5651d; font-weight: 600; text-decoration: underline; }}
  .law {{ background: #fff8ec; border-left: 4px solid #b5651d; padding: 10px 14px; margin-bottom: 14px;
          border-radius: 4px; scroll-margin-top: 20px; }}
  .law h3 {{ margin: 0 0 6px 0; }}
</style>
</head>
<body>
<h1>Novedades de energía — {date_str}</h1>

<h2>📰 Noticias relevantes</h2>
{''.join(news_blocks) if news_blocks else '<p>No hubo noticias relevantes ayer.</p>'}

<h2>🎥 Videos de YouTube</h2>
{''.join(video_blocks) if video_blocks else '<p>No hubo videos nuevos ayer.</p>'}

{'<h2>⚖️ Leyes y proyectos mencionados</h2>' + ''.join(law_blocks) if law_blocks else ''}

<script>
  // Si se entra con un #ancla, abrir el <details> correspondiente si aplica
  window.addEventListener('DOMContentLoaded', () => {{
    if (location.hash) {{
      const el = document.querySelector(location.hash);
      if (el && el.tagName === 'DETAILS') el.open = true;
    }}
  }});
</script>
</body>
</html>"""
    return html


def build_email_html(date_str: str, news_items: list[dict], video_items: list[dict], report_url: str) -> str:
    def news_row(idx, item):
        return f'<li><a href="{report_url}#news-{idx}" style="color:#1a1a1a; text-decoration:none;">' \
               f'<strong>{item["one_liner"]}</strong></a> <span style="color:#888;">— {item["source"]}</span></li>'

    def video_row(idx, item):
        return f'<li><a href="{report_url}#video-{idx}" style="color:#1a1a1a; text-decoration:none;">' \
               f'<strong>{item["one_liner"]}</strong></a> <span style="color:#888;">— {item["channel"]}</span></li>'

    news_list = "".join(news_row(i, it) for i, it in enumerate(news_items)) or "<li>No hubo noticias relevantes ayer.</li>"
    video_list = "".join(video_row(i, it) for i, it in enumerate(video_items)) or "<li>No hubo videos nuevos ayer.</li>"

    return f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; color:#1a1a1a; max-width:640px; margin:0 auto;">
  <h2>Novedades de energía — {date_str}</h2>
  <p>Tocá cualquier ítem para ver el resumen completo y las leyes/proyectos con su análisis.</p>

  <h3>📰 Noticias relevantes</h3>
  <ul style="padding-left:20px; line-height:1.7;">{news_list}</ul>

  <h3>🎥 Videos de YouTube</h3>
  <ul style="padding-left:20px; line-height:1.7;">{video_list}</ul>

  <p style="margin-top:24px;">
    <a href="{report_url}" style="background:#b5651d;color:white;padding:10px 16px;border-radius:6px;text-decoration:none;">
      Ver el reporte completo →
    </a>
  </p>
</body>
</html>"""
