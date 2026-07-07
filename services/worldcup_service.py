"""世界杯专区 V2 数据服务。

所有查询都读取 V5 Data Warehouse 的 Aggregate / Dimension 表，
不再从 raw_bet_detail 或 fact_bet_detail 直接现算。
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from services.bigquery_client import query_bq

PROJECT = "mydata-494606"
DATASET = "mydata"


def _q(table: str) -> str:
    return f"`{PROJECT}.{DATASET}.{table}`"


def _sql_str(value: str) -> str:
    return "'" + str(value).replace("'", "\\'") + "'"


def _in_clause(column: str, values: Iterable[str] | None) -> str:
    vals = [str(v) for v in (values or []) if str(v).strip()]
    if not vals:
        return ""
    return f" AND {column} IN ({', '.join(_sql_str(v) for v in vals)})"


def _as_list(value) -> list[str]:
    """Safely normalize BigQuery/Pandas scalar or ARRAY values to a clean list.

    BigQuery ARRAY columns may arrive as list, tuple, numpy.ndarray, or None.
    Never use `value or []` on numpy arrays, because it can raise
    `ValueError: The truth value of an array with more than one element is ambiguous`.
    """
    if value is None:
        return []
    try:
        if pd.isna(value):
            return []
    except Exception:
        pass
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value if v is not None and str(v).strip()]
    try:
        # numpy.ndarray / pandas array-like
        return [str(v) for v in value.tolist() if v is not None and str(v).strip()]
    except Exception:
        return [str(value)] if str(value).strip() else []


def get_filter_options() -> dict[str, list[str]]:
    sql = f"""
    SELECT
      ARRAY_AGG(DISTINCT stage IGNORE NULLS ORDER BY stage) AS stages,
      ARRAY_AGG(DISTINCT home_team IGNORE NULLS ORDER BY home_team) AS home_teams,
      ARRAY_AGG(DISTINCT away_team IGNORE NULLS ORDER BY away_team) AS away_teams
    FROM {_q('agg_worldcup_match')}
    """
    df = query_bq(sql)
    if df.empty:
        return {"stages": [], "teams": []}
    row = df.iloc[0]
    teams = sorted(set(_as_list(row.get("home_teams")) + _as_list(row.get("away_teams"))))
    return {
        "stages": _as_list(row.get("stages")),
        "teams": teams,
    }


def _match_where(stages: list[str] | None = None, teams: list[str] | None = None) -> str:
    where = "WHERE 1=1"
    where += _in_clause("stage", stages)
    team_vals = [str(v) for v in (teams or []) if str(v).strip()]
    if team_vals:
        team_in = ", ".join(_sql_str(v) for v in team_vals)
        where += f" AND (home_team IN ({team_in}) OR away_team IN ({team_in}))"
    return where


def get_worldcup_kpi(stages: list[str] | None = None, teams: list[str] | None = None) -> pd.DataFrame:
    where = _match_where(stages, teams)
    sql = f"""
    WITH m AS (
      SELECT *
      FROM {_q('agg_worldcup_match')}
      {where}
    ), members AS (
      SELECT COUNT(DISTINCT f.`会员账号`) AS member_count
      FROM {_q('fact_worldcup_bet')} f
      JOIN m
        ON TRIM(CAST(f.`游戏编号` AS STRING)) = m.game_id
    )
    SELECT
      SUM(bet_count) AS bet_count,
      (SELECT member_count FROM members) AS member_count,
      COUNT(DISTINCT game_id) AS match_count,
      SUM(bet_amount) AS bet_amount,
      SUM(valid_turnover) AS valid_turnover,
      SUM(member_profit_loss) AS member_profit_loss,
      SUM(platform_profit_loss) AS platform_profit_loss,
      SAFE_DIVIDE(SUM(platform_profit_loss), NULLIF(SUM(valid_turnover), 0)) AS platform_roi
    FROM m
    """
    return query_bq(sql)


def get_match_summary(stages: list[str] | None = None, teams: list[str] | None = None, limit: int = 50) -> pd.DataFrame:
    where = _match_where(stages, teams)
    sql = f"""
    SELECT
      game_id, tournament, stage, match_name, home_team, away_team, kickoff_time,
      bet_count, member_count, bet_amount, valid_turnover,
      member_profit_loss, platform_profit_loss, member_rtp, platform_roi, updated_at
    FROM {_q('agg_worldcup_match')}
    {where}
    ORDER BY valid_turnover DESC
    LIMIT {int(limit)}
    """
    return query_bq(sql)


def get_daily_trend(stages: list[str] | None = None, teams: list[str] | None = None) -> pd.DataFrame:
    where = _match_where(stages, teams)
    sql = f"""
    SELECT
      DATE(kickoff_time) AS match_date,
      SUM(bet_count) AS bet_count,
      SUM(member_count) AS member_count,
      SUM(bet_amount) AS bet_amount,
      SUM(valid_turnover) AS valid_turnover,
      SUM(platform_profit_loss) AS platform_profit_loss
    FROM {_q('agg_worldcup_match')}
    {where}
    GROUP BY match_date
    ORDER BY match_date
    """
    return query_bq(sql)


def get_stage_summary() -> pd.DataFrame:
    sql = f"""
    SELECT
      stage,
      COUNT(DISTINCT game_id) AS match_count,
      SUM(bet_count) AS bet_count,
      SUM(valid_turnover) AS valid_turnover,
      SUM(platform_profit_loss) AS platform_profit_loss
    FROM {_q('agg_worldcup_match')}
    GROUP BY stage
    ORDER BY
      CASE stage
        WHEN '小组赛' THEN 1
        WHEN '32强' THEN 2
        WHEN '16强' THEN 3
        WHEN '8强' THEN 4
        WHEN '4强' THEN 5
        WHEN '决赛阶段' THEN 6
        ELSE 99
      END
    """
    return query_bq(sql)


def get_playtype_summary(stages: list[str] | None = None, limit: int = 30) -> pd.DataFrame:
    where = "WHERE 1=1" + _in_clause("stage", stages)
    sql = f"""
    SELECT
      play_type,
      SUM(bet_count) AS bet_count,
      SUM(member_count) AS member_count,
      SUM(bet_amount) AS bet_amount,
      SUM(valid_turnover) AS valid_turnover,
      SUM(member_profit_loss) AS member_profit_loss,
      SUM(platform_profit_loss) AS platform_profit_loss,
      SAFE_DIVIDE(SUM(platform_profit_loss), NULLIF(SUM(valid_turnover), 0)) AS platform_roi
    FROM {_q('agg_worldcup_playtype')}
    {where}
    GROUP BY play_type
    ORDER BY valid_turnover DESC
    LIMIT {int(limit)}
    """
    return query_bq(sql)


def get_member_summary(limit: int = 50) -> pd.DataFrame:
    sql = f"""
    SELECT
      w.member_key,
      COALESCE(m.vip_level, '') AS vip_level,
      COALESCE(m.agent_name, '') AS agent_name,
      COALESCE(m.risk_level, '') AS risk_level,
      COALESCE(m.risk_score, 0) AS risk_score,
      w.bet_count,
      w.game_count,
      w.play_type_count,
      w.provider_count,
      w.bet_amount,
      w.valid_turnover,
      w.member_profit_loss,
      w.platform_profit_loss
    FROM {_q('agg_member_worldcup')} w
    LEFT JOIN {_q('dim_member')} m
      ON LOWER(TRIM(w.member_key)) = LOWER(TRIM(m.member_key))
    ORDER BY w.valid_turnover DESC
    LIMIT {int(limit)}
    """
    return query_bq(sql)


def get_risk_member_summary(limit: int = 50) -> pd.DataFrame:
    sql = f"""
    SELECT
      w.member_key,
      COALESCE(m.vip_level, '') AS vip_level,
      COALESCE(m.agent_name, '') AS agent_name,
      COALESCE(m.risk_level, 'Normal') AS risk_level,
      COALESCE(m.risk_score, 0) AS risk_score,
      w.bet_count,
      w.game_count,
      w.valid_turnover,
      w.platform_profit_loss
    FROM {_q('agg_member_worldcup')} w
    LEFT JOIN {_q('dim_member')} m
      ON LOWER(TRIM(w.member_key)) = LOWER(TRIM(m.member_key))
    WHERE COALESCE(m.risk_level, 'Normal') != 'Normal'
    ORDER BY m.risk_score DESC, w.valid_turnover DESC
    LIMIT {int(limit)}
    """
    return query_bq(sql)


def get_risk_distribution() -> pd.DataFrame:
    sql = f"""
    SELECT
      COALESCE(m.risk_level, 'Normal') AS risk_level,
      COUNT(DISTINCT w.member_key) AS member_count,
      SUM(w.valid_turnover) AS valid_turnover,
      SUM(w.platform_profit_loss) AS platform_profit_loss
    FROM {_q('agg_member_worldcup')} w
    LEFT JOIN {_q('dim_member')} m
      ON LOWER(TRIM(w.member_key)) = LOWER(TRIM(m.member_key))
    GROUP BY risk_level
    ORDER BY member_count DESC
    """
    return query_bq(sql)
