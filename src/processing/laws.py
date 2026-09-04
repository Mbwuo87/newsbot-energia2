"""
Detección de leyes/proyectos en los textos y generación de:
  - un resumen IA por cada norma (página HTML en GitHub Pages)
  - reemplazo de la mención por un hipervínculo hacia esa página
"""
from __future__ import annotations
import re
import unicodedata

from src.models import LawRef
from src.processing.ai_client import AIClient


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:60] or "norma"


class LawRegistry:
    """Detecta normas, cachea sus resúmenes y arma los links."""

    def __init__(self, cfg: dict, ai: AIClient, pages_base_url: str):
        self.cfg = cfg.get("laws", {})
        self.ai = ai
        self.base_url = pages_base_url.rstrip("/")
        self.patterns = [re.compile(p) for p in self.cfg.get("patterns", [])]
        self.registry: dict[str, LawRef] = {}   # slug -> LawRef

    def _summarize_law(self, label: str) -> str:
        if self.ai.enabled:
            system = (
                "Sos un asesor legislativo. Explicá de forma breve y clara qué es la "
                "norma/proyecto mencionado, su objetivo, a quién afecta y su estado "
                "(si lo conocés). Español, 3-5 oraciones. Si no tenés certeza, aclaralo."
            )
            out = self.ai.complete(system, f"Norma: {label}", max_tokens=300)
            if out:
                return out
        return (
            f"Resumen automático no disponible para <b>{label}</b>. "
            "Configurá OPENAI_API_KEY para habilitar resúmenes con IA."
        )

    def process(self, text: str) -> str:
        """
        Reemplaza en 'text' cada mención de norma por un <a> hacia su página resumen.
        Registra las normas nuevas para generar sus páginas luego.
        Devuelve el texto con HTML.
        """
        if not self.cfg.get("enabled") or not text:
            return text

        def repl(match: re.Match) -> str:
            label = match.group(0).strip()
            slug = _slugify(label)
            if slug not in self.registry:
                ref = LawRef(label=label, slug=slug)
                ref.summary_html = self._summarize_law(label)
                ref.page_url = f"{self.base_url}/laws/{slug}.html"
                self.registry[slug] = ref
            url = self.registry[slug].page_url
            return (
                f'<a href="{url}" style="color:#0b5cad;text-decoration:underline;">'
                f'{label}</a>'
            )

        result = text
        for pat in self.patterns:
            result = pat.sub(repl, result)
        return result

    def all_refs(self) -> list[LawRef]:
        return list(self.registry.values())
