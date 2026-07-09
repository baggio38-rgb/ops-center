"""V6.0 运营总览页面。"""
from __future__ import annotations

from typing import Any
from textwrap import dedent

import pandas as pd
import plotly.express as px
import streamlit as st

from components.kpi_card import kpi_card, kpi_css, fmt_compact_number, fmt_percent
from components.page_header import page_header, page_header_css
from components.section_title import section_title, section_title_css
from components.chart_card import chart_card, chart_card_css
from components.status_badge import status_badge_css
from services.dashboard_service import (
    load_dashboard_hourly,
    load_dashboard_kpi,
    load_dashboard_top,
    make_rule_summary,
)


def _inject_v6_css() -> None:
    st.markdown(
        dedent(kpi_css() + page_header_css() + section_title_css() + chart_card_css() + status_badge_css() +
        """
        <style>
        .yz-ai-summary-v6 {
          border-radius: 22px;
          padding: 19px 21px;
          background: linear-gradient(180deg, rgba(255,255,255,.97), rgba(248,250,252,.96));
          border: 1px solid rgba(226,232,240,.86);
          box-shadow: 0 12px 32px rgba(2,6,23,.15);
          color:#0f172a;
          font-weight:800;
          line-height:1.85;
        }
        .yz-ai-summary-v6 b {font-weight:950; color:#1d4ed8;}
        .yz-risk-mini-v6 {
          border-radius: 18px;
          padding: 15px 16px;
          background: rgba(255,255,255,.96);
          color:#0f172a;
          border-left: 6px solid #f59e0b;
          box-shadow: 0 12px 30px rgba(2,6,23,.14);
          font-weight:850;
          margin-bottom: 10px;
        }
        .yz-table-note-v6 {font-size:12px; color:#94a3b8; font-weight:800; margin-top:-4px; margin-bottom:7px;}
        </style>
        """),
        unsafe_allow_html=True,
    )


def _value(row: pd.Series, key: str, default: Any = 0) -> Any:
    try:
        v = row.get(key, default)
        if pd.isna(v):
            return default
        return v
    except Exception:
        return default


def _updated_at(kpi: pd.DataFrame) -> str:
    if kpi.empty or "updated_at" not in kpi.columns:
        return "-"
    try:
        ts = pd.to_datetime(kpi.iloc[0]["updated_at"])
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(kpi.iloc[0].get("updated_at", "-"))


def _render_kpis(kpi: pd.DataFrame) -> None:
    if kpi.empty:
        st.info("尚未建立运营总览资料。请先执行 V5.3 自动刷新。")
        return
    r = kpi.iloc[0]
    first = st.columns(4)
    with first[0]:
        kpi_card("今日投注金额", _value(r, "bet_amount"), icon="💰", delta=_value(r, "bet_amount_delta", None))
    with first[1]:
        kpi_card("今日有效投注", _value(r, "valid_turnover"), icon="💵", delta=_value(r, "valid_turnover_delta", None))
    with first[2]:
        kpi_card("今日平台盈亏", _value(r, "platform_profit_loss"), icon="📈", delta=_value(r, "platform_profit_delta", None))
    with first[3]:
        kpi_card("今日活跃会员", _value(r, "member_count"), icon="👥", delta=_value(r, "member_count_delta", None))

    second = st.columns(4)
    with second[0]:
        kpi_card("世界杯有效投注", _value(r, "worldcup_turnover"), icon="⚽", delta=None)
    with second[1]:
        kpi_card("体育有效投注", _value(r, "sportsbook_turnover"), icon="🏟️", delta=None)
    with second[2]:
        kpi_card("Casino有效投注", _value(r, "casino_turnover"), icon="🎰", delta=None)
    with second[3]:
        kpi_card("平台ROI", _value(r, "platform_roi"), icon="🎯", value_type="percent", delta=None)


def _render_hourly(hourly: pd.DataFrame) -> None:
    section_title("今日趋势", "以小时观察投注金额、有效投注与平台盈亏。")
    if hourly.empty:
        st.info("目前暂无趋势资料，请确认 V5.3 自动刷新已完成。")
        return
    df = hourly.copy()
    if "report_hour" in df.columns:
        df["时段"] = df["report_hour"].astype(str).str.zfill(2) + ":00"
    else:
        df["时段"] = range(len(df))

    c1, c2 = st.columns(2)
    with c1:
        with chart_card("有效投注趋势", "每小时有效投注变化"):
            fig = px.line(df, x="时段", y="valid_turnover", markers=True, labels={"valid_turnover": "有效投注", "时段": "时段"})
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=18, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        with chart_card("平台盈亏趋势", "每小时平台盈亏变化"):
            fig = px.bar(df, x="时段", y="platform_profit_loss", labels={"platform_profit_loss": "平台盈亏", "时段": "时段"})
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=18, b=10))
            st.plotly_chart(fig, use_container_width=True)


def _format_top_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = [c for c in ["metric_type", "item_name", "valid_turnover", "platform_profit_loss", "bet_count", "member_count"] if c in df.columns]
    out = df[cols].copy()
    rename = {
        "metric_type": "类型",
        "item_name": "项目",
        "valid_turnover": "有效投注",
        "platform_profit_loss": "平台盈亏",
        "bet_count": "投注笔数",
        "member_count": "投注人数",
    }
    out = out.rename(columns=rename)
    for c in ["有效投注", "平台盈亏"]:
        if c in out.columns:
            out[c] = out[c].map(lambda v: fmt_compact_number(v, 2))
    return out


def _render_tops(tops: pd.DataFrame) -> None:
    section_title("热门排行榜", "运营总览的四个入口：赛事、游戏、场馆、会员。")
    if tops.empty:
        st.info("目前暂无排行榜资料，请确认 V5.3 自动刷新已完成。")
        return
    c1, c2 = st.columns(2)
    types = list(tops["metric_type"].dropna().unique()) if "metric_type" in tops.columns else ["热门赛事"]
    left_type = types[0] if types else "热门赛事"
    right_type = types[1] if len(types) > 1 else left_type
    with c1:
        with chart_card(left_type, "按有效投注排序"):
            st.dataframe(_format_top_df(tops[tops["metric_type"] == left_type].head(10)), use_container_width=True, hide_index=True)
    with c2:
        with chart_card(right_type, "按有效投注排序"):
            st.dataframe(_format_top_df(tops[tops["metric_type"] == right_type].head(10)), use_container_width=True, hide_index=True)


def _render_ai_summary(kpi: pd.DataFrame, tops: pd.DataFrame) -> None:
    section_title("AI 今日运营摘要", "第一版采用规则生成，后续可升级为 AI 自动分析。")
    lines = make_rule_summary(kpi, tops)
    lis = "".join(f"<li>{line}</li>" for line in lines)
    st.markdown(
        f"""
        <div class="yz-ai-summary-v6">
          <b>今日重点</b>
          <ul>{lis}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_risk_notice(kpi: pd.DataFrame) -> None:
    section_title("风险提醒", "运营总览仅显示高层提醒，详细处理请进入风险中心。")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="yz-risk-mini-v6">⚠ 高流水赛事请结合世界杯专区持续观察。</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="yz-risk-mini-v6">👤 VIP 高价值会员若出现连续盈利，请进入 Member360 复查。</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="yz-risk-mini-v6">🧭 若平台盈亏转弱，优先检查热门赛事与代理贡献。</div>', unsafe_allow_html=True)


def render_operation_overview() -> None:
    _inject_v6_css()
    kpi = load_dashboard_kpi()
    hourly = load_dashboard_hourly()
    tops = load_dashboard_top(limit=10)

    page_header(
        "运营总览",
        "管理层首页，快速掌握今日投注、盈亏、会员活跃与重点风险。",
        version="V6.0.1",
        updated_at=_updated_at(kpi),
        status_items=[("BigQuery", "正常"), ("ETL", "正常"), ("Aggregate", "正常")],
    )

    section_title("今日核心 KPI", "所有数字来自现有 BigQuery Aggregate：agg_dashboard_daily。")
    _render_kpis(kpi)
    _render_hourly(hourly)
    _render_tops(tops)
    _render_ai_summary(kpi, tops)
    _render_risk_notice(kpi)
