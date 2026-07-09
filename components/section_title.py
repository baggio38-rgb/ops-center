"""Unified section titles."""
from __future__ import annotations

from html import escape
import streamlit as st


def section_title(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="yz-section-v6">
          <div class="yz-section-title-v6">{escape(title)}</div>
          {f'<div class="yz-section-sub-v6">{escape(subtitle)}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title_css() -> str:
    return """
    <style>
    .yz-section-v6 {margin: 23px 0 12px 0;}
    .yz-section-title-v6 {font-size:22px; line-height:1.2; color:#f8fafc; font-weight:950; letter-spacing:-.2px;}
    .yz-section-title-v6:before {content:""; display:inline-block; width:8px; height:22px; border-radius:999px; background:linear-gradient(180deg,#60a5fa,#0ea5e9); margin-right:9px; vertical-align:-4px;}
    .yz-section-sub-v6 {font-size:13px; color:#94a3b8; font-weight:800; margin-top:5px;}
    </style>
    """
