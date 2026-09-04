# 📰 News Bot — Digest semanal automático con GitHub Actions

Robot que **todos los lunes a las 08:00 (hora Argentina)** te envía por email las
novedades de los últimos 7 días. Combina **RSS**, **web scraping** y
**transcripciones de YouTube**, resume todo con **IA**, y convierte cada ley o
proyecto mencionado en un **hipervínculo a un resumen generado por IA**.

No necesitás servidor: corre gratis en GitHub Actions.

---

## ✨ Qué hace

- **Parte 1 — Noticias relevantes:** lista de asuntos resumidos en 1 renglón.
  Al hacer clic en un ítem se **despliega** el resumen completo (`<details>`).
- **Parte 2 — Videos de YouTube:** lista con título/resumen; al clic se despliega
  el resumen de la transcripción.
- **Hipervínculos de leyes:** cada mención (ej. `Ley 27.401`, `DNU 70/2023`) linkea
  a una página propia con un resumen IA, publicada en GitHub Pages.
- **Versión web** de cada edición (por si tu cliente de correo no soporta el
  desplegable nativo — ver nota más abajo).

---

## 🚀 Puesta en marcha (10 minutos)

### 1. Subí el repo a GitHub
Creá un repo (ej. `news-bot`) y subí estos archivos.

### 2. Configurá tus fuentes
Editá **`config/sources.yaml`**:
- **RSS:** pegá la URL del feed. (Lo más simple y confiable.)
- **Scraping:** para páginas sin RSS, definí los selectores CSS
  (`item_selector`, `title_selector`, `link_selector`). Poné `enabled: true`.
- **YouTube:** conseguí el `channel_id` (empieza con `UC...`) y poné `enabled: true`.

Ajustá los **criterios de relevancia** en **`config/settings.yaml`**
(palabras clave que suman/restan puntaje, umbral mínimo, máximo de noticias).

### 3. Configurá los secrets
En **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Descripción |
|---|---|
| `SMTP_HOST` | ej. `smtp.gmail.com` |
| `SMTP_PORT` | ej. `587` |
| `SMTP_USER` | tu email (ej. `tucorreo@gmail.com`) |
| `SMTP_PASS` | **App Password** de Gmail (no tu clave normal) |
| `MAIL_TO` | destino(s), separados por coma |
| `OPENAI_API_KEY` | *(opcional)* para resúmenes IA. Sin esto usa modo extractivo. |
| `OPENAI_BASE_URL` | *(opcional)* si usás Azure/OpenRouter |

> **Gmail App Password:** activá verificación en 2 pasos y generá una clave en
> https://myaccount.google.com/apppasswords

En **Settings → Secrets and variables → Actions → Variables** agregá:

| Variable | Valor |
|---|---|
| `PAGES_BASE_URL` | `https://TU_USUARIO.github.io/news-bot` |

### 4. Activá GitHub Pages
**Settings → Pages → Source: Deploy from a branch → Branch: `main` / carpeta `/docs`.**
Ahí se publican las páginas de leyes y la versión web del digest.

### 5. Probalo sin esperar al lunes
**Actions → Weekly News Digest → Run workflow.** Poné `dry_run = true` para
generar un **preview** sin enviar email (se sube como *artifact* `email-preview`).
Cuando estés conforme, corrélo con `dry_run = false`.

---

## ⏰ El horario

El cron está en UTC. Argentina es UTC-3 todo el año (no hay horario de verano):

```yaml
schedule:
  - cron: "0 11 * * 1"   # 11:00 UTC = 08:00 ART, todos los lunes
```

> GitHub puede demorar algunos minutos el disparo de crons en horarios pico; es normal.

---

## ⚠️ Nota importante sobre el desplegable en el email

El efecto "clic para desplegar" usa la etiqueta HTML `<details>`. Funciona nativo en
**Apple Mail** y varios clientes, pero **Gmail web la ignora** y muestra el contenido
expandido. Por eso el email incluye siempre un link **"Ver en el navegador"** a la
versión en GitHub Pages, donde el desplegable funciona perfecto en cualquier lado.

---

## 🧪 Correr localmente

```bash
pip install -r requirements.txt
python -m src.main --dry-run      # genera preview.html sin enviar
```

---

## 🗂️ Estructura

```
├── .github/workflows/weekly-digest.yml   # cron + pipeline
├── config/
│   ├── sources.yaml      # TUS fuentes (RSS, scraping, YouTube)
│   └── settings.yaml     # relevancia, IA, patrones de leyes
├── src/
│   ├── collectors/       # rss.py, scraper.py, youtube.py
│   ├── processing/       # relevance.py, summarize.py, laws.py, ai_client.py
│   ├── render/           # plantillas HTML + render.py
│   ├── publish/          # pages.py (GitHub Pages)
│   ├── notify/           # email_sender.py (SMTP)
│   └── main.py           # orquestador
└── docs/                 # salida publicada (GitHub Pages)
```

---

## 🔧 Cómo ajustar la relevancia

En `config/settings.yaml`, sección `relevance`:
- Sumá términos a `keywords_high/medium/low` (con su peso).
- Usá `keywords_negative` para filtrar ruido (horóscopo, farándula, etc.).
- Subí/bajá `min_score` para ser más/menos estricto.
- Con `use_llm_scoring: true` la IA además puntúa 0-5 cada noticia.
