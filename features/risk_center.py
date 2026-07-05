"""风控中心 MVP 页面。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from services.bigquery_client import query_bq

PROJECT = "mydata-494606"
DATASET = "mydata"

RISK_ORDER = ["Critical", "High", "Medium", "Low", "Normal"]
RISK_LABELS = {
    "Critical": "极高风险",
    "High": "高风险",
    "Medium": "中风险",
    "Low": "低风险",
    "Normal": "正常",
}
RISK_COLORS = {
    "Critical": "#dc2626",
    "High": "#ea580c",
    "Medium": "#ca8a04",
    "Low": "#16a34a",
    "Normal": "#64748b",
}

SCORE_REASON_MAP = [
    ("rtp_score", "RTP异常"),
    ("turnover_score", "高流水"),
    ("night_score", "夜间投注"),
    ("provider_score", "真人场馆偏好"),
    ("profit_score", "公司亏损"),
    ("tag_score", "命中风险标签"),
]


def _fmt_num(value: Any, digits: int = 0) -> str:
    if value is None or pd.isna(value):
        return "-"
    try:
        n = float(value)
    except Exception:
        return str(value)
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


def _card(title: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div style="border:1px solid #e5e7eb;border-radius:14px;padding:14px 16px;background:#fff;box-shadow:0 1px 3px rgba(15,23,42,.06);">
          <div style="font-size:13px;color:#64748b;margin-bottom:6px;">{title}</div>
          <div style="font-size:26px;font-weight:800;color:#0f172a;line-height:1.15;">{value}</div>
          <div style="font-size:12px;color:#64748b;margin-top:4px;">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _risk_badge(level: str | None, score: Any) -> str:
    level = str(level or "Normal")
    color = RISK_COLORS.get(level, "#64748b")
    label = RISK_LABELS.get(level, level)
    return (
        f"<span style='background:{color};color:white;border-radius:999px;"
        f"padding:4px 10px;font-weight:700;'>风险 {int(float(score or 0))} · {label}</span>"
    )


def _reason_from_row(row: pd.Series) -> str:
    reasons: list[str] = []
    for col, label in SCORE_REASON_MAP:
        try:
            if float(row.get(col) or 0) > 0:
                reasons.append(label)
        except Exception:
            pass
    return "，".join(reasons) if reasons else "未命中明显风险规则"


@st.cache_data(ttl=300, show_spinner=False)
def _load_distribution() -> pd.DataFrame:
    sql = f"""
    SELECT
      risk_level,
      COUNT(*) AS members,
      AVG(risk_score) AS avg_score,
      MAX(risk_score) AS max_score
    FROM `{PROJECT}.{DATASET}.risk_member_score`
    GROUP BY risk_level
    """
    df = _safe_query(sql)
    if df.empty:
        return df
    df["risk_level"] = pd.Categorical(df["risk_level"], categories=RISK_ORDER, ordered=True)
    return df.sort_values("risk_level")


@st.cache_data(ttl=300, show_spinner=False)
def _load_top_risk(levels: list[str], min_score: int, limit: int) -> pd.DataFrame:
    level_sql = ",".join([f"'{x}'" for x in levels]) if levels else "'Critical','High','Medium','Low','Normal'"
    sql = f"""
    SELECT
      r.member_key,
      r.member_id,
      p.vip_level,
      p.agent_name,
      p.value_level,
      r.risk_level,
      r.risk_score,
      r.rtp_score,
      r.turnover_score,
      r.night_score,
      r.provider_score,
      r.profit_score,
      r.tag_score,
      r.valid_turnover,
      r.profit_loss,
      r.rtp,
      r.roi,
      r.favorite_provider,
      p.favorite_game,
      p.favorite_category,
      r.favorite_hour,
      r.auto_tags
    FROM `{PROJECT}.{DATASET}.risk_member_score` r
    LEFT JOIN `{PROJECT}.{DATASET}.mart_member_profile` p
      ON r.member_key = p.member_key
    WHERE r.risk_level IN ({level_sql})
      AND r.risk_score >= {int(min_score)}
    ORDER BY r.risk_score DESC, r.valid_turnover DESC
    LIMIT {int(limit)}
    """
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def _load_score_buckets() -> pd.DataFrame:
    sql = f"""
    SELECT
      CASE
        WHEN risk_score >= 80 THEN '80-100'
        WHEN risk_score >= 60 THEN '60-79'
        WHEN risk_score >= 40 THEN '40-59'
        WHEN risk_score >= 20 THEN '20-39'
        ELSE '0-19'
      END AS score_bucket,
      COUNT(*) AS members
    FROM `{PROJECT}.{DATASET}.risk_member_score`
    GROUP BY score_bucket
    ORDER BY score_bucket DESC
    """
    return _safe_query(sql)


def _render_distribution() -> None:
    dist = _load_distribution()
    if dist.empty:
        st.warning("尚未建立 risk_member_score，或目前没有风险资料。")
        return

    totals = {str(r["risk_level"]): int(r["members"]) for _, r in dist.iterrows()}
    cols = st.columns(5)
    for idx, level in enumerate(RISK_ORDER):
        with cols[idx]:
            _card(RISK_LABELS[level], _fmt_num(totals.get(level, 0)), level)

    chart_df = dist.copy()
    chart_df["风险等级"] = chart_df["risk_level"].map(RISK_LABELS)
    fig = px.bar(chart_df, x="风险等级", y="members", text="members", title="风险等级分布")
    fig.update_layout(height=330, xaxis_title="", yaxis_title="会员数")
    st.plotly_chart(fig, use_container_width=True)


def _render_top_table() -> None:
    st.markdown("### 高风险会员排行")
    c1, c2, c3 = st.columns([0.45, 0.25, 0.30])
    with c1:
        levels = st.multiselect(
            "风险等级",
            RISK_ORDER,
            default=["Critical", "High", "Medium"],
            format_func=lambda x: RISK_LABELS.get(x, x),
        )
    with c2:
        min_score = st.slider("最低风险分", 0, 100, 30, 5)
    with c3:
        limit = st.selectbox("显示笔数", [20, 50, 100, 200], index=1)

    df = _load_top_risk(levels, min_score, limit)
    if df.empty:
        st.info("目前没有符合条件的会员。")
        return

    df = df.copy()
    df["风险原因"] = df.apply(_reason_from_row, axis=1)
    show_cols = [
        "member_id", "vip_level", "agent_name", "risk_level", "risk_score", "风险原因",
        "valid_turnover", "profit_loss", "rtp", "roi", "favorite_provider", "favorite_game", "favorite_category", "auto_tags",
    ]
    rename = {
        "member_id": "会员账号",
        "vip_level": "VIP等级",
        "agent_name": "代理",
        "risk_level": "风险等级",
        "risk_score": "风险分",
        "valid_turnover": "有效投注",
        "profit_loss": "会员盈亏",
        "rtp": "RTP",
        "roi": "ROI",
        "favorite_provider": "偏好场馆",
        "favorite_game": "偏好游戏",
        "favorite_category": "偏好类型",
        "auto_tags": "自动标签",
    }
    display = df[[c for c in show_cols if c in df.columns]].rename(columns=rename)
    st.dataframe(display, use_container_width=True, hide_index=True)

    selected = st.selectbox("选择会员查看风险详情", df["member_id"].astype(str).tolist())
    row = df[df["member_id"].astype(str) == selected].iloc[0]
    st.markdown("### 会员风险详情")
    left, right = st.columns([0.65, 0.35])
    with left:
        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb;border-radius:18px;padding:18px;background:linear-gradient(135deg,#ffffff,#f8fafc);">
              <div style="font-size:26px;font-weight:900;color:#0f172a;">{row.get('member_id')}</div>
              <div style="margin-top:8px;color:#475569;">VIP：<b>{row.get('vip_level') or '-'}</b> ｜ 代理：<b>{row.get('agent_name') or '-'}</b></div>
              <div style="margin-top:10px;">{_risk_badge(row.get('risk_level'), row.get('risk_score'))}</div>
              <div style="margin-top:14px;color:#334155;">风险原因：<b>{_reason_from_row(row)}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        _card("有效投注", _fmt_num(row.get("valid_turnover")))
        _card("会员盈亏", _fmt_num(row.get("profit_loss")))

    score_cols = ["rtp_score", "turnover_score", "night_score", "provider_score", "profit_score", "tag_score"]
    score_labels = {
        "rtp_score": "RTP分",
        "turnover_score": "流水分",
        "night_score": "夜间分",
        "provider_score": "场馆分",
        "profit_score": "盈亏分",
        "tag_score": "标签分",
    }
    score_df = pd.DataFrame({
        "项目": [score_labels[c] for c in score_cols],
        "分数": [float(row.get(c) or 0) for c in score_cols],
    })
    fig = px.bar(score_df, x="项目", y="分数", text="分数", title="风险分组成")
    fig.update_layout(height=320, xaxis_title="", yaxis_title="分数")
    st.plotly_chart(fig, use_container_width=True)

    st.caption("提示：要查看会员完整画像，请到「会员价值 → 会员360」输入该会员账号。")


def render_risk_overview() -> None:
    st.title("🛡 风控中心 · 风险总览")
    st.caption("用于最高决策层、风控主管快速查看当前会员风险分布与高风险名单。资料来源：risk_member_score、mart_member_profile。")
    _render_distribution()
    st.divider()
    _render_top_table()


def render_risk_rules() -> None:
    st.title("🛡 风控中心 · 规则说明")
    st.caption("当前为第一版规则引擎，后续可升级为可配置规则表。")
    rules = pd.DataFrame([
        {"规则": "RTP异常", "条件": "RTP >= 100% / 98% / 95%", "分数": "40 / 25 / 10"},
        {"规则": "高流水", "条件": "有效投注 >= 500万 / 100万 / 50万", "分数": "20 / 10 / 5"},
        {"规则": "夜间投注", "条件": "最常投注时段为 0-6 点", "分数": "10"},
        {"规则": "真人场馆偏好", "条件": "偏好场馆命中 Evolution / Pragmatic / Asia / Sexy / WM / DG", "分数": "10"},
        {"规则": "公司亏损", "条件": "会员盈亏 <= -50万 / -10万", "分数": "20 / 10"},
        {"规则": "风险标签", "条件": "自动标签命中 VIP / 高流水 / 高额提款 / 套利 / 高风险 / 洗码", "分数": "10"},
    ])
    st.dataframe(rules, use_container_width=True, hide_index=True)
