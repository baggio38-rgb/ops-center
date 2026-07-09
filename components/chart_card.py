"""Chart/table card container helpers."""
from __future__ import annotations

from contextlib import contextmanager
import streamlit as st


@contextmanager
def chart_card(title: str = "", subtitle: str = ""):
    st.markdown('<div class="yz-chart-card-v6">', unsafe_allow_html=True)
    if title:
        st.markdown(f'<div class="yz-chart-card-title-v6">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="yz-chart-card-sub-v6">{subtitle}</div>', unsafe_allow_html=True)
    yield
    st.markdown('</div>', unsafe_allow_html=True)


def chart_card_css() -> str:
    return """
    <style>
    .yz-chart-card-v6 {border-radius:22px; border:1px solid rgba(226,232,240,.86); background:linear-gradient(180deg, rgba(255,255,255,.97), rgba(248,250,252,.95)); padding:18px 18px 16px 18px; box-shadow:0 12px 32px rgba(2,6,23,.15); margin-bottom:14px;}
    .yz-chart-card-title-v6 {font-size:16px; font-weight:950; color:#0f172a; margin-bottom:3px;}
    .yz-chart-card-sub-v6 {font-size:12px; font-weight:800; color:#64748b; margin-bottom:8px;}
    </style>
    """
