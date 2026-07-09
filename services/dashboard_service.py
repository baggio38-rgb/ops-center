"""Service layer for V6 运营总览.

Dashboard pages should use this module instead of embedding SQL directly.
The service reads V6 aggregate tables when available and gracefully falls back to
V5.3 `agg_dashboard_daily` for compatibility.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config import BQ_PREFIX
from services.bigquery_client import query_bq


def _safe_query(sql: str) -> pd.DataFrame:
    try:
        return query_bq(sql)
    except Exception as exc:
        # Keep pages alive even if a new aggregate has not been created yet.
        st.warning(f"数据查询暂时不可用：{exc}")
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_kpi() -> pd.DataFrame:
    sql = f"""
    SELECT *
    FROM `{BQ_PREFIX}.agg_dashboard_kpi`
    ORDER BY report_date DESC
    LIMIT 1
    """
    df = _safe_query(sql)
    if not df.empty:
        return df

    fallback = f"""
    WITH ranked AS (
      SELECT *, ROW_NUMBER() OVER (ORDER BY report_date DESC) AS rn
      FROM `{BQ_PREFIX}.agg_dashboard_daily`
    ), today AS (
      SELECT * FROM ranked WHERE rn = 1
    ), yesterday AS (
      SELECT * FROM ranked WHERE rn = 2
    )
    SELECT
      t.report_date,
      t.bet_count,
      t.member_count,
      t.bet_amount,
      t.valid_turnover,
      t.member_profit_loss,
      t.platform_profit_loss,
      t.worldcup_turnover,
      t.sportsbook_turnover,
      t.casino_turnover,
      SAFE_DIVIDE(t.platform_profit_loss, NULLIF(t.valid_turnover, 0)) AS platform_roi,
      SAFE_DIVIDE(t.member_profit_loss, NULLIF(t.valid_turnover, 0)) AS member_rtp,
      y.bet_amount AS prev_bet_amount,
      y.valid_turnover AS prev_valid_turnover,
      y.platform_profit_loss AS prev_platform_profit_loss,
      y.member_count AS prev_member_count,
      SAFE_DIVIDE(t.bet_amount - y.bet_amount, NULLIF(y.bet_amount, 0)) AS bet_amount_delta,
      SAFE_DIVIDE(t.valid_turnover - y.valid_turnover, NULLIF(y.valid_turnover, 0)) AS valid_turnover_delta,
      SAFE_DIVIDE(t.platform_profit_loss - y.platform_profit_loss, NULLIF(ABS(y.platform_profit_loss), 0)) AS platform_profit_delta,
      SAFE_DIVIDE(t.member_count - y.member_count, NULLIF(y.member_count, 0)) AS member_count_delta,
      t.updated_at
    FROM today t
    LEFT JOIN yesterday y ON TRUE
    """
    return _safe_query(fallback)


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_hourly() -> pd.DataFrame:
    sql = f"""
    SELECT *
    FROM `{BQ_PREFIX}.agg_dashboard_hourly`
    WHERE report_date = (SELECT MAX(report_date) FROM `{BQ_PREFIX}.agg_dashboard_hourly`)
    ORDER BY report_hour
    """
    df = _safe_query(sql)
    if not df.empty:
        return df
    return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_top(metric_type: str | None = None, limit: int = 10) -> pd.DataFrame:
    where = ""
    if metric_type:
        where = f"WHERE metric_type = '{metric_type}'"
    sql = f"""
    SELECT *
    FROM `{BQ_PREFIX}.agg_dashboard_top`
    {where}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY metric_type ORDER BY valid_turnover DESC, platform_profit_loss DESC) <= {int(limit)}
    ORDER BY metric_type, valid_turnover DESC
    """
    df = _safe_query(sql)
    if not df.empty:
        return df

    # Fallback from World Cup and member aggregates, enough for the first V6 demo.
    fallback = f"""
    SELECT
      CURRENT_DATE() AS report_date,
      '热门赛事' AS metric_type,
      game_id AS item_id,
      match_name AS item_name,
      valid_turnover,
      platform_profit_loss,
      bet_count,
      member_count,
      updated_at
    FROM `{BQ_PREFIX}.agg_worldcup_match`
    ORDER BY valid_turnover DESC
    LIMIT {int(limit)}
    """
    return _safe_query(fallback)


def make_rule_summary(kpi: pd.DataFrame, tops: pd.DataFrame) -> list[str]:
    if kpi.empty:
        return ["目前没有足够资料生成运营摘要。"]
    row = kpi.iloc[0]
    lines: list[str] = []

    def pct(v):
        try:
            return float(v) * 100
        except Exception:
            return 0.0

    bet_delta = pct(row.get("bet_amount_delta"))
    profit_delta = pct(row.get("platform_profit_delta"))
    wc_share = 0.0
    try:
        wc_share = float(row.get("worldcup_turnover") or 0) / max(float(row.get("valid_turnover") or 0), 1) * 100
    except Exception:
        pass

    if bet_delta > 0:
        lines.append(f"今日投注金额较昨日成长 {bet_delta:.2f}%，整体活跃度上升。")
    elif bet_delta < 0:
        lines.append(f"今日投注金额较昨日下降 {abs(bet_delta):.2f}%，建议关注主要场馆与赛事流量。")
    else:
        lines.append("今日投注金额与昨日接近，整体波动不大。")

    if profit_delta > 0:
        lines.append(f"今日平台盈亏较昨日改善 {profit_delta:.2f}%。")
    elif profit_delta < 0:
        lines.append(f"今日平台盈亏较昨日转弱 {abs(profit_delta):.2f}%，建议检查高流水赛事与高价值会员。")

    if wc_share > 0:
        lines.append(f"世界杯投注占今日有效投注约 {wc_share:.2f}%，仍是重点观察业务。")

    if not tops.empty:
        first = tops.iloc[0]
        name = first.get("item_name") or first.get("match_name") or "-"
        turnover = first.get("valid_turnover") or 0
        lines.append(f"当前最高流水项目为「{name}」，有效投注约 {turnover:,.0f}。")

    lines.append("建议优先关注：高流水赛事、平台负盈亏项目、VIP高频投注会员。")
    return lines
