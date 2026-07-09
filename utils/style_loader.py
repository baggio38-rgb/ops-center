"""Central CSS loader for YEIP.

All page/component CSS should live in assets/css/main.css.
Do not print CSS strings with st.write/st.code.
"""
from __future__ import annotations

from pathlib import Path
import streamlit as st


@st.cache_data(show_spinner=False)
def _read_css(path: str) -> str:
    root = Path(__file__).resolve().parent.parent
    candidates = [root / path, Path(path)]
    for css_path in candidates:
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
    return ""


def load_css(path: str = "assets/css/main.css") -> None:
    css = _read_css(path)
    if not css:
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
