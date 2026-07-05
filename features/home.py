"""首页与总裁驾驶舱。

v1.2.0
- 首页：经营概况、风险概况、快捷入口、系统状态
- 总裁驾驶舱：趋势、排行榜、经营摘要
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from services.bigquery_client import query_bq

PROJECT = "mydata-494606"
DATASET = "mydata"

RISK_ORDER = ["Critical", "High", "Medium", "Low", "Normal"]
RISK_CN = {
    "Critical": "极高风险",
    "High": "高风险",
    "Medium": "中风险",
    "Low": "低风险",
    "Normal": "正常",
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


def _safe_query(sql: str) -> pd.DataFrame:
    try:
        return query_bq(sql)
    except Exception as exc:
        st.error(f"查询失败：{exc}")
        return pd.DataFrame()


def _metric_card(title: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div style="border:1px solid #e5e7eb;border-radius:16px;padding:16px 18px;background:#fff;box-shadow:0 1px 4px rgba(15,23,42,.07);min-height:112px;">
          <div style="font-size:13px;color:#64748b;margin-bottom:8px;">{title}</div>
          <div style="font-size:29px;font-weight:850;color:#0f172a;line-height:1.1;">{value}</div>
          <div style="font-size:12px;color:#64748b;margin-top:8px;">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(title: str, subtitle: str = "") -> None:
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


@st.cache_data(ttl=300, show_spinner=False)
def _load_home_kpis() -> pd.DataFrame:
    sql = f"""
    WITH latest_day AS (
      SELECT MAX(report_date) AS report_date
      FROM `{PROJECT}.{DATASET}.fact_member_daily_v2`
    ), today AS (
      SELECT
        f.report_date,
        SUM(f.turnover) AS turnover,
        SUM(f.valid_turnover) AS valid_turnover,
        SUM(f.profit_loss) AS profit_loss,
        COUNT(DISTINCT f.member_key) AS active_members,
        COUNT(*) AS member_daily_rows,
        SUM(f.bet_count) AS bet_count
      FROM `{PROJECT}.{DATASET}.fact_member_daily_v2` f
      JOIN latest_day d ON f.report_date = d.report_date
      GROUP BY f.report_date
    ), risk AS (
      SELECT
        COUNTIF(risk_level IN ('Critical','High')) AS high_risk_members,
        COUNTIF(risk_level = 'Critical') AS critical_members,
        COUNTIF(risk_level = 'High') AS high_members,
        AVG(risk_score) AS avg_risk_score
      FROM `{PROJECT}.{DATASET}.risk_member_score`
    ), profile AS (
      SELECT
        COUNT(*) AS profile_members,
        COUNTIF(value_level IN ('Whale','高价值')) AS high_value_members
      FROM `{PROJECT}.{DATASET}.mart_member_profile`
    )
    SELECT
      t.*,
      r.high_risk_members,
      r.critical_members,
      r.high_members,
      r.avg_risk_score,
      p.profile_members,
      p.high_value_members
    FROM today t
    CROSS JOIN risk r
    CROSS JOIN profile p
    """
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def _load_daily_trend(days: int = 14) -> pd.DataFrame:
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
      favorite_provider AS `偏好场馆`,
      favorite_game AS `偏好游戏`,
      auto_tags AS `标签`
    FROM `{PROJECT}.{DATASET}.mart_member_profile`
    ORDER BY valid_turnover DESC
    LIMIT {int(limit)}
    """
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def _load_table_status() -> pd.DataFrame:
    sql = f"""
    SELECT 'fact_member_daily_v2' AS table_name, COUNT(*) AS rows_count, MAX(updated_at) AS updated_at
    FROM `{PROJECT}.{DATASET}.fact_member_daily_v2`
    UNION ALL
    SELECT 'mart_member_profile', COUNT(*), MAX(updated_at)
    FROM `{PROJECT}.{DATASET}.mart_member_profile`
    UNION ALL
    SELECT 'risk_member_score', COUNT(*), MAX(updated_at)
    FROM `{PROJECT}.{DATASET}.risk_member_score`
    """
    return _safe_query(sql)


def _build_brief(kpis: pd.Series | None, trend: pd.DataFrame, risk: pd.DataFrame) -> str:
    if kpis is None:
        return "目前尚未读取到经营数据，请先确认数据同步与 BigQuery 表是否正常。"
    report_date = kpis.get("report_date", "-")
    turnover = _fmt_num(kpis.get("turnover"))
    profit = _fmt_num(kpis.get("profit_loss"))
    active = _fmt_num(kpis.get("active_members"))
    high_risk = _fmt_num(kpis.get("high_risk_members"))
    high_value = _fmt_num(kpis.get("high_value_members"))

    trend_text = ""
    if len(trend) >= 2:
        last = trend.iloc[-1]
        prev = trend.iloc[-2]
        prev_turnover = float(prev.get("turnover") or 0)
        last_turnover = float(last.get("turnover") or 0)
        if prev_turnover:
            change = (last_turnover - prev_turnover) / prev_turnover
            direction = "增长" if change >= 0 else "下降"
            trend_text = f"较前一日流水{direction} {abs(change) * 100:.2f}%。"

    risk_text = ""
    if not risk.empty:
        top = risk.sort_values("members", ascending=False).head(1).iloc[0]
        risk_text = f"当前会员风险分布以「{top.get('风险等级','-')}」为主。"

    return (
        f"最新经营日为 {report_date}，总流水 {turnover}，会员盈亏 {profit}，活跃会员 {active} 人。"
        f"当前高风险会员 {high_risk} 人，高价值会员 {high_value} 人。{trend_text}{risk_text}"
        "建议优先查看风控中心的高风险会员排行，并结合会员360确认投注偏好、近期注单与风险标签。"
    )


def render_home_page() -> None:
    st.title("博彩智能决策平台")
    st.caption("首页 · 经营概况 · 风险摘要 · 快捷入口")

    kpi_df = _load_home_kpis()
    trend = _load_daily_trend(14)
    risk_dist = _load_risk_dist()
    kpis = None if kpi_df.empty else kpi_df.iloc[0]

    _section("今日经营概况", "以最新投注日作为今日经营日。")
    cols = st.columns(4)
    if kpis is not None:
        with cols[0]:
            _metric_card("今日流水", _fmt_num(kpis.get("turnover")), f"经营日：{kpis.get('report_date', '-')}")
        with cols[1]:
            _metric_card("今日有效投注", _fmt_num(kpis.get("valid_turnover")), "用于会员与风险分析")
        with cols[2]:
            _metric_card("今日会员盈亏", _fmt_num(kpis.get("profit_loss")), "正数代表会员赢，负数代表会员输")
        with cols[3]:
            _metric_card("活跃会员", _fmt_num(kpis.get("active_members")), f"下注笔数：{_fmt_num(kpis.get('bet_count'))}")

        cols2 = st.columns(4)
        with cols2[0]:
            _metric_card("会员总数", _fmt_num(kpis.get("profile_members")), "来自会员画像主表")
        with cols2[1]:
            _metric_card("高价值会员", _fmt_num(kpis.get("high_value_members")), "Whale / 高价值")
        with cols2[2]:
            _metric_card("高风险会员", _fmt_num(kpis.get("high_risk_members")), "Critical + High")
        with cols2[3]:
            _metric_card("平均风险分", _fmt_num(kpis.get("avg_risk_score"), 1), "来自风控评分表")
    else:
        st.warning("暂无首页 KPI 数据，请确认 fact_member_daily_v2、mart_member_profile、risk_member_score 是否已建立。")

    st.markdown("---")
    _section("AI经营摘要", "当前为规则摘要，后续可接入 AI 模型生成。")
    st.info(_build_brief(kpis, trend, risk_dist))

    st.markdown("---")
    _section("快捷入口")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.success("会员中心\n\n搜索会员、查看画像、投注偏好与近期注单。")
    with c2:
        st.warning("风控中心\n\n查看高风险会员、风险等级与命中规则。")
    with c3:
        st.info("总裁驾驶舱\n\n查看平台经营趋势、风险排行与经营摘要。")
    with c4:
        st.write("系统管理\n\n查看数据同步状态与表更新时间。")

    st.markdown("---")
    _section("今日预警")
    alerts: list[str] = []
    if kpis is not None:
        if float(kpis.get("high_risk_members") or 0) > 0:
            alerts.append(f"🔴 高风险会员：{_fmt_num(kpis.get('high_risk_members'))} 人")
        if float(kpis.get("critical_members") or 0) > 0:
            alerts.append(f"🔴 极高风险会员：{_fmt_num(kpis.get('critical_members'))} 人")
        if float(kpis.get("profit_loss") or 0) > 0:
            alerts.append(f"🟠 今日会员整体盈利：{_fmt_num(kpis.get('profit_loss'))}，建议查看高额赢家。")
        if float(kpis.get("high_value_members") or 0) > 0:
            alerts.append(f"🟢 高价值会员：{_fmt_num(kpis.get('high_value_members'))} 人，可由 VIP 团队重点维护。")
    if alerts:
        for item in alerts:
            st.write(item)
    else:
        st.write("🟢 暂无重大预警。")

    st.markdown("---")
    _section("系统状态")
    status = _load_table_status()
    if not status.empty:
        st.dataframe(status, use_container_width=True, hide_index=True)


def render_executive_dashboard() -> None:
    st.title("总裁驾驶舱")
    st.caption("经营趋势 · 风险分布 · 会员排行 · 决策摘要")

    kpi_df = _load_home_kpis()
    trend = _load_daily_trend(30)
    risk_dist = _load_risk_dist()
    top_risk = _load_top_risk(20)
    top_members = _load_top_members(20)
    kpis = None if kpi_df.empty else kpi_df.iloc[0]

    _section("经营总览")
    cols = st.columns(5)
    if kpis is not None:
        with cols[0]: _metric_card("最新经营日", str(kpis.get("report_date", "-")), "数据仓库最新日期")
        with cols[1]: _metric_card("流水", _fmt_num(kpis.get("turnover")), "今日投注金额")
        with cols[2]: _metric_card("有效投注", _fmt_num(kpis.get("valid_turnover")), "用于结算分析")
        with cols[3]: _metric_card("会员盈亏", _fmt_num(kpis.get("profit_loss")), "正数会员赢，负数会员输")
        with cols[4]: _metric_card("高风险", _fmt_num(kpis.get("high_risk_members")), "Critical + High")

    st.markdown("---")
    _section("经营趋势", "最近 30 个有数据日期。")
    if not trend.empty:
        t1, t2 = st.columns(2)
        with t1:
            fig = px.line(trend, x="report_date", y="turnover", markers=True, title="流水趋势")
            st.plotly_chart(fig, use_container_width=True)
        with t2:
            fig = px.line(trend, x="report_date", y="profit_loss", markers=True, title="会员盈亏趋势")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    _section("风险分布")
    if not risk_dist.empty:
        c1, c2 = st.columns([1, 1])
        with c1:
            fig = px.bar(risk_dist, x="风险等级", y="members", text="members", title="风险等级会员数")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.dataframe(risk_dist[["风险等级", "members", "avg_score"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    _section("高风险会员排行")
    if not top_risk.empty:
        show = top_risk.copy()
        for col in ["有效投注", "盈亏"]:
            if col in show.columns:
                show[col] = show[col].map(lambda x: _fmt_num(x))
        if "RTP" in show.columns:
            show["RTP"] = show["RTP"].map(_fmt_pct)
        st.dataframe(show, use_container_width=True, hide_index=True)

    st.markdown("---")
    _section("高流水会员排行")
    if not top_members.empty:
        show = top_members.copy()
        for col in ["有效投注", "盈亏"]:
            if col in show.columns:
                show[col] = show[col].map(lambda x: _fmt_num(x))
        if "RTP" in show.columns:
            show["RTP"] = show["RTP"].map(_fmt_pct)
        st.dataframe(show, use_container_width=True, hide_index=True)

    st.markdown("---")
    _section("AI经营建议")
    st.info(_build_brief(kpis, trend, risk_dist))


def render_version_page() -> None:
    st.title("版本信息")
    st.write("当前版本：v1.2.0")
    st.write("本次更新：新增首页、总裁驾驶舱、经营摘要、系统状态与排行榜入口。")
    st.write("数据来源：fact_member_daily_v2、mart_member_profile、risk_member_score。")
