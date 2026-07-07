"""世界杯专区 V2 Enterprise Dashboard。

使用 V5 Data Warehouse：
- agg_worldcup_match
- agg_worldcup_playtype
- agg_member_worldcup
- dim_member
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.worldcup_cards import apply_worldcup_v2_style, hero, kpi_card, section
from components.charts import bar_chart, line_chart, donut_chart, dual_axis_bar_line
from services import worldcup_service as svc
from utils.formatter import fmt_num, fmt_pct


def _first(df: pd.DataFrame, col: str, default=0):
    if df is None or df.empty or col not in df.columns:
        return default
    return df.iloc[0][col]


def _filters() -> tuple[list[str], list[str]]:
    opts = svc.get_filter_options()
    with st.container():
        c1, c2 = st.columns([1, 1])
        with c1:
            stages = st.multiselect("阶段筛选", opts.get("stages", []), placeholder="全部阶段")
        with c2:
            teams = st.multiselect("球队筛选", opts.get("teams", []), placeholder="全部球队")
    return stages, teams


def render_worldcup_v2_overview() -> None:
    apply_worldcup_v2_style()
    hero("世界杯运营分析中心", "基于 V5 数据仓储，所有统计统一读取 Aggregate 层。")
    stages, teams = _filters()

    kpi = svc.get_worldcup_kpi(stages, teams)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        kpi_card("注单数", fmt_num(_first(kpi, "bet_count")), "去重后注单")
    with c2:
        kpi_card("下注人数", fmt_num(_first(kpi, "member_count")), "世界杯会员")
    with c3:
        kpi_card("比赛数", fmt_num(_first(kpi, "match_count")), "按 game_id")
    with c4:
        kpi_card("下注金额", fmt_num(_first(kpi, "bet_amount")), "总投注")
    with c5:
        kpi_card("有效投注", fmt_num(_first(kpi, "valid_turnover")), "统一口径")
    with c6:
        kpi_card("平台盈亏", fmt_num(_first(kpi, "platform_profit_loss")), f"ROI {fmt_pct(_first(kpi, 'platform_roi'))}")

    section("趋势与阶段", "每日走势与各阶段投注分布。")
    trend = svc.get_daily_trend(stages, teams)
    s1, s2 = st.columns([1.4, 1])
    with s1:
        dual_axis_bar_line(trend, "match_date", "valid_turnover", "platform_profit_loss", "每日有效投注 / 平台盈亏")
    with s2:
        stage_df = svc.get_stage_summary()
        donut_chart(stage_df, "stage", "valid_turnover", "阶段流水占比")

    section("比赛排行", "依有效投注排序，比赛名称来自 dim_game。")
    match_df = svc.get_match_summary(stages, teams, limit=20)
    mchart = match_df[["match_name", "valid_turnover"]].head(10) if not match_df.empty else pd.DataFrame()
    bar_chart(mchart.sort_values("valid_turnover") if not mchart.empty else mchart, "match_name", "valid_turnover", "Top10 比赛有效投注", orientation="h")
    st.dataframe(match_df, use_container_width=True, hide_index=True)


def render_worldcup_v2_matches() -> None:
    apply_worldcup_v2_style()
    hero("单场比赛分析", "每场比赛以 game_id 为唯一识别，不再解析投注详情。")
    stages, teams = _filters()
    df = svc.get_match_summary(stages, teams, limit=100)
    if df.empty:
        st.info("目前没有符合筛选条件的比赛。")
        return
    c1, c2 = st.columns([1.15, .85])
    with c1:
        bar_chart(df.head(20).sort_values("valid_turnover"), "match_name", "valid_turnover", "有效投注 Top20", orientation="h", height=620)
    with c2:
        bar_chart(df.head(20).sort_values("platform_profit_loss"), "match_name", "platform_profit_loss", "平台盈亏 Top20", orientation="h", height=620)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_worldcup_v2_playtypes() -> None:
    apply_worldcup_v2_style()
    hero("玩法分析", "读取 agg_worldcup_playtype，支持玩法流水、人数、盈亏快速分析。")
    opts = svc.get_filter_options()
    stages = st.multiselect("阶段筛选", opts.get("stages", []), placeholder="全部阶段")
    df = svc.get_playtype_summary(stages, limit=60)
    if df.empty:
        st.info("暂无玩法汇总资料。")
        return
    c1, c2 = st.columns(2)
    with c1:
        bar_chart(df.head(15).sort_values("valid_turnover"), "play_type", "valid_turnover", "玩法有效投注 Top15", orientation="h", height=520)
    with c2:
        bar_chart(df.head(15).sort_values("platform_profit_loss"), "play_type", "platform_profit_loss", "玩法平台盈亏 Top15", orientation="h", height=520)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_worldcup_v2_members() -> None:
    apply_worldcup_v2_style()
    hero("会员分析", "读取 agg_member_worldcup，并结合 dim_member 的 VIP、代理与风险等级。")
    df = svc.get_member_summary(limit=100)
    if df.empty:
        st.info("暂无会员汇总资料。")
        return
    c1, c2 = st.columns(2)
    with c1:
        bar_chart(df.head(20).sort_values("valid_turnover"), "member_key", "valid_turnover", "会员有效投注 Top20", orientation="h", height=620)
    with c2:
        prof = df.sort_values("platform_profit_loss", ascending=False).head(20)
        bar_chart(prof.sort_values("platform_profit_loss"), "member_key", "platform_profit_loss", "平台盈利会员 Top20", orientation="h", height=620)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_worldcup_v2_risk() -> None:
    apply_worldcup_v2_style()
    hero("世界杯风险会员", "结合 dim_member 风险评分与世界杯会员汇总。")
    dist = svc.get_risk_distribution()
    risk_df = svc.get_risk_member_summary(limit=100)
    c1, c2 = st.columns([.85, 1.15])
    with c1:
        donut_chart(dist, "risk_level", "member_count", "风险等级分布")
    with c2:
        if risk_df.empty:
            st.success("当前世界杯会员没有非 Normal 风险资料。")
        else:
            bar_chart(risk_df.head(20).sort_values("valid_turnover"), "member_key", "valid_turnover", "风险会员有效投注 Top20", orientation="h")
    st.dataframe(risk_df, use_container_width=True, hide_index=True)
