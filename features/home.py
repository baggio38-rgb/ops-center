"""首页与总裁驾驶舱。

v1.3.0 CEO Dashboard Plus
- 全新KPI卡片
- AI经营摘要（规则版）
- 今日警报
- 经营健康度
- Top10会员 / Top10代理
- 场馆与游戏偏好分析
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import alert, apply_theme, brief, hero, metric_card, score_card, section
from services.bigquery_client import query_bq

PROJECT = "mydata-494606"
DATASET = "mydata"
VERSION = "v1.3.0"

RISK_ORDER = ["Critical", "High", "Medium", "Low", "Normal"]
RISK_CN = {
    "Critical": "极高风险",
    "High": "高风险",
    "Medium": "中风险",
    "Low": "低风险",
    "Normal": "正常",
}

PERIOD_MAP = {
    "最近7天": 7,
    "最近30天": 30,
    "最近90天": 90,
    "今年": 366,
}


def _fmt_num(value: Any, digits: int = 0) -> str:
    if value is None or pd.isna(value):
        return "-"
    try:
        n = float(value)
    except Exception:
        return str(value)
    if abs(n) >= 100000000:
        return f"{n / 100000000:.2f}亿"
    if abs(n) >= 10000:
        return f"{n / 10000:.2f}万"
    if digits == 0:
        return f"{n:,.0f}"
    return f"{n:,.{digits}f}"


def _fmt_pct(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "-"


def _safe_float(value: Any) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _safe_query(sql: str) -> pd.DataFrame:
    try:
        return query_bq(sql)
    except Exception as exc:
        st.error(f"查询失败：{exc}")
        return pd.DataFrame()


def _delta(today: Any, yesterday: Any) -> float | None:
    t = _safe_float(today)
    y = _safe_float(yesterday)
    if y == 0:
        return None
    return (t - y) / y


@st.cache_data(ttl=300, show_spinner=False)
def _load_daily_summary() -> pd.DataFrame:
    sql = f"""
    WITH daily AS (
      SELECT
        report_date,
        SUM(turnover) AS turnover,
        SUM(valid_turnover) AS valid_turnover,
        SUM(profit_loss) AS profit_loss,
        COUNT(DISTINCT member_key) AS active_members,
        SUM(bet_count) AS bet_count
      FROM `{PROJECT}.{DATASET}.fact_member_daily_v2`
      GROUP BY report_date
    ), ranked AS (
      SELECT *, ROW_NUMBER() OVER (ORDER BY report_date DESC) AS rn
      FROM daily
    ), today AS (
      SELECT * FROM ranked WHERE rn = 1
    ), yesterday AS (
      SELECT * FROM ranked WHERE rn = 2
    ), risk AS (
      SELECT
        COUNTIF(risk_level IN ('Critical','High')) AS high_risk_members,
        COUNTIF(risk_level = 'Critical') AS critical_members,
        COUNTIF(risk_level = 'High') AS high_members,
        COUNTIF(risk_level = 'Medium') AS medium_members,
        AVG(risk_score) AS avg_risk_score
      FROM `{PROJECT}.{DATASET}.risk_member_score`
    ), profile AS (
      SELECT
        COUNT(*) AS profile_members,
        COUNTIF(value_level IN ('Whale','高价值')) AS high_value_members,
        COUNTIF(vip_level IS NOT NULL AND vip_level NOT IN ('','普通会员')) AS vip_members
      FROM `{PROJECT}.{DATASET}.mart_member_profile`
    )
    SELECT
      t.report_date,
      t.turnover,
      t.valid_turnover,
      t.profit_loss,
      t.active_members,
      t.bet_count,
      y.turnover AS prev_turnover,
      y.valid_turnover AS prev_valid_turnover,
      y.profit_loss AS prev_profit_loss,
      y.active_members AS prev_active_members,
      r.high_risk_members,
      r.critical_members,
      r.high_members,
      r.medium_members,
      r.avg_risk_score,
      p.profile_members,
      p.high_value_members,
      p.vip_members
    FROM today t
    LEFT JOIN yesterday y ON TRUE
    CROSS JOIN risk r
    CROSS JOIN profile p
    """
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def _load_daily_trend(days: int = 30) -> pd.DataFrame:
    sql = f"""
    SELECT
      report_date,
      SUM(turnover) AS turnover,
      SUM(valid_turnover) AS valid_turnover,
      SUM(profit_loss) AS profit_loss,
      COUNT(DISTINCT member_key) AS active_members,
      SUM(bet_count) AS bet_count
    FROM `{PROJECT}.{DATASET}.fact_member_daily_v2`
    GROUP BY report_date
    ORDER BY report_date DESC
    LIMIT {int(days)}
    """
    df = _safe_query(sql)
    if not df.empty:
        df = df.sort_values("report_date")
    return df


@st.cache_data(ttl=300, show_spinner=False)
def _load_risk_dist() -> pd.DataFrame:
    sql = f"""
    SELECT
      risk_level,
      COUNT(*) AS members,
      AVG(risk_score) AS avg_score
    FROM `{PROJECT}.{DATASET}.risk_member_score`
    GROUP BY risk_level
    """
    df = _safe_query(sql)
    if df.empty:
        return df
    df["risk_level"] = pd.Categorical(df["risk_level"], categories=RISK_ORDER, ordered=True)
    df["风险等级"] = df["risk_level"].map(RISK_CN).astype(str)
    return df.sort_values("risk_level")


@st.cache_data(ttl=300, show_spinner=False)
def _load_top_risk(limit: int = 10) -> pd.DataFrame:
    sql = f"""
    SELECT
      r.member_id AS `会员账号`,
      p.vip_level AS `VIP等级`,
      p.agent_name AS `代理`,
      r.risk_score AS `风险分`,
      CASE r.risk_level
        WHEN 'Critical' THEN '极高风险'
        WHEN 'High' THEN '高风险'
        WHEN 'Medium' THEN '中风险'
        WHEN 'Low' THEN '低风险'
        ELSE '正常'
      END AS `风险等级`,
      r.valid_turnover AS `有效投注`,
      r.profit_loss AS `盈亏`,
      r.rtp AS `RTP`,
      p.favorite_provider AS `偏好场馆`,
      p.favorite_game AS `偏好游戏`,
      p.auto_tags AS `标签`
    FROM `{PROJECT}.{DATASET}.risk_member_score` r
    LEFT JOIN `{PROJECT}.{DATASET}.mart_member_profile` p
      ON r.member_key = p.member_key
    ORDER BY r.risk_score DESC, r.valid_turnover DESC
    LIMIT {int(limit)}
    """
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def _load_top_members(limit: int = 10) -> pd.DataFrame:
    sql = f"""
    SELECT
      member_id AS `会员账号`,
      vip_level AS `VIP等级`,
      agent_name AS `代理`,
      value_level AS `价值等级`,
      valid_turnover AS `有效投注`,
      profit_loss AS `盈亏`,
      rtp AS `RTP`,
      roi AS `ROI`,
      favorite_provider AS `偏好场馆`,
      favorite_game AS `偏好游戏`,
      auto_tags AS `标签`
    FROM `{PROJECT}.{DATASET}.mart_member_profile`
    ORDER BY valid_turnover DESC
    LIMIT {int(limit)}
    """
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def _load_top_agents(limit: int = 10) -> pd.DataFrame:
    sql = f"""
    SELECT
      IFNULL(agent_name, '未归属') AS `代理`,
      COUNT(DISTINCT member_key) AS `会员数`,
      SUM(valid_turnover) AS `有效投注`,
      SUM(turnover) AS `流水`,
      SUM(profit_loss) AS `会员盈亏`,
      AVG(rtp) AS `平均RTP`,
      COUNTIF(value_level IN ('Whale','高价值')) AS `高价值会员`,
      COUNTIF(auto_tags LIKE '%VIP会员%') AS `VIP会员`
    FROM `{PROJECT}.{DATASET}.mart_member_profile`
    GROUP BY `代理`
    ORDER BY `有效投注` DESC
    LIMIT {int(limit)}
    """
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def _load_provider_analysis(limit: int = 12) -> pd.DataFrame:
    sql = f"""
    SELECT
      IFNULL(favorite_category, '未知类型') AS `类型`,
      IFNULL(favorite_provider, '未知场馆') AS `场馆`,
      COUNT(DISTINCT member_key) AS `会员数`,
      SUM(valid_turnover) AS `有效投注`,
      SUM(turnover) AS `流水`,
      SUM(profit_loss) AS `会员盈亏`,
      SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS `RTP`,
      SUM(valid_turnover) / SUM(SUM(valid_turnover)) OVER() AS `占比`
    FROM `{PROJECT}.{DATASET}.mart_member_profile`
    GROUP BY `类型`, `场馆`
    ORDER BY `有效投注` DESC
    LIMIT {int(limit)}
    """
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def _load_table_status() -> pd.DataFrame:
    sql = f"""
    SELECT 'fact_member_daily_v2' AS `数据表`, COUNT(*) AS `行数`, MAX(updated_at) AS `更新时间`
    FROM `{PROJECT}.{DATASET}.fact_member_daily_v2`
    UNION ALL
    SELECT 'mart_member_profile', COUNT(*), MAX(updated_at)
    FROM `{PROJECT}.{DATASET}.mart_member_profile`
    UNION ALL
    SELECT 'risk_member_score', COUNT(*), MAX(updated_at)
    FROM `{PROJECT}.{DATASET}.risk_member_score`
    """
    return _safe_query(sql)


def _health_score(kpis: pd.Series | None, risk_dist: pd.DataFrame) -> tuple[int, list[str]]:
    if kpis is None:
        return 0, ["暂无数据"]
    score = 100
    notes: list[str] = []
    turnover_delta = _delta(kpis.get("turnover"), kpis.get("prev_turnover"))
    active_delta = _delta(kpis.get("active_members"), kpis.get("prev_active_members"))
    high_risk = _safe_float(kpis.get("high_risk_members"))
    critical = _safe_float(kpis.get("critical_members"))
    profit = _safe_float(kpis.get("profit_loss"))

    if turnover_delta is not None and turnover_delta < -0.1:
        score -= 12
        notes.append("流水较前一日下降超过10%")
    elif turnover_delta is not None and turnover_delta > 0.1:
        notes.append("流水较前一日明显增长")
    if active_delta is not None and active_delta < -0.1:
        score -= 10
        notes.append("活跃会员下降超过10%")
    if high_risk > 20:
        score -= 10
        notes.append("高风险会员数量偏高")
    if critical > 0:
        score -= 10
        notes.append("存在极高风险会员")
    if profit > 0:
        score -= 8
        notes.append("会员整体盈利，公司需要关注高额赢家")
    if not notes:
        notes.append("主要指标稳定，暂无重大经营异常")
    return max(0, min(100, int(score))), notes


def _build_brief(kpis: pd.Series | None, trend: pd.DataFrame, risk_dist: pd.DataFrame) -> list[str]:
    if kpis is None:
        return ["目前尚未读取到经营数据，请先确认数据同步与 BigQuery 表是否正常。"]

    lines: list[str] = []
    report_date = kpis.get("report_date", "-")
    turnover_delta = _delta(kpis.get("turnover"), kpis.get("prev_turnover"))
    active_delta = _delta(kpis.get("active_members"), kpis.get("prev_active_members"))
    profit = _safe_float(kpis.get("profit_loss"))
    high_risk = _safe_float(kpis.get("high_risk_members"))

    if turnover_delta is None:
        lines.append(f"最新经营日为 {report_date}，今日流水 {_fmt_num(kpis.get('turnover'))}。")
    else:
        direction = "增长" if turnover_delta >= 0 else "下降"
        lines.append(f"最新经营日为 {report_date}，今日流水 {_fmt_num(kpis.get('turnover'))}，较前一日{direction} {abs(turnover_delta) * 100:.2f}%。")

    if active_delta is not None:
        direction = "增长" if active_delta >= 0 else "下降"
        lines.append(f"活跃会员 {_fmt_num(kpis.get('active_members'))} 人，较前一日{direction} {abs(active_delta) * 100:.2f}%。")

    if profit > 0:
        lines.append(f"今日会员整体盈利 {_fmt_num(profit)}，建议优先查看高盈利会员与高RTP会员。")
    else:
        lines.append(f"今日会员整体亏损 {_fmt_num(abs(profit))}，公司侧经营结果相对有利。")

    if high_risk > 0:
        lines.append(f"当前高风险会员 {int(high_risk)} 人，建议风控优先处理风险排行榜前10名。")
    else:
        lines.append("当前暂无高风险会员，风控状态相对稳定。")

    if not risk_dist.empty:
        top = risk_dist.sort_values("members", ascending=False).head(1).iloc[0]
        lines.append(f"会员风险分布以「{top.get('风险等级','-')}」为主。")
    return lines


def _build_alerts(kpis: pd.Series | None) -> list[tuple[str, str]]:
    if kpis is None:
        return [("暂无数据，无法生成今日警报。", "warning")]
    alerts: list[tuple[str, str]] = []
    turnover_delta = _delta(kpis.get("turnover"), kpis.get("prev_turnover"))
    profit = _safe_float(kpis.get("profit_loss"))
    high_risk = _safe_float(kpis.get("high_risk_members"))
    critical = _safe_float(kpis.get("critical_members"))
    high_value = _safe_float(kpis.get("high_value_members"))

    if critical > 0:
        alerts.append((f"🔴 极高风险会员：{_fmt_num(critical)} 人，请优先处理。", "critical"))
    if high_risk > 0:
        alerts.append((f"🟠 高风险会员：{_fmt_num(high_risk)} 人。", "warning"))
    if turnover_delta is not None and turnover_delta < -0.1:
        alerts.append((f"🟠 流水较前一日下降 {abs(turnover_delta) * 100:.2f}%。", "warning"))
    if profit > 0:
        alerts.append((f"🔴 会员整体盈利 {_fmt_num(profit)}，建议查看高额赢家。", "critical"))
    if high_value > 0:
        alerts.append((f"🟢 高价值会员 {_fmt_num(high_value)} 人，建议 VIP 团队重点维护。", "good"))
    if not alerts:
        alerts.append(("🟢 暂无重大经营警报。", "good"))
    return alerts


def _format_money_table(df: pd.DataFrame, money_cols: list[str], pct_cols: list[str] | None = None) -> pd.DataFrame:
    out = df.copy()
    for col in money_cols:
        if col in out.columns:
            out[col] = out[col].map(_fmt_num)
    for col in pct_cols or []:
        if col in out.columns:
            out[col] = out[col].map(_fmt_pct)
    return out


def render_home_page() -> None:
    apply_theme()
    hero("博彩智能决策平台", "首页 · 经营概况 · 风险预警 · 快捷入口", VERSION)

    kpi_df = _load_daily_summary()
    trend = _load_daily_trend(14)
    risk_dist = _load_risk_dist()
    kpis = None if kpi_df.empty else kpi_df.iloc[0]

    section("今日经营概况", "以数据仓库最新投注日作为经营日。")
    if kpis is not None:
        cols = st.columns(4)
        with cols[0]:
            metric_card("今日流水", _fmt_num(kpis.get("turnover")), f"昨日：{_fmt_num(kpis.get('prev_turnover'))}", _delta(kpis.get("turnover"), kpis.get("prev_turnover")), "💰")
        with cols[1]:
            metric_card("今日有效投注", _fmt_num(kpis.get("valid_turnover")), f"昨日：{_fmt_num(kpis.get('prev_valid_turnover'))}", _delta(kpis.get("valid_turnover"), kpis.get("prev_valid_turnover")), "🎲")
        with cols[2]:
            metric_card("今日会员盈亏", _fmt_num(kpis.get("profit_loss")), f"昨日：{_fmt_num(kpis.get('prev_profit_loss'))}", _delta(kpis.get("profit_loss"), kpis.get("prev_profit_loss")), "📈")
        with cols[3]:
            metric_card("活跃会员", _fmt_num(kpis.get("active_members")), f"下注笔数：{_fmt_num(kpis.get('bet_count'))}", _delta(kpis.get("active_members"), kpis.get("prev_active_members")), "👥")

        cols2 = st.columns(4)
        with cols2[0]:
            metric_card("会员画像数", _fmt_num(kpis.get("profile_members")), "来自 mart_member_profile", None, "👤")
        with cols2[1]:
            metric_card("高价值会员", _fmt_num(kpis.get("high_value_members")), "Whale / 高价值", None, "💎")
        with cols2[2]:
            metric_card("高风险会员", _fmt_num(kpis.get("high_risk_members")), "Critical + High", None, "🛡")
        with cols2[3]:
            metric_card("平均风险分", _fmt_num(kpis.get("avg_risk_score"), 1), "来自 risk_member_score", None, "⚠️")
    else:
        st.warning("暂无首页 KPI 数据，请确认 fact_member_daily_v2、mart_member_profile、risk_member_score 是否已建立。")

    section("AI经营摘要", "规则版摘要，后续可无缝接入大模型。")
    brief(_build_brief(kpis, trend, risk_dist))

    section("今日警报")
    for text, level in _build_alerts(kpis):
        alert(text, level)

    section("快捷入口")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.success("会员中心\n\n搜索会员、查看画像、投注偏好与近期注单。")
    with c2:
        st.warning("风控中心\n\n查看高风险会员、风险等级与命中规则。")
    with c3:
        st.info("总裁驾驶舱\n\n查看平台经营趋势、风险排行与经营摘要。")
    with c4:
        st.write("版本信息\n\n查看当前版本、数据来源与更新说明。")

    section("系统状态")
    status = _load_table_status()
    if not status.empty:
        st.dataframe(status, use_container_width=True, hide_index=True)


def render_executive_dashboard() -> None:
    apply_theme()
    hero("总裁驾驶舱", "30秒掌握经营、风险、会员、代理与场馆变化", VERSION)

    kpi_df = _load_daily_summary()
    risk_dist = _load_risk_dist()
    kpis = None if kpi_df.empty else kpi_df.iloc[0]

    period_label = st.radio("趋势区间", list(PERIOD_MAP.keys()), horizontal=True, index=1)
    trend = _load_daily_trend(PERIOD_MAP[period_label])

    health, health_notes = _health_score(kpis, risk_dist)

    section("经营健康度")
    h1, h2 = st.columns([1, 3])
    with h1:
        score_card("经营健康度", health, "综合流水、活跃、风险与盈亏情况。")
    with h2:
        brief(health_notes)

    section("核心KPI")
    if kpis is not None:
        cols = st.columns(5)
        with cols[0]: metric_card("最新经营日", str(kpis.get("report_date", "-")), "数据仓库最新日期", None, "📅")
        with cols[1]: metric_card("流水", _fmt_num(kpis.get("turnover")), f"昨日：{_fmt_num(kpis.get('prev_turnover'))}", _delta(kpis.get("turnover"), kpis.get("prev_turnover")), "💰")
        with cols[2]: metric_card("有效投注", _fmt_num(kpis.get("valid_turnover")), f"昨日：{_fmt_num(kpis.get('prev_valid_turnover'))}", _delta(kpis.get("valid_turnover"), kpis.get("prev_valid_turnover")), "🎯")
        with cols[3]: metric_card("会员盈亏", _fmt_num(kpis.get("profit_loss")), f"昨日：{_fmt_num(kpis.get('prev_profit_loss'))}", _delta(kpis.get("profit_loss"), kpis.get("prev_profit_loss")), "📊")
        with cols[4]: metric_card("高风险", _fmt_num(kpis.get("high_risk_members")), "Critical + High", None, "🚨")

    section("AI经营摘要")
    brief(_build_brief(kpis, trend, risk_dist))

    section("今日警报")
    for text, level in _build_alerts(kpis):
        alert(text, level)

    section("经营趋势", f"当前区间：{period_label}")
    if not trend.empty:
        t1, t2 = st.columns(2)
        with t1:
            fig = px.line(trend, x="report_date", y="turnover", markers=True, title="流水趋势")
            st.plotly_chart(fig, use_container_width=True)
        with t2:
            fig = px.line(trend, x="report_date", y="profit_loss", markers=True, title="会员盈亏趋势")
            st.plotly_chart(fig, use_container_width=True)

    section("风险分布")
    if not risk_dist.empty:
        c1, c2 = st.columns([1, 1])
        with c1:
            fig = px.bar(risk_dist, x="风险等级", y="members", text="members", title="风险等级会员数")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            show = risk_dist[["风险等级", "members", "avg_score"]].copy()
            show["avg_score"] = show["avg_score"].map(lambda x: _fmt_num(x, 1))
            st.dataframe(show, use_container_width=True, hide_index=True)

    section("场馆分析", "基于会员偏好场馆与有效投注汇总。")
    providers = _load_provider_analysis(12)
    if not providers.empty:
        p1, p2 = st.columns([1, 1])
        with p1:
            fig = px.bar(providers.head(10), x="场馆", y="有效投注", color="类型", title="场馆有效投注 Top10")
            st.plotly_chart(fig, use_container_width=True)
        with p2:
            show = _format_money_table(providers, ["有效投注", "流水", "会员盈亏"], ["RTP", "占比"])
            st.dataframe(show, use_container_width=True, hide_index=True)

    section("Top10高价值会员")
    top_members = _load_top_members(10)
    if not top_members.empty:
        show = _format_money_table(top_members, ["有效投注", "盈亏"], ["RTP", "ROI"])
        st.dataframe(show, use_container_width=True, hide_index=True)

    section("Top10代理")
    top_agents = _load_top_agents(10)
    if not top_agents.empty:
        show = _format_money_table(top_agents, ["有效投注", "流水", "会员盈亏"], ["平均RTP"])
        st.dataframe(show, use_container_width=True, hide_index=True)

    section("高风险会员排行")
    top_risk = _load_top_risk(15)
    if not top_risk.empty:
        show = _format_money_table(top_risk, ["有效投注", "盈亏"], ["RTP"])
        st.dataframe(show, use_container_width=True, hide_index=True)


def render_version_page() -> None:
    apply_theme()
    hero("版本信息", "系统版本、更新说明与数据来源", VERSION)
    st.write("当前版本：v1.3.0")
    st.write("本次更新：CEO Dashboard Plus、AI经营摘要、今日警报、经营健康度、Top10会员、Top10代理、场馆分析、统一UI组件。")
    st.write("数据来源：fact_member_daily_v2、mart_member_profile、risk_member_score。")
    st.write("建议 Commit：Add CEO dashboard plus v1.3.0")
