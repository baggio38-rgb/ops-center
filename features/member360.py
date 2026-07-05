"""会员360 Pro 页面（v1.4 Sprint 1）。

目标：客服、VIP、风控人员输入会员账号后，30 秒内完成会员判断。
资料来源：
- mart_member_profile：会员画像主表
- risk_member_score：风险评分
- fact_member_daily_v2：会员每日趋势
- raw_bet_detail：近期投注与偏好明细
"""

from __future__ import annotations

import re
from html import escape
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from components.ui import apply_theme, hero, metric_card, section, brief, score_card
except Exception:  # 兼容旧版本项目
    apply_theme = lambda: None

    def hero(title: str, subtitle: str, version: str = "v1.4.0") -> None:
        st.title(title)
        st.caption(f"{subtitle} · {version}")

    def section(title: str, subtitle: str = "") -> None:
        st.markdown(f"### {title}")
        if subtitle:
            st.caption(subtitle)

    def brief(lines: list[str]) -> None:
        st.info("\n".join(lines))

    def score_card(title: str, score: int, note: str = "") -> None:
        st.metric(title, score, note)

    def metric_card(title: str, value: str, note: str = "", delta: Any = None, icon: str = "") -> None:
        st.metric(f"{icon} {title}".strip(), value, note)

from services.bigquery_client import query_bq

PROJECT = "mydata-494606"
DATASET = "mydata"


def _escape_sql(value: str) -> str:
    return value.replace("'", "''")


def _member_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value.strip()).upper()


def _is_null(value: Any) -> bool:
    try:
        return value is None or pd.isna(value)
    except Exception:
        return value is None


def _num(value: Any, default: float = 0.0) -> float:
    if _is_null(value):
        return default
    try:
        return float(value)
    except Exception:
        return default


def _fmt_num(value: Any, digits: int = 0) -> str:
    if _is_null(value):
        return "-"
    try:
        n = float(value)
    except Exception:
        return str(value)
    if abs(n) >= 100000000:
        return f"{n / 100000000:,.2f}亿"
    if abs(n) >= 10000:
        return f"{n / 10000:,.2f}万"
    if digits == 0:
        return f"{n:,.0f}"
    return f"{n:,.{digits}f}"


def _fmt_pct(value: Any, digits: int = 2) -> str:
    if _is_null(value):
        return "-"
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except Exception:
        return "-"


def _safe_query(sql: str) -> pd.DataFrame:
    try:
        return query_bq(sql)
    except Exception as exc:
        st.error(f"查询失败：{exc}")
        return pd.DataFrame()


def _risk_color(level: str | None) -> str:
    return {
        "Critical": "#dc2626",
        "High": "#ea580c",
        "Medium": "#ca8a04",
        "Low": "#16a34a",
        "Normal": "#64748b",
    }.get(str(level or "Normal"), "#64748b")


def _risk_cn(level: str | None) -> str:
    return {
        "Critical": "极高风险",
        "High": "高风险",
        "Medium": "中风险",
        "Low": "低风险",
        "Normal": "正常",
    }.get(str(level or "Normal"), str(level or "正常"))


def _pill(text: str, bg: str = "#eef2ff", color: str = "#3730a3") -> str:
    return (
        f"<span style='display:inline-block;background:{bg};color:{color};"
        f"border-radius:999px;padding:5px 10px;margin:3px;font-size:13px;font-weight:700;'>"
        f"{escape(text)}</span>"
    )


def _load_member(keyword: str) -> pd.DataFrame:
    key = _member_key(keyword)
    raw = _escape_sql(keyword.strip())
    sql = f"""
    SELECT
      p.*,
      r.risk_score,
      r.risk_level,
      r.rtp_score,
      r.turnover_score,
      r.night_score,
      r.provider_score,
      r.profit_score,
      r.tag_score
    FROM `{PROJECT}.{DATASET}.mart_member_profile` p
    LEFT JOIN `{PROJECT}.{DATASET}.risk_member_score` r
      ON p.member_key = r.member_key
    WHERE p.member_key = '{key}'
       OR LOWER(p.member_id) = LOWER('{raw}')
       OR LOWER(p.member_id) LIKE LOWER('%{raw}%')
    ORDER BY p.valid_turnover DESC
    LIMIT 30
    """
    return _safe_query(sql)


def _load_daily(member_key: str, days: int) -> pd.DataFrame:
    sql = f"""
    SELECT
      report_date,
      bet_count,
      turnover,
      valid_turnover,
      profit_loss,
      rtp,
      roi,
      avg_bet,
      max_bet,
      active_minutes
    FROM `{PROJECT}.{DATASET}.fact_member_daily_v2`
    WHERE member_key = '{_escape_sql(member_key)}'
      AND report_date >= DATE_SUB((SELECT MAX(report_date) FROM `{PROJECT}.{DATASET}.fact_member_daily_v2`), INTERVAL {int(days)} DAY)
    ORDER BY report_date
    """
    return _safe_query(sql)


def _load_category_mix(member_key: str) -> pd.DataFrame:
    sql = f"""
    SELECT
      IFNULL(`场馆类型`, '未知') AS `游戏类型`,
      SUM(SAFE_CAST(`有效投注` AS FLOAT64)) AS `有效投注`,
      COUNT(*) AS `注单数`
    FROM `{PROJECT}.{DATASET}.raw_bet_detail`
    WHERE UPPER(REGEXP_REPLACE(TRIM(`会员账号`), r'[^A-Za-z0-9]', '')) = '{_escape_sql(member_key)}'
    GROUP BY `游戏类型`
    ORDER BY `有效投注` DESC
    LIMIT 10
    """
    return _safe_query(sql)


def _load_recent_bets(member_key: str, limit: int = 80) -> pd.DataFrame:
    sql = f"""
    SELECT
      `下注时间`,
      `场馆名称`,
      `游戏名称`,
      `场馆类型`,
      SAFE_CAST(`下注金额` AS FLOAT64) AS `下注金额`,
      SAFE_CAST(`有效投注` AS FLOAT64) AS `有效投注`,
      SAFE_CAST(`盈亏` AS FLOAT64) AS `盈亏`,
      `玩法`,
      `状态`,
      `注单流水号`
    FROM `{PROJECT}.{DATASET}.raw_bet_detail`
    WHERE UPPER(REGEXP_REPLACE(TRIM(`会员账号`), r'[^A-Za-z0-9]', '')) = '{_escape_sql(member_key)}'
    ORDER BY PARSE_DATETIME('%Y-%m-%d %H:%M:%S', `下注时间`) DESC
    LIMIT {int(limit)}
    """
    return _safe_query(sql)


def _calc_value_score(row: pd.Series) -> int:
    valid = _num(row.get("valid_turnover"))
    active_days = _num(row.get("active_days"))
    deposit = _num(row.get("deposit"))
    score = 0
    if valid >= 5000000:
        score += 55
    elif valid >= 1000000:
        score += 42
    elif valid >= 300000:
        score += 28
    elif valid >= 50000:
        score += 16
    else:
        score += 8
    if active_days >= 20:
        score += 22
    elif active_days >= 10:
        score += 15
    elif active_days >= 3:
        score += 8
    if deposit >= 1000000:
        score += 20
    elif deposit >= 300000:
        score += 12
    elif deposit > 0:
        score += 6
    tags = str(row.get("auto_tags") or "")
    if "VIP" in tags:
        score += 8
    return min(score, 100)


def _calc_loyalty_score(row: pd.Series) -> int:
    active_days = _num(row.get("active_days"))
    bet_count = _num(row.get("bet_count"))
    avg_daily = _num(row.get("avg_bets_per_day"))
    score = 20
    score += min(int(active_days * 3), 35)
    if bet_count >= 1000:
        score += 20
    elif bet_count >= 300:
        score += 14
    elif bet_count >= 50:
        score += 8
    if avg_daily >= 100:
        score += 15
    elif avg_daily >= 30:
        score += 10
    elif avg_daily >= 5:
        score += 5
    if not _is_null(row.get("last_login_time")):
        score += 10
    return min(score, 100)


def _score_label(score: int) -> str:
    if score >= 85:
        return "★★★★★"
    if score >= 70:
        return "★★★★☆"
    if score >= 50:
        return "★★★☆☆"
    if score >= 30:
        return "★★☆☆☆"
    return "★☆☆☆☆"


def _build_ai_summary(row: pd.Series, daily: pd.DataFrame | None = None) -> list[str]:
    lines: list[str] = []
    category = row.get("favorite_category") or "未知类型"
    provider = row.get("favorite_provider") or "未知场馆"
    game = row.get("favorite_game") or "未知游戏"
    hour = row.get("favorite_hour")
    valid = _fmt_num(row.get("valid_turnover"))
    profit = _num(row.get("profit_loss"))
    risk_score = int(_num(row.get("risk_score")))
    risk_level = _risk_cn(row.get("risk_level"))
    value_score = _calc_value_score(row)

    lines.append(f"该会员累计有效投注 {valid}，主要投注 {category}，偏好场馆为 {provider}，常玩游戏为 {game}。")
    if not _is_null(hour):
        lines.append(f"常见投注时段集中在 {int(_num(hour))}:00 左右，可作为客服联系与活动推送参考。")
    if profit < 0:
        lines.append(f"目前会员累计亏损 {_fmt_num(abs(profit))}，公司侧整体为盈利状态。")
    elif profit > 0:
        lines.append(f"目前会员累计盈利 {_fmt_num(profit)}，建议结合风险分与近期注单进一步观察。")
    if daily is not None and len(daily) >= 2:
        recent = daily.tail(7)["valid_turnover"].sum()
        prev = daily.tail(14).head(max(len(daily.tail(14)) - len(daily.tail(7)), 0))["valid_turnover"].sum()
        if prev > 0:
            growth = (recent - prev) / prev
            if growth >= 0.2:
                lines.append(f"近 7 天有效投注较前期增加 {growth * 100:.1f}%，活跃度正在上升。")
            elif growth <= -0.2:
                lines.append(f"近 7 天有效投注较前期下降 {abs(growth) * 100:.1f}%，建议关注是否有流失迹象。")
    if risk_score >= 60:
        lines.append(f"当前风险等级为 {risk_level}，建议风控优先查看风险原因与近期大额注单。")
    elif value_score >= 85:
        lines.append("会员价值较高，建议 VIP 或客服持续维护。")
    else:
        lines.append("当前未发现明显高风险信号，可继续观察投注与存提变化。")
    return lines


def _render_profile_header(row: pd.Series) -> None:
    risk_score = int(_num(row.get("risk_score")))
    risk_level = row.get("risk_level") or "Normal"
    value_score = _calc_value_score(row)
    loyalty_score = _calc_loyalty_score(row)
    color = _risk_color(risk_level)

    st.markdown(
        f"""
        <div style="border:1px solid #e5e7eb;border-radius:22px;padding:20px 22px;background:linear-gradient(135deg,#ffffff,#f8fafc);box-shadow:0 4px 14px rgba(15,23,42,.06);">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap;">
            <div>
              <div style="font-size:32px;font-weight:950;color:#0f172a;line-height:1.1;">👤 {escape(str(row.get('member_id') or '-'))}</div>
              <div style="margin-top:10px;color:#475569;font-size:14px;">
                VIP：<b>{escape(str(row.get('vip_level') or '-'))}</b>　｜　代理：<b>{escape(str(row.get('agent_name') or '-'))}</b>　｜　状态：<b>{escape(str(row.get('member_status') or '-'))}</b>
              </div>
              <div style="margin-top:10px;color:#64748b;font-size:13px;">
                注册：{escape(str(row.get('register_time') or '-'))}　｜　最近登录：{escape(str(row.get('last_login_time') or '-'))}　｜　最后投注：{escape(str(row.get('last_bet_time') or '-'))}
              </div>
            </div>
            <div style="min-width:260px;text-align:right;">
              <span style="background:{color};color:white;border-radius:999px;padding:7px 13px;font-weight:900;display:inline-block;">风险 {risk_score} · {escape(_risk_cn(str(risk_level)))}</span>
              <div style="margin-top:12px;color:#0f172a;font-weight:800;">价值 {value_score} {_score_label(value_score)}</div>
              <div style="margin-top:5px;color:#0f172a;font-weight:800;">忠诚 {loyalty_score} {_score_label(loyalty_score)}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_tags(row: pd.Series) -> None:
    tags = [t.strip() for t in str(row.get("auto_tags") or "").split(",") if t.strip()]
    if not tags:
        st.caption("暂无自动标签")
        return
    html = "".join(_pill(t) for t in tags)
    st.markdown(html, unsafe_allow_html=True)


def _render_scores(row: pd.Series) -> None:
    risk_score = int(_num(row.get("risk_score")))
    value_score = _calc_value_score(row)
    loyalty_score = _calc_loyalty_score(row)
    a, b, c = st.columns(3)
    with a:
        score_card("风险分", risk_score, _risk_cn(row.get("risk_level")))
    with b:
        score_card("会员价值", value_score, _score_label(value_score))
    with c:
        score_card("忠诚度", loyalty_score, _score_label(loyalty_score))


def _render_kpis(row: pd.Series) -> None:
    cols = st.columns(4)
    with cols[0]:
        metric_card("累计流水", _fmt_num(row.get("turnover")), "下注金额", icon="💰")
    with cols[1]:
        metric_card("有效投注", _fmt_num(row.get("valid_turnover")), "风控与经营核心指标", icon="🎯")
    with cols[2]:
        metric_card("会员盈亏", _fmt_num(row.get("profit_loss")), "正数会员赢，负数会员输", icon="📉")
    with cols[3]:
        metric_card("平均投注", _fmt_num(row.get("avg_bet")), "单笔平均下注", icon="🎲")

    cols2 = st.columns(4)
    with cols2[0]:
        metric_card("存款", _fmt_num(row.get("deposit")), "累计", icon="🏦")
    with cols2[1]:
        metric_card("提款", _fmt_num(row.get("withdraw")), "累计", icon="💸")
    with cols2[2]:
        metric_card("RTP", _fmt_pct(row.get("rtp")), "会员盈亏 / 有效投注", icon="⚖️")
    with cols2[3]:
        metric_card("ROI", _fmt_pct(row.get("roi")), "会员盈亏 / 流水", icon="📊")


def _render_trend(daily: pd.DataFrame) -> None:
    if daily.empty:
        st.caption("暂无每日趋势资料。")
        return
    plot_df = daily.copy()
    plot_df["report_date"] = pd.to_datetime(plot_df["report_date"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_df["report_date"], y=plot_df["valid_turnover"], name="有效投注", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=plot_df["report_date"], y=plot_df["profit_loss"], name="会员盈亏", mode="lines+markers", yaxis="y2"))
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="有效投注"),
        yaxis2=dict(title="会员盈亏", overlaying="y", side="right"),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_category_mix(cat: pd.DataFrame) -> None:
    if cat.empty:
        st.caption("暂无游戏偏好资料。")
        return
    cat = cat.copy()
    total = cat["有效投注"].sum()
    cat["占比"] = cat["有效投注"] / total if total else 0
    fig = px.bar(cat, x="有效投注", y="游戏类型", orientation="h", text=cat["占比"].map(lambda x: f"{x*100:.1f}%"))
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)


def _render_risk_reason(row: pd.Series) -> None:
    reasons = []
    if _num(row.get("rtp_score")) > 0:
        reasons.append("RTP偏高")
    if _num(row.get("turnover_score")) > 0:
        reasons.append("高流水")
    if _num(row.get("night_score")) > 0:
        reasons.append("夜间投注")
    if _num(row.get("provider_score")) > 0:
        reasons.append("真人场馆偏好")
    if _num(row.get("profit_score")) > 0:
        reasons.append("公司亏损较高")
    if _num(row.get("tag_score")) > 0:
        reasons.append("命中风险标签")
    if not reasons:
        st.success("当前未命中主要风控规则。")
        return
    st.warning("、".join(reasons))


def render_member360() -> None:
    apply_theme()
    hero("会员360 Pro", "客服、VIP、风控人员用于 30 秒内完成会员判断。", version="v1.4.0")

    keyword = st.text_input("🔍 搜索会员", placeholder="请输入会员账号，例如 sun007007", key="member360_pro_keyword")
    if not keyword.strip():
        st.info("请输入会员账号后查询。")
        return

    result = _load_member(keyword)
    if result.empty:
        st.warning("查无此会员。请确认账号是否正确，或该会员是否已有投注资料。")
        return

    if len(result) > 1:
        choices = result["member_id"].astype(str).tolist()
        selected = st.selectbox("找到多笔相似会员，请选择", choices)
        row = result[result["member_id"].astype(str) == selected].iloc[0]
    else:
        row = result.iloc[0]

    member_key = str(row.get("member_key"))
    period = st.segmented_control("趋势区间", options=[7, 30, 90], default=30, format_func=lambda x: f"近{x}天")
    daily = _load_daily(member_key, int(period or 30))

    _render_profile_header(row)

    section("一眼判断", "风险、价值、忠诚三项核心评分。")
    _render_scores(row)

    left, right = st.columns([0.64, 0.36])
    with left:
        section("AI会员摘要", "规则版摘要，后续可直接升级为大模型摘要。")
        brief(_build_ai_summary(row, daily))
    with right:
        section("自动标签", "系统根据投注、风险、价值自动产生。")
        _render_tags(row)
        st.markdown("##### 风险原因")
        _render_risk_reason(row)

    section("核心KPI", "会员资金、投注、RTP、ROI。")
    _render_kpis(row)

    section("趋势与偏好", "最近趋势与游戏类型偏好。")
    c1, c2 = st.columns([0.58, 0.42])
    with c1:
        _render_trend(daily)
    with c2:
        cat = _load_category_mix(member_key)
        _render_category_mix(cat)
        st.markdown(
            f"""
            <div style="font-size:13px;color:#475569;line-height:1.9;">
            最常场馆：<b>{escape(str(row.get('favorite_provider') or '-'))}</b><br>
            最常游戏：<b>{escape(str(row.get('favorite_game') or '-'))}</b><br>
            最常类型：<b>{escape(str(row.get('favorite_category') or '-'))}</b><br>
            最常时段：<b>{_fmt_num(row.get('favorite_hour'))} 点</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    section("最近投注", "最近 80 笔注单，可搜索、排序，并可由 Streamlit 下载。")
    bets = _load_recent_bets(member_key, 80)
    if bets.empty:
        st.caption("暂无近期注单。")
    else:
        q = st.text_input("筛选近期注单", placeholder="输入场馆、游戏、玩法或状态", key="member360_bet_filter")
        view = bets.copy()
        if q.strip():
            mask = view.astype(str).apply(lambda col: col.str.contains(q.strip(), case=False, na=False)).any(axis=1)
            view = view[mask]
        st.dataframe(view, use_container_width=True, hide_index=True)
        csv = view.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下载当前注单CSV", csv, file_name=f"member_bets_{member_key}.csv", mime="text/csv")

    with st.expander("字段明细 / 调试资料"):
        detail = pd.DataFrame({"字段": row.index.astype(str), "值": [row.get(c) for c in row.index]})
        st.dataframe(detail, use_container_width=True, hide_index=True)
