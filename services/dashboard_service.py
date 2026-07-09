"""Service layer for V6 运营总览.

V6.0.1 Hotfix:
- Uses the existing stable V5.3 aggregate table `agg_dashboard_daily`.
- Does not require `agg_dashboard_kpi`, `agg_dashboard_hourly`, or `agg_dashboard_top`.
- Keeps Streamlit pages alive with friendly empty states instead of raw BigQuery 404 errors.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config import BQ_PREFIX
from services.bigquery_client import query_bq


def _safe_query(sql: str) -> pd.DataFrame:
    try:
        return query_bq(sql)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_kpi() -> pd.DataFrame:
    """Load latest KPI from the stable daily aggregate.

    This intentionally reads only `agg_dashboard_daily` so V6 remains compatible
    with the current V5.3 auto-refresh pipeline.
    """
    sql = f"""
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
    return _safe_query(sql)


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_hourly() -> pd.DataFrame:
    """V6.0.1 uses daily aggregate as a safe trend fallback.

    The column name remains compatible with the page by exposing `report_hour` as
    the report date string. A real hourly aggregate can be added later without
    breaking the UI.
    """
    sql = f"""
    SELECT
      CAST(report_date AS STRING) AS report_hour,
      report_date,
      bet_amount,
      valid_turnover,
      platform_profit_loss,
      member_count,
      updated_at
    FROM `{BQ_PREFIX}.agg_dashboard_daily`
    ORDER BY report_date DESC
    LIMIT 7
    """
    df = _safe_query(sql)
    if df.empty:
      return df
    return df.sort_values("report_date")


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_top(metric_type: str | None = None, limit: int = 10) -> pd.DataFrame:
    """Load top rankings from existing stable aggregates.

    No dependency on `agg_dashboard_top` in V6.0.1.
    """
    sql = f"""
    WITH match_top AS (
      SELECT
        CURRENT_DATE() AS report_date,
        '热门赛事' AS metric_type,
        CAST(game_id AS STRING) AS item_id,
        match_name AS item_name,
        valid_turnover,
        platform_profit_loss,
        bet_count,
        member_count,
        updated_at
      FROM `{BQ_PREFIX}.agg_worldcup_match`
    ), member_top AS (
      SELECT
        CURRENT_DATE() AS report_date,
        '高贡献会员' AS metric_type,
        CAST(member_key AS STRING) AS item_id,
        CAST(member_key AS STRING) AS item_name,
        valid_turnover,
        platform_profit_loss,
        bet_count,
        NULL AS member_count,
        updated_at
      FROM `{BQ_PREFIX}.agg_member_worldcup`
    ), unioned AS (
      SELECT * FROM match_top
      UNION ALL
      SELECT * FROM member_top
    )
    SELECT *
    FROM unioned
    WHERE (@metric_type IS NULL OR metric_type = @metric_type)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY metric_type ORDER BY valid_turnover DESC, ABS(platform_profit_loss) DESC) <= {int(limit)}
    ORDER BY metric_type, valid_turnover DESC
    """
    # query_bq in this project does not support named parameters, so apply a simple filter after query.
    sql = sql.replace("WHERE (@metric_type IS NULL OR metric_type = @metric_type)", "WHERE TRUE")
    df = _safe_query(sql)
    if metric_type and not df.empty and "metric_type" in df.columns:
        df = df[df["metric_type"] == metric_type]
    return df


def make_rule_summary(kpi: pd.DataFrame, tops: pd.DataFrame) -> list[str]:
    if kpi.empty:
        return ["目前没有足够资料生成运营摘要，请确认 V5.3 自动刷新已完成。"]
    row = kpi.iloc[0]
    lines: list[str] = []

    def pct(v):
        try:
            if pd.isna(v):
                return 0.0
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
