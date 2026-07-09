"""V6 common KPI card components for YEIP."""
from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st


def _is_missing(value: Any) -> bool:
    try:
        return value is None or pd.isna(value)
    except Exception:
        return value is None


def fmt_compact_number(value: Any, digits: int = 2) -> str:
    if _is_missing(value):
        return "-"
    try:
        n = float(value)
    except Exception:
        return str(value)
    sign = "-" if n < 0 else ""
    a = abs(n)
    if a >= 100000000:
        return f"{sign}{a / 100000000:,.{digits}f}亿"
    if a >= 10000:
        return f"{sign}{a / 10000:,.{digits}f}万"
    if a >= 1000:
        return f"{n:,.0f}"
    if float(n).is_integer():
        return f"{n:,.0f}"
    return f"{n:,.{digits}f}"


def fmt_percent(value: Any, digits: int = 2) -> str:
    if _is_missing(value):
        return "-"
    try:
        n = float(value)
    except Exception:
        return "-"
    if abs(n) <= 1:
        n *= 100
    return f"{n:,.{digits}f}%"


def kpi_card(
    title: str,
    value: Any,
    *,
    icon: str = "📊",
    delta: Any = None,
    note: str = "较昨日",
    value_type: str = "number",
    positive_good: bool = True,
) -> None:
    """Render a unified V6 KPI card.

    value_type: number | percent | raw
    positive_good: False for metrics where下降/负数 is preferred.
    """
    if value_type == "percent":
        value_text = fmt_percent(value)
    elif value_type == "raw":
        value_text = "-" if _is_missing(value) else str(value)
    else:
        value_text = fmt_compact_number(value)

    delta_text = "-"
    delta_class = "yz-kpi-delta-flat"
    arrow = "—"
    if not _is_missing(delta):
        try:
            d = float(delta)
            delta_text = fmt_percent(d)
            if d > 0:
                arrow = "▲"
                delta_class = "yz-kpi-delta-up" if positive_good else "yz-kpi-delta-down"
            elif d < 0:
                arrow = "▼"
                delta_class = "yz-kpi-delta-down" if positive_good else "yz-kpi-delta-up"
        except Exception:
            delta_text = str(delta)

    st.markdown(
        f"""
        <div class="yz-kpi-card-v6">
          <div class="yz-kpi-topline">
            <div class="yz-kpi-icon">{escape(icon)}</div>
            <div class="yz-kpi-title">{escape(title)}</div>
          </div>
          <div class="yz-kpi-value">{escape(value_text)}</div>
          <div class="yz-kpi-delta {delta_class}">{escape(arrow)} {escape(delta_text)} <span>{escape(note)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_css() -> str:
    return """
    <style>
    .yz-kpi-card-v6 {
      min-height: 142px;
      padding: 18px 19px;
      border-radius: 22px;
      border: 1px solid rgba(226, 232, 240, .86);
      background:
        radial-gradient(circle at 88% 0%, rgba(59,130,246,.13), transparent 10rem),
        linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,250,252,.95));
      box-shadow: 0 14px 34px rgba(2, 6, 23, .16);
      transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
    }
    .yz-kpi-card-v6:hover {
      transform: translateY(-2px);
      border-color: rgba(96, 165, 250, .58);
      box-shadow: 0 20px 42px rgba(2, 6, 23, .24);
    }
    .yz-kpi-topline {display:flex; align-items:center; gap:10px; margin-bottom: 12px;}
    .yz-kpi-icon {width:34px; height:34px; display:flex; align-items:center; justify-content:center; border-radius:13px; background:#eff6ff; font-size:18px;}
    .yz-kpi-title {font-size: 13px; color:#64748b; font-weight:950; letter-spacing:.1px;}
    .yz-kpi-value {font-size: 31px; line-height:1.08; font-weight: 950; color:#0f172a; letter-spacing: -.6px; margin-top: 6px;}
    .yz-kpi-delta {font-size: 12px; font-weight: 950; margin-top: 13px;}
    .yz-kpi-delta span {font-weight: 800; color:#64748b; margin-left:4px;}
    .yz-kpi-delta-up {color:#16a34a;}
    .yz-kpi-delta-down {color:#dc2626;}
    .yz-kpi-delta-flat {color:#64748b;}
    </style>
    """
