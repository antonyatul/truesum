"""Shared UI primitives. Read-only HTML pieces only; inputs use native widgets."""
from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit as st

from truesum.ui.theme import full_css

LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "logo.png"

TIER_GLYPH = {"High": "▲", "Medium": "●", "Low": "▼"}


def inject_theme() -> None:
    st.markdown(f"<style>{full_css()}</style>", unsafe_allow_html=True)


@lru_cache(maxsize=1)
def _logo_data_uri() -> str | None:
    if not LOGO_PATH.exists():
        return None
    return "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()


def hero(title: str, subtitle: str) -> None:
    logo = _logo_data_uri()
    img = f'<img src="{logo}" alt="">' if logo else ""
    st.markdown(
        f'<div class="sl-hero">{img}<div><h1>{html.escape(title)}</h1>'
        f"<p>{html.escape(subtitle)}</p></div></div>",
        unsafe_allow_html=True,
    )


def metric(label: str, value: str, hint: str | None = None) -> None:
    hint_html = f'<div class="hint">{html.escape(hint)}</div>' if hint else ""
    st.markdown(
        f'<div class="sl-metric"><div class="label">{html.escape(label)}</div>'
        f'<div class="value">{html.escape(value)}</div>{hint_html}</div>',
        unsafe_allow_html=True,
    )


def tier_badge(tier: str) -> str:
    """HTML for a tier badge; colour is always paired with a word and a glyph."""
    cls = tier.lower()
    return f'<span class="sl-badge {cls}">{TIER_GLYPH.get(tier, "")} {html.escape(tier)}</span>'


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f'<div class="sl-empty"><h3>{html.escape(title)}</h3><p>{html.escape(body)}</p></div>',
        unsafe_allow_html=True,
    )


def step_list(entries: list[tuple[str, str]]) -> None:
    """entries: (message, meta) pairs."""
    if not entries:
        empty_state("No cleaning steps yet", "Run a clean on the Overview page and each step is recorded here.")
        return
    items = "".join(
        f'<li>{html.escape(msg)}<span class="meta">{html.escape(meta)}</span></li>' for msg, meta in entries
    )
    st.markdown(f'<ol class="sl-steps">{items}</ol>', unsafe_allow_html=True)
