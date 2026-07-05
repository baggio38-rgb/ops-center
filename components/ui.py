"""博彩智能决策平台共用UI组件。"""

from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st


CSS = """
<style>
.block-container {padding-top: 1.15rem; padding-bottom: 2rem; max-width: 1480px;}
div[data-testid="stHorizontalBlock"] {gap: .85rem;}
.gip-hero {
  border: 1px solid #e5e7eb;
  border-radius: 22px;
  padding: 22px 24px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 52%, #334155 100%);
  color: white;
  box-shadow: 0 12px 32px rgba(15, 23, 42, .18);
  margin-bottom: 18px;
}
.gip-hero h1 {margin: 0 0 6px 0; font-size: 30px; font-weight: 900; letter-spacing: .3px;}
.gip-hero p {margin: 0; color: #cbd5e1; font-size: 14px;}
.gip-card {
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 17px 18px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(15, 23, 42, .06);
  min-height: 118px;
}
.gip-card-title {font-size: 13px; color: #64748b; margin-bottom: 9px; display:flex; align-items:center; gap:6px;}
.gip-card-value {font-size: 29px; font-weight: 900; color: #0f172a; line-height: 1.1;}
.gip-card-note {font-size: 12px; color: #64748b; margin-top: 9px;}
.gip-delta-up {color:#16a34a; font-weight:800;}
.gip-delta-down {color:#dc2626; font-weight:800;}
.gip-delta-flat {color:#64748b; font-weight:800;}
.gip-section-title {margin-top: 18px; margin-bottom: 8px; font-size: 22px; font-weight: 900; color:#e6f0ff;}
.gip-section-subtitle {margin-top: -4px; margin-bottom: 13px; color:#a8b3c7; font-size: 13px;}
.gip-alert {
  border-radius: 14px;
  padding: 12px 14px;
  margin-bottom: 9px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111827;
  font-weight: 700;
  box-shadow: 0 1px 8px rgba(15, 23, 42, .08);
}
.gip-alert span, .gip-alert div, .gip-alert p {color:#111827 !important;}
.gip-quick-card {
  border-radius: 14px;
  padding: 16px 18px;
  min-height: 116px;
  color: #e6f0ff;
  border: 1px solid rgba(226, 232, 240, .18);
  box-shadow: 0 6px 20px rgba(0,0,0,.12);
}
.gip-quick-card h4 {margin:0 0 10px 0; color:#ffffff; font-size:16px; font-weight:900;}
.gip-quick-card p {margin:0; color:#e6f0ff; line-height:1.65; font-size:14px;}
.gip-quick-green {background: linear-gradient(135deg, #065f46 0%, #166534 100%);}
.gip-quick-yellow {background: linear-gradient(135deg, #713f12 0%, #854d0e 100%);}
.gip-quick-blue {background: linear-gradient(135deg, #0f3b66 0%, #1e3a8a 100%);}
.gip-quick-gray {background: linear-gradient(135deg, #1f2937 0%, #374151 100%);}
.gip-alert-critical {border-left: 5px solid #dc2626;}
.gip-alert-warning {border-left: 5px solid #f59e0b;}
.gip-alert-good {border-left: 5px solid #16a34a;}
.gip-brief {
  border-radius: 18px;
  padding: 18px 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  line-height: 1.75;
  color:#0f172a;
}
.gip-score {
  font-size: 42px;
  line-height: 1;
  font-weight: 950;
  color:#0f172a;
}
.gip-pill {
  display:inline-block;
  border-radius:999px;
  padding:4px 10px;
  background:#f1f5f9;
  color:#334155;
  font-size:12px;
  font-weight:700;
  margin-right: 6px;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, version: str = "v1.3.0") -> None:
    st.markdown(
        f"""
        <div class="gip-hero">
          <h1>{escape(title)} <span style="font-size:14px;background:#e2e8f0;color:#0f172a;border-radius:999px;padding:4px 9px;vertical-align:middle;">{escape(version)}</span></h1>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="gip-section-title">{escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="gip-section-subtitle">{escape(subtitle)}</div>', unsafe_allow_html=True)


def metric_card(title: str, value: str, note: str = "", delta: Any = None, icon: str = "") -> None:
    delta_html = ""
    if delta is not None and not (isinstance(delta, float) and pd.isna(delta)):
        try:
            d = float(delta)
            cls = "gip-delta-up" if d >= 0 else "gip-delta-down"
            arrow = "▲" if d >= 0 else "▼"
            delta_html = f'<span class="{cls}">{arrow} {abs(d) * 100:.2f}%</span>'
        except Exception:
            delta_html = f'<span class="gip-delta-flat">{escape(str(delta))}</span>'
    st.markdown(
        f"""
        <div class="gip-card">
          <div class="gip-card-title"><span>{escape(icon)}</span><span>{escape(title)}</span></div>
          <div class="gip-card-value">{escape(str(value))}</div>
          <div class="gip-card-note">{delta_html} {escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def alert(text: str, level: str = "warning") -> None:
    cls = {
        "critical": "gip-alert-critical",
        "warning": "gip-alert-warning",
        "good": "gip-alert-good",
    }.get(level, "gip-alert-warning")
    st.markdown(f'<div class="gip-alert {cls}">{escape(text)}</div>', unsafe_allow_html=True)


def brief(lines: list[str]) -> None:
    body = "<br>".join(escape(line) for line in lines if line)
    st.markdown(f'<div class="gip-brief">{body}</div>', unsafe_allow_html=True)


def score_card(title: str, score: int, note: str = "") -> None:
    score = max(0, min(int(score), 100))
    if score >= 85:
        label = "优秀"
        color = "#16a34a"
    elif score >= 70:
        label = "稳定"
        color = "#2563eb"
    elif score >= 55:
        label = "观察"
        color = "#f59e0b"
    else:
        label = "风险"
        color = "#dc2626"
    st.markdown(
        f"""
        <div class="gip-card">
          <div class="gip-card-title">{escape(title)}</div>
          <div class="gip-score" style="color:{color};">{score}</div>
          <div class="gip-card-note"><span class="gip-pill">{label}</span>{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
