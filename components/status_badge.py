"""Small status badge helpers."""
from __future__ import annotations

from html import escape
import streamlit as st


def status_badge(label: str, status: str = "正常", tone: str = "ok") -> None:
    st.markdown(
        f'<span class="yz-mini-status yz-mini-status-{escape(tone)}">● {escape(label)}：{escape(status)}</span>',
        unsafe_allow_html=True,
    )


def status_badge_css() -> str:
    return """
    <style>
    .yz-mini-status {display:inline-block; border-radius:999px; padding:5px 9px; font-size:12px; font-weight:900; border:1px solid #e2e8f0; background:#fff; color:#334155; margin-right:6px;}
    .yz-mini-status-ok {color:#16a34a;}
    .yz-mini-status-warn {color:#f59e0b;}
    .yz-mini-status-bad {color:#dc2626;}
    </style>
    """
