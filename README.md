# Robot de noticias de energía

Todos los días a las **8:00 am (hora Argentina)**, incluidos fines de semana, este robot:

1. Revisa tus 5 fuentes de noticias y tus 6 canales de YouTube.
2. Toma solo lo publicado el día anterior.
3. Usa IA (Claude) para decidir qué es relevante, resumir cada nota/video, y detectar leyes o
   proyectos legislativos mencionados.
4. Publica un reporte web con acordeones (clickeás y se despliega el resumen) y links a los
   resúmenes de cada ley/proyecto.
5. Te manda un email a **axelcwaik@gmail.com** con las dos listas pedidas, cada ítem linkeado
   directo al punto correspondiente del reporte.

Corre solo, gratis, en la nube (GitHub Actions + GitHub Pages). No necesitás dejar ninguna PC
prendida ni tocar código en el día a día.

---

## Puesta en marcha (una sola vez)

### 1. Crear una cuenta de GitHub (si no tenés)
Andá a [github.com](https://github.com) y registrate. Es gratis.

### 2. Crear el repositorio
- Botón verde **"New"** → nombre, por ejemplo `newsbot-energia` → dejalo **público**
  (así los "Actions minutes" son ilimitados y gratis; el contenido de las noticias no es
  información sensible) → **Create repository**.

### 3. Subir estos archivos
En la página del repo recién creado: **Add file → Upload files**, arrastrá **toda** la carpeta
`newsbot` que te compartí (o su contenido) y confirmá el commit. Tiene que quedar la carpeta
`.github/workflows/`, `src/`, `data/`, `docs/`, `requirements.txt` y este `README.md` en la raíz
del repo.

### 4. Activar GitHub Pages (para el reporte web)
- **Settings** (del repo) → **Pages** (en el menú de la izquierda).
- En "Source" elegí **Deploy from a branch**.
- Branch: **main**, carpeta: **/docs** → **Save**.
- GitHub te va a dar una URL tipo `https://tu-usuario.github.io/newsbot-energia/`. Ahí se van a
  publicar los reportes diarios.

### 5. Crear tu API key de Anthropic (para que funcione la IA)
- Andá a [console.anthropic.com](https://console.anthropic.com) → creá una cuenta si no tenés →
  **API Keys** → **Create Key** → copiala (empieza con `sk-ant-...`).
- Esto tiene un costo de uso (no es parte de tu suscripción a Claude.ai), pero para este volumen
  diario de notas es de centavos de dólar por día. Podés poner un límite de gasto mensual en
  **Settings → Limits** de la consola.

### 6. Crear una "contraseña de aplicación" de Gmail (para que pueda enviar el mail)
Gmail no permite usar tu contraseña normal para esto por seguridad. Necesitás:
1. Activar la verificación en 2 pasos en tu cuenta de Google, si no la tenés:
   [myaccount.google.com/security](https://myaccount.google.com/security).
2. Ir a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Crear una nueva "contraseña de aplicación" (ponele de nombre, por ejemplo, "newsbot").
4. Copiá el código de 16 letras que te da (sin espacios).

### 7. Cargar los "Secrets" en GitHub (tus credenciales, de forma segura)
En el repo: **Settings → Secrets and variables → Actions → New repository secret**. Creá estos
tres, uno por uno:

| Nombre | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | la key que copiaste en el paso 5 |
| `GMAIL_ADDRESS` | `axelcwaik@gmail.com` |
| `GMAIL_APP_PASSWORD` | el código de 16 letras del paso 6 |

### 8. Probarlo manualmente (antes de esperar hasta mañana)
- Pestaña **Actions** del repo → click en **"Reporte diario de energía"** (en la lista de la
  izquierda) → botón **"Run workflow"** → **Run workflow** de nuevo para confirmar.
- Esperá 2-5 minutos y refrescá. Si el círculo queda verde ✅, salió todo bien y te debería haber
  llegado el mail. Si queda rojo ❌, entrá y mirá el log para ver en qué paso falló (a veces es
  simplemente que algún sitio bloqueó el scraping ese día; contame y lo ajustamos).

Después de esto, **no tenés que hacer nada más**: corre solo todos los días a las 8am.

---

## Cómo tocar la configuración más adelante

Todo lo que vas a querer cambiar está en **`src/config.py`**:
- Agregar/sacar fuentes de noticias (`NEWS_SOURCES`).
- Agregar/sacar canales de YouTube (`YOUTUBE_CHANNELS`).
- Ajustar los criterios de relevancia (`RELEVANCE_CRITERIA`), en español, como una instrucción a la IA.
- Cambiar el mail de destino (`EMAIL_TO`).

Después de editar, solo hace falta subir el archivo actualizado a GitHub (o hacer `git push` si
usás git); el próximo run ya usa la nueva configuración. El horario (8am) se cambia en
`.github/workflows/daily.yml`, en la línea del `cron` (está en UTC).

## Limitaciones a tener en cuenta

- **Scraping sin RSS**: el bot detecta artículos automáticamente en sitios sin RSS, pero no es
  100% infalible como un feed RSS real. Si notás que a algún sitio le faltan notas, avisame:
  le hago un lector a medida para ese sitio puntual.
- **Transcripciones de YouTube**: si un video no tiene subtítulos (ni automáticos) disponibles,
  no se puede generar su resumen; el bot lo salta y lo indica en el log.
- **Costo de la API de Anthropic**: se cobra por uso (no está incluido en una suscripción de
  Claude.ai). Con el volumen de este bot, el gasto mensual debería ser bajo, pero es bueno
  chequearlo los primeros días en la consola de Anthropic.
