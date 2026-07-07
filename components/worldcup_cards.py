"""世界杯专区专用卡片组件。"""

from __future__ import annotations

from html import escape

import streamlit as st


def apply_worldcup_v2_style() -> None:
    st.markdown(
        """
        <style>
        .wc-v2-hero {
          border: 1px solid rgba(250, 204, 21, .35);
          border-radius: 26px;
          padding: 24px 26px;
          margin-bottom: 18px;
          background:
            radial-gradient(circle at 12% 10%, rgba(250, 204, 21, .18), transparent 34%),
            radial-gradient(circle at 88% 20%, rgba(34, 197, 94, .15), transparent 30%),
            linear-gradient(135deg, rgba(5, 46, 22, .98), rgba(6, 78, 59, .92));
          box-shadow: 0 18px 44px rgba(0,0,0,.28);
        }
        .wc-v2-title {font-size:30px; font-weight:950; color:#fff7ed; margin:0 0 6px 0;}
        .wc-v2-subtitle {font-size:13px; color:#d9f99d; font-weight:800; margin:0;}
        .wc-v2-badge {display:inline-block; margin-left:10px; padding:4px 10px; border-radius:999px; background:rgba(250,204,21,.14); border:1px solid rgba(250,204,21,.38); color:#fde68a; font-size:12px; font-weight:950;}
        .wc-v2-card {
          min-height:120px;
          border:1px solid rgba(250,204,21,.22);
          border-radius:20px;
          padding:18px 18px;
          background:linear-gradient(180deg, rgba(15, 23, 42, .92), rgba(6, 78, 59, .86));
          box-shadow:0 12px 28px rgba(0,0,0,.24);
        }
        .wc-v2-card-title {font-size:13px; color:#bbf7d0; font-weight:900; margin-bottom:10px;}
        .wc-v2-card-value {font-size:30px; color:#fde68a; font-weight:950; line-height:1.1;}
        .wc-v2-card-note {font-size:12px; color:#d1fae5; font-weight:750; margin-top:10px;}
        .wc-v2-section {font-size:22px; font-weight:950; color:#f8fafc; margin:24px 0 8px 0;}
        .wc-v2-section:before {content:""; display:inline-block; width:8px; height:22px; border-radius:999px; background:linear-gradient(180deg,#fde68a,#22c55e); margin-right:10px; vertical-align:-4px;}
        .wc-v2-muted {font-size:13px; color:#94a3b8; font-weight:750; margin-bottom:14px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, version: str = "V2 Enterprise") -> None:
    st.markdown(
        f"""
        <div class="wc-v2-hero">
          <div class="wc-v2-title">{escape(title)}<span class="wc-v2-badge">{escape(version)}</span></div>
          <p class="wc-v2-subtitle">{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(title: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="wc-v2-card">
          <div class="wc-v2-card-title">{escape(title)}</div>
          <div class="wc-v2-card-value">{escape(str(value))}</div>
          <div class="wc-v2-card-note">{escape(str(note))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="wc-v2-section">{escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="wc-v2-muted">{escape(subtitle)}</div>', unsafe_allow_html=True)
