"""会员360页面。"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from services.bigquery_client import query_bq


PROJECT = "mydata-494606"
DATASET = "mydata"


def _escape_sql(value: str) -> str:
    return value.replace("'", "\\'")


def _member_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value.strip()).upper()


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


def _risk_badge(level: str | None, score: Any) -> str:
    level = (level or "Normal").strip()
    color = {
        "Critical": "#dc2626",
        "High": "#ea580c",
        "Medium": "#ca8a04",
        "Low": "#16a34a",
        "Normal": "#64748b",
    }.get(level, "#64748b")
    return f"<span style='background:{color};color:white;border-radius:999px;padding:4px 10px;font-weight:700;'>风险 {int(score or 0)} · {level}</span>"


def _card(title: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div style="border:1px solid #e5e7eb;border-radius:14px;padding:14px 16px;background:#ffffff;box-shadow:0 1px 3px rgba(15,23,42,.06);">
          <div style="font-size:13px;color:#64748b;margin-bottom:6px;">{title}</div>
          <div style="font-size:26px;font-weight:800;color:#0f172a;line-height:1.15;">{value}</div>
          <div style="font-size:12px;color:#64748b;margin-top:4px;">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _safe_query(sql: str) -> pd.DataFrame:
    try:
        return query_bq(sql)
    except Exception as exc:
        st.error(f"查询失败：{exc}")
        return pd.DataFrame()


def _load_member(keyword: str) -> pd.DataFrame:
    k = _member_key(keyword)
    raw = _escape_sql(keyword.strip())
    sql = f"""
    SELECT
      p.*,
      r.risk_score,
      r.risk_level
    FROM `{PROJECT}.{DATASET}.mart_member_profile` p
    LEFT JOIN `{PROJECT}.{DATASET}.risk_member_score` r
      ON p.member_key = r.member_key
    WHERE p.member_key = '{k}'
       OR LOWER(p.member_id) = LOWER('{raw}')
       OR LOWER(p.member_id) LIKE LOWER('%{raw}%')
    ORDER BY p.valid_turnover DESC
    LIMIT 20
    """
    return _safe_query(sql)


def _load_daily(member_key: str) -> pd.DataFrame:
    sql = f"""
    SELECT
      report_date,
      bet_count,
      turnover,
      valid_turnover,
      profit_loss,
      rtp,
      roi,
      active_minutes
    FROM `{PROJECT}.{DATASET}.fact_member_daily_v2`
    WHERE member_key = '{_escape_sql(member_key)}'
    ORDER BY report_date
    """
    return _safe_query(sql)


def _load_recent_bets(member_key: str) -> pd.DataFrame:
    sql = f"""
    SELECT
      `下注时间` AS `下注时间`,
      `场馆名称` AS `场馆名称`,
      `游戏名称` AS `游戏名称`,
      `场馆类型` AS `场馆类型`,
      SAFE_CAST(`下注金额` AS FLOAT64) AS `下注金额`,
      SAFE_CAST(`有效投注` AS FLOAT64) AS `有效投注`,
      SAFE_CAST(`盈亏` AS FLOAT64) AS `盈亏`,
      `状态` AS `状态`,
      `注单流水号` AS `注单流水号`
    FROM `{PROJECT}.{DATASET}.raw_bet_detail`
    WHERE UPPER(REGEXP_REPLACE(TRIM(`会员账号`), r'[^A-Za-z0-9]', '')) = '{_escape_sql(member_key)}'
    ORDER BY PARSE_DATETIME('%Y-%m-%d %H:%M:%S', `下注时间`) DESC
    LIMIT 50
    """
    return _safe_query(sql)


def _render_member_header(row: pd.Series) -> None:
    st.markdown("### 👤 会员360")
    left, right = st.columns([0.72, 0.28])
    with left:
        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb;border-radius:18px;padding:18px;background:linear-gradient(135deg,#ffffff,#f8fafc);">
              <div style="font-size:28px;font-weight:900;color:#0f172a;">{row.get('member_id','-')}</div>
              <div style="margin-top:8px;color:#475569;">
                VIP：<b>{row.get('vip_level') or '-'}</b>　｜　代理：<b>{row.get('agent_name') or '-'}</b>　｜　状态：<b>{row.get('member_status') or '-'}</b>
              </div>
              <div style="margin-top:10px;color:#64748b;font-size:13px;">
                注册时间：{row.get('register_time') or '-'}　｜　最后登录：{row.get('last_login_time') or '-'}　｜　最后下注：{row.get('last_bet_time') or '-'}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(_risk_badge(row.get("risk_level"), row.get("risk_score")), unsafe_allow_html=True)
        st.markdown(f"**价值等级：** {row.get('value_level') or '-'}")
        st.markdown(f"**价值分：** {_fmt_num(row.get('value_score'))}")


def _render_tags(row: pd.Series) -> None:
    tags = str(row.get("auto_tags") or "").split(",")
    tags = [t.strip() for t in tags if t.strip()]
    if not tags:
        st.caption("暂无自动标签")
        return
    html = "".join(
        f"<span style='display:inline-block;background:#eef2ff;color:#3730a3;border-radius:999px;padding:5px 10px;margin:3px;font-size:13px;font-weight:600;'>{t}</span>"
        for t in tags
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_ai_summary(row: pd.Series) -> None:
    risk_level = row.get("risk_level") or "Normal"
    level_cn = {
        "Critical": "极高风险",
        "High": "高风险",
        "Medium": "中风险",
        "Low": "低风险",
        "Normal": "正常",
    }.get(str(risk_level), str(risk_level))
    summary = (
        f"该会员累计有效投注 {_fmt_num(row.get('valid_turnover'))}，"
        f"主要偏好 {row.get('favorite_category') or '未知类型'}，"
        f"常玩场馆为 {row.get('favorite_provider') or '未知'}，"
        f"常玩游戏为 {row.get('favorite_game') or '未知'}，"
        f"常见下注时段为 {row.get('favorite_hour') if pd.notna(row.get('favorite_hour')) else '-'} 点。"
        f"当前风险等级为 {level_cn}，风险分为 {_fmt_num(row.get('risk_score'))}。"
    )
    st.info(summary)


def render_member360():
    st.title("👤 会员中心 · 会员360")
    st.caption("用于客服、VIP、风控与管理层快速了解单一会员状态。资料来源：mart_member_profile、risk_member_score、fact_member_daily_v2、raw_bet_detail。")

    keyword = st.text_input("请输入会员账号", placeholder="例如：sun007007", key="member360_keyword")
    if not keyword.strip():
        st.info("请输入会员账号后查询。")
        return

    result = _load_member(keyword)
    if result.empty:
        st.warning("查无此会员。请确认会员账号是否正确，或该会员是否已有投注资料。")
        return

    if len(result) > 1:
        st.caption("找到多笔相似会员，请选择一个。")
        choices = result["member_id"].astype(str).tolist()
        selected = st.selectbox("选择会员", choices)
        row = result[result["member_id"].astype(str) == selected].iloc[0]
    else:
        row = result.iloc[0]

    _render_member_header(row)

    st.markdown("#### 自动标签")
    _render_tags(row)

    st.markdown("#### 核心指标")
    c = st.columns(4)
    with c[0]:
        _card("有效投注", _fmt_num(row.get("valid_turnover")), "累计")
    with c[1]:
        _card("会员盈亏", _fmt_num(row.get("profit_loss")), "正数代表会员赢，负数代表会员输")
    with c[2]:
        _card("下注次数", _fmt_num(row.get("bet_count")), "累计注单")
    with c[3]:
        _card("活跃天数", _fmt_num(row.get("active_days")), "有投注的日期")

    c2 = st.columns(4)
    with c2[0]:
        _card("平均下注", _fmt_num(row.get("avg_bet")), "单笔平均")
    with c2[1]:
        _card("最大下注", _fmt_num(row.get("max_bet")), "单笔最大")
    with c2[2]:
        _card("RTP", _fmt_pct(row.get("rtp")), "盈亏 / 有效投注")
    with c2[3]:
        _card("ROI", _fmt_pct(row.get("roi")), "盈亏 / 下注金额")

    st.markdown("#### 资金概况")
    c3 = st.columns(4)
    with c3[0]:
        _card("存款", _fmt_num(row.get("deposit")))
    with c3[1]:
        _card("提款", _fmt_num(row.get("withdraw")))
    with c3[2]:
        _card("净入金", _fmt_num(row.get("net_deposit")))
    with c3[3]:
        _card("公司收入", _fmt_num(row.get("company_profit")))

    st.markdown("#### 投注偏好")
    p = st.columns(4)
    with p[0]:
        _card("最常场馆", str(row.get("favorite_provider") or "-"))
    with p[1]:
        _card("最常游戏", str(row.get("favorite_game") or "-"))
    with p[2]:
        _card("最常类型", str(row.get("favorite_category") or "-"))
    with p[3]:
        _card("最常时段", f"{_fmt_num(row.get('favorite_hour'))} 点" if pd.notna(row.get("favorite_hour")) else "-")

    st.markdown("#### AI会员摘要")
    _render_ai_summary(row)

    tabs = st.tabs(["每日趋势", "近期注单", "字段明细"])
    member_key = str(row.get("member_key"))

    with tabs[0]:
        daily = _load_daily(member_key)
        if daily.empty:
            st.caption("暂无每日趋势资料。")
        else:
            fig = px.line(daily, x="report_date", y=["valid_turnover", "profit_loss"], markers=True)
            fig.update_layout(height=360, legend_title_text="指标")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(daily, use_container_width=True, hide_index=True)

    with tabs[1]:
        bets = _load_recent_bets(member_key)
        if bets.empty:
            st.caption("暂无近期注单。")
        else:
            st.dataframe(bets, use_container_width=True, hide_index=True)

    with tabs[2]:
        detail = pd.DataFrame({"字段": row.index.astype(str), "值": [row.get(c) for c in row.index]})
        st.dataframe(detail, use_container_width=True, hide_index=True)
