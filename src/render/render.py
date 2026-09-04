"""Renderiza el email HTML y las páginas de leyes usando Jinja2."""
from __future__ import annotations
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TPL_DIR = os.path.dirname(__file__)
_env = Environment(
    loader=FileSystemLoader(_TPL_DIR),
    autoescape=select_autoescape(["html"]),
)


def render_email(context: dict) -> str:
    return _env.get_template("email_template.html").render(**context)


def render_law_page(label: str, summary_html: str) -> str:
    return _env.get_template("law_template.html").render(
        label=label,
        summary_html=summary_html,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
