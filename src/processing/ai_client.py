"""Cliente de IA unificado con degradación elegante si no hay API key."""
from __future__ import annotations
import os


class AIClient:
    def __init__(self, cfg: dict):
        self.cfg = cfg.get("ai", {})
        self.model = self.cfg.get("model", "gpt-4o-mini")
        self.enabled = bool(self.cfg.get("enabled")) and bool(os.getenv("OPENAI_API_KEY"))
        self._client = None
        if self.enabled:
            try:
                from openai import OpenAI
                base_url = os.getenv("OPENAI_BASE_URL")
                kwargs = {"api_key": os.getenv("OPENAI_API_KEY")}
                if base_url:
                    kwargs["base_url"] = base_url
                self._client = OpenAI(**kwargs)
            except Exception as e:
                print(f"[AI] No se pudo inicializar OpenAI: {e}")
                self.enabled = False

    def complete(self, system: str, user: str, max_tokens: int = 400) -> str:
        """Devuelve texto del modelo, o '' si la IA no está disponible/falla."""
        if not self.enabled or not self._client:
            return ""
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"[AI] Error en completion: {e}")
            return ""
