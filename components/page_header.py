"""V6 page header and status components."""
from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st


def page_header(
    title: str,
    subtitle: str = "",
    *,
    version: str = "V6.0.0",
    updated_at: str = "-",
    status_items: Iterable[tuple[str, str]] | None = None,
) -> None:
    status_items = list(status_items or [("BigQuery", "正常"), ("ETL", "正常"), ("Aggregate", "正常")])
    pills = "".join(
        f'<span class="yz-status-pill-v6"><i></i>{escape(name)}：{escape(status)}</span>'
        for name, status in status_items
    )
    st.markdown(
        f"""
        <div class="yz-page-header-v6">
          <div>
            <div class="yz-page-kicker">亿兆智能决策平台 · {escape(version)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
          </div>
          <div class="yz-page-status-v6">
            <div class="yz-page-updated">数据更新时间：{escape(updated_at)}</div>
            <div class="yz-page-pills">{pills}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header_css() -> str:
    return """
    <style>
    .yz-page-header-v6 {
      position: relative;
      display:flex;
      align-items:flex-start;
      justify-content:space-between;
      gap: 24px;
      padding: 24px 26px;
      margin: 6px 0 18px 0;
      border-radius: 26px;
      border: 1px solid rgba(148,163,184,.30);
      background:
        radial-gradient(circle at 76% 22%, rgba(14,165,233,.28), transparent 26rem),
        radial-gradient(circle at 10% 0%, rgba(37,99,235,.34), transparent 24rem),
        linear-gradient(135deg, rgba(15,23,42,.96), rgba(30,64,175,.76) 58%, rgba(2,132,199,.43));
      box-shadow: 0 18px 44px rgba(2, 6, 23, .26);
      overflow:hidden;
    }
    .yz-page-header-v6:after {
      content:""; position:absolute; right:-82px; top:-90px; width:260px; height:260px;
      border-radius:999px; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12);
    }
    .yz-page-header-v6 > div {position:relative; z-index:1;}
    .yz-page-kicker {font-size:12px; font-weight:950; color:#93c5fd; letter-spacing:.4px; text-transform:uppercase; margin-bottom:8px;}
    .yz-page-header-v6 h1 {margin:0; color:#fff; font-size:33px; line-height:1.12; font-weight:950; letter-spacing:-.4px;}
    .yz-page-header-v6 p {margin:8px 0 0 0; color:#dbeafe; font-size:14px; font-weight:800;}
    .yz-page-status-v6 {min-width: 360px; text-align:right;}
    .yz-page-updated {font-size:12px; color:#dbeafe; font-weight:900; margin-bottom:12px;}
    .yz-page-pills {display:flex; flex-wrap:wrap; justify-content:flex-end; gap:8px;}
    .yz-status-pill-v6 {display:inline-flex; align-items:center; gap:7px; padding:8px 10px; border-radius:999px; background:rgba(255,255,255,.11); color:#e0f2fe; border:1px solid rgba(255,255,255,.13); font-size:12px; font-weight:950;}
    .yz-status-pill-v6 i {width:8px; height:8px; border-radius:999px; background:#22c55e; box-shadow:0 0 0 4px rgba(34,197,94,.14); display:inline-block;}
    @media (max-width: 980px) {.yz-page-header-v6 {flex-direction:column;} .yz-page-status-v6 {text-align:left; min-width:0;} .yz-page-pills {justify-content:flex-start;}}
    </style>
    """
