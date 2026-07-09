"""Reusable KPI card components."""
from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st


def fmt_compact_number(value: Any, digits: int = 2) -> str:
    try:
        if value is None or pd.isna(value):
            return "0"
        n = float(value)
    except Exception:
        return str(value)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 100_000_000:
        return f"{sign}{n / 100_000_000:.{digits}f}亿"
    if n >= 10_000:
        return f"{sign}{n / 10_000:.{digits}f}万"
    if n == int(n):
        return f"{sign}{int(n):,}"
    return f"{sign}{n:,.{digits}f}"


def fmt_percent(value: Any, digits: int = 2) -> str:
    try:
        if value is None or pd.isna(value):
            return "0.00%"
        return f"{float(value) * 100:.{digits}f}%"
    except Exception:
        return str(value)


def _fmt_delta(delta: Any) -> str:
    if delta is None:
        return ""
    try:
        if pd.isna(delta):
            return ""
        d = float(delta)
        arrow = "▲" if d >= 0 else "▼"
        cls = "#16A34A" if d >= 0 else "#DC2626"
        return f'<div style="margin-top:10px;color:{cls};font-weight:850;">{arrow} {abs(d) * 100:.2f}% 较昨日</div>'
    except Exception:
        return f'<div style="margin-top:10px;color:#64748B;font-weight:800;">{escape(str(delta))}</div>'


def kpi_card(
    label: str,
    value: Any,
    *,
    icon: str = "📊",
    delta: Any = None,
    value_type: str = "number",
) -> None:
    display_value = fmt_percent(value) if value_type == "percent" else fmt_compact_number(value)
    st.markdown(
        f"""
        <div class="yz-kpi-card">
            <div class="yz-kpi-label">{escape(icon)} {escape(label)}</div>
            <div class="yz-kpi-value">{escape(display_value)}</div>
            {_fmt_delta(delta)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_kpi_card(label: str, value: str, delta: str = "", icon: str = "📊") -> None:
    st.markdown(
        f"""
        <div class="yz-kpi-card">
            <div class="yz-kpi-label">{escape(icon)} {escape(label)}</div>
            <div class="yz-kpi-value">{escape(str(value))}</div>
            <div style="margin-top:10px;color:#16A34A;font-weight:800;">{escape(delta)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_css() -> str:
    """Compatibility shim. CSS now lives in assets/css/main.css."""
    return ""
