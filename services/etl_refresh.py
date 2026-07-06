"""BigQuery ETL refresh helpers for 亿兆智能决策平台.

This module rebuilds the derived tables used by Dashboard, Member360 and Risk Center
after new raw reports are uploaded.

Main flow:
raw_bet_detail -> fact_member_daily_v2 -> mart_member_profile -> risk_member_score
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from google.cloud import bigquery

from config import BQ_PREFIX, PROJECT_ID, DATASET_ID


@dataclass
class RefreshResult:
    table: str
    ok: bool
    message: str


def _run(client: bigquery.Client, sql: str) -> None:
    client.query(sql).result()


def _bet_datetime_expr(col: str = "`下注时间`") -> str:
    """Normalize mixed BigQuery string values to DATETIME.

    Handles normal strings like 2026-07-06 05:11:57 and Excel serial strings like
    46209.21663194444. Returns a SQL expression, not a Python value.
    """
    s = f"TRIM(CAST({col} AS STRING))"
    return f"""
    CASE
      WHEN REGEXP_CONTAINS({s}, r'^\\d+(\\.\\d+)?$')
           AND SAFE_CAST({s} AS FLOAT64) BETWEEN 30000 AND 60000
        THEN DATETIME_ADD(
          DATETIME '1899-12-30 00:00:00',
          INTERVAL CAST(ROUND(SAFE_CAST({s} AS FLOAT64) * 86400) AS INT64) SECOND
        )
      ELSE SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', {s})
    END
    """


BET_DT = _bet_datetime_expr()


SQL_FACT_MEMBER_DAILY_V2 = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.fact_member_daily_v2` AS
WITH clean AS (
  SELECT
    DATE({BET_DT}) AS report_date,
    UPPER(REGEXP_REPLACE(TRIM(CAST(`会员账号` AS STRING)), r'[^A-Za-z0-9]', '')) AS member_key,
    TRIM(CAST(`会员账号` AS STRING)) AS member_id,
    TRIM(CAST(`场馆名称` AS STRING)) AS provider,
    TRIM(CAST(`场馆类型` AS STRING)) AS category,
    TRIM(CAST(`游戏名称` AS STRING)) AS game_name,
    SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64) AS turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64) AS valid_turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64) AS profit_loss,
    {BET_DT} AS bet_dt
  FROM `{BQ_PREFIX}.raw_bet_detail`
  WHERE TRIM(CAST(`会员账号` AS STRING)) IS NOT NULL
    AND TRIM(CAST(`会员账号` AS STRING)) != ''
), valid AS (
  SELECT * FROM clean
  WHERE report_date IS NOT NULL AND member_key IS NOT NULL AND member_key != ''
)
SELECT
  report_date,
  member_key,
  ANY_VALUE(member_id) AS member_id,
  SUM(IFNULL(turnover, 0)) AS turnover,
  SUM(IFNULL(valid_turnover, 0)) AS valid_turnover,
  SUM(IFNULL(profit_loss, 0)) AS profit_loss,
  COUNT(*) AS bet_count,
  SAFE_DIVIDE(SUM(IFNULL(profit_loss, 0)), NULLIF(SUM(IFNULL(valid_turnover, 0)), 0)) AS rtp,
  SAFE_DIVIDE(SUM(IFNULL(profit_loss, 0)), NULLIF(SUM(IFNULL(turnover, 0)), 0)) AS roi,
  AVG(IFNULL(turnover, 0)) AS avg_bet,
  MAX(IFNULL(turnover, 0)) AS max_bet,
  COUNT(DISTINCT EXTRACT(HOUR FROM bet_dt) * 60 + EXTRACT(MINUTE FROM bet_dt)) AS active_minutes,
  MAX(bet_dt) AS last_bet_time,
  CURRENT_TIMESTAMP() AS updated_at
FROM valid
GROUP BY report_date, member_key
"""


SQL_MART_MEMBER_PROFILE = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.mart_member_profile` AS
WITH bet_clean AS (
  SELECT
    UPPER(REGEXP_REPLACE(TRIM(CAST(`会员账号` AS STRING)), r'[^A-Za-z0-9]', '')) AS member_key,
    TRIM(CAST(`会员账号` AS STRING)) AS member_id,
    TRIM(CAST(`场馆名称` AS STRING)) AS provider,
    TRIM(CAST(`场馆类型` AS STRING)) AS category,
    TRIM(CAST(`游戏名称` AS STRING)) AS game_name,
    SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64) AS turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64) AS valid_turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64) AS profit_loss,
    {BET_DT} AS bet_dt
  FROM `{BQ_PREFIX}.raw_bet_detail`
  WHERE TRIM(CAST(`会员账号` AS STRING)) IS NOT NULL
    AND TRIM(CAST(`会员账号` AS STRING)) != ''
), valid AS (
  SELECT * FROM bet_clean WHERE member_key IS NOT NULL AND member_key != '' AND bet_dt IS NOT NULL
), agg AS (
  SELECT
    member_key,
    ANY_VALUE(member_id) AS member_id,
    SUM(IFNULL(turnover, 0)) AS turnover,
    SUM(IFNULL(valid_turnover, 0)) AS valid_turnover,
    SUM(IFNULL(profit_loss, 0)) AS profit_loss,
    COUNT(*) AS bet_count,
    COUNT(DISTINCT DATE(bet_dt)) AS active_days,
    SAFE_DIVIDE(COUNT(*), NULLIF(COUNT(DISTINCT DATE(bet_dt)), 0)) AS avg_bets_per_day,
    SAFE_DIVIDE(SUM(IFNULL(profit_loss, 0)), NULLIF(SUM(IFNULL(valid_turnover, 0)), 0)) AS rtp,
    SAFE_DIVIDE(SUM(IFNULL(profit_loss, 0)), NULLIF(SUM(IFNULL(turnover, 0)), 0)) AS roi,
    AVG(IFNULL(turnover, 0)) AS avg_bet,
    MAX(IFNULL(turnover, 0)) AS max_bet,
    MAX(bet_dt) AS last_bet_time
  FROM valid
  GROUP BY member_key
), provider_rank AS (
  SELECT member_key, provider AS favorite_provider,
         ROW_NUMBER() OVER (PARTITION BY member_key ORDER BY SUM(IFNULL(valid_turnover,0)) DESC, COUNT(*) DESC) AS rn
  FROM valid
  GROUP BY member_key, provider
), category_rank AS (
  SELECT member_key, category AS favorite_category,
         ROW_NUMBER() OVER (PARTITION BY member_key ORDER BY SUM(IFNULL(valid_turnover,0)) DESC, COUNT(*) DESC) AS rn
  FROM valid
  GROUP BY member_key, category
), game_rank AS (
  SELECT member_key, game_name AS favorite_game,
         ROW_NUMBER() OVER (PARTITION BY member_key ORDER BY SUM(IFNULL(valid_turnover,0)) DESC, COUNT(*) DESC) AS rn
  FROM valid
  GROUP BY member_key, game_name
), hour_rank AS (
  SELECT member_key, EXTRACT(HOUR FROM bet_dt) AS favorite_hour,
         ROW_NUMBER() OVER (PARTITION BY member_key ORDER BY COUNT(*) DESC) AS rn
  FROM valid
  GROUP BY member_key, favorite_hour
), member_raw AS (
  SELECT
    UPPER(REGEXP_REPLACE(TRIM(CAST(`会员账号` AS STRING)), r'[^A-Za-z0-9]', '')) AS member_key,
    ARRAY_AGG(CAST(`VIP等级` AS STRING) IGNORE NULLS ORDER BY _imported_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS vip_level,
    ARRAY_AGG(CAST(`代理` AS STRING) IGNORE NULLS ORDER BY _imported_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS agent_name,
    ARRAY_AGG(CAST(`会员状态` AS STRING) IGNORE NULLS ORDER BY _imported_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS member_status,
    ARRAY_AGG(CAST(`注册时间` AS STRING) IGNORE NULLS ORDER BY _imported_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS register_time,
    ARRAY_AGG(CAST(`最后登录时间` AS STRING) IGNORE NULLS ORDER BY _imported_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS last_login_time
  FROM `{BQ_PREFIX}.raw_member_report`
  WHERE TRIM(CAST(`会员账号` AS STRING)) IS NOT NULL
    AND TRIM(CAST(`会员账号` AS STRING)) != ''
  GROUP BY member_key
)
SELECT
  a.member_key,
  a.member_id,
  IFNULL(m.vip_level, '') AS vip_level,
  IFNULL(m.agent_name, '') AS agent_name,
  IFNULL(m.member_status, '') AS member_status,
  m.register_time,
  m.last_login_time,
  CAST(a.last_bet_time AS STRING) AS last_bet_time,
  a.turnover,
  a.valid_turnover,
  a.profit_loss,
  a.bet_count,
  a.active_days,
  a.avg_bets_per_day,
  a.rtp,
  a.roi,
  a.avg_bet,
  a.max_bet,
  0.0 AS deposit,
  0.0 AS withdraw,
  CASE
    WHEN a.valid_turnover >= 5000000 THEN 'Whale'
    WHEN a.valid_turnover >= 1000000 THEN '高价值'
    WHEN a.valid_turnover >= 300000 THEN '中高价值'
    ELSE '普通'
  END AS value_level,
  IFNULL(pr.favorite_provider, '未知场馆') AS favorite_provider,
  IFNULL(gr.favorite_game, '未知游戏') AS favorite_game,
  IFNULL(cr.favorite_category, '未知类型') AS favorite_category,
  hr.favorite_hour,
  CONCAT(
    IF(a.valid_turnover >= 5000000, 'Whale,', ''),
    IF(a.valid_turnover >= 1000000, '高价值,', ''),
    IF(LOWER(IFNULL(m.vip_level,'')) NOT IN ('', '普通会员', 'normal'), 'VIP会员,', ''),
    IF(a.profit_loss > 300000, '高盈利会员,', ''),
    IF(a.profit_loss < -300000, '高亏损会员,', '')
  ) AS auto_tags,
  CURRENT_TIMESTAMP() AS updated_at
FROM agg a
LEFT JOIN member_raw m USING(member_key)
LEFT JOIN provider_rank pr ON a.member_key = pr.member_key AND pr.rn = 1
LEFT JOIN category_rank cr ON a.member_key = cr.member_key AND cr.rn = 1
LEFT JOIN game_rank gr ON a.member_key = gr.member_key AND gr.rn = 1
LEFT JOIN hour_rank hr ON a.member_key = hr.member_key AND hr.rn = 1
"""



SQL_MART_MEMBER_PROFILE_NO_MEMBER_RAW = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.mart_member_profile` AS
WITH bet_clean AS (
  SELECT
    UPPER(REGEXP_REPLACE(TRIM(CAST(`会员账号` AS STRING)), r'[^A-Za-z0-9]', '')) AS member_key,
    TRIM(CAST(`会员账号` AS STRING)) AS member_id,
    TRIM(CAST(`场馆名称` AS STRING)) AS provider,
    TRIM(CAST(`场馆类型` AS STRING)) AS category,
    TRIM(CAST(`游戏名称` AS STRING)) AS game_name,
    SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64) AS turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64) AS valid_turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64) AS profit_loss,
    {BET_DT} AS bet_dt
  FROM `{BQ_PREFIX}.raw_bet_detail`
  WHERE TRIM(CAST(`会员账号` AS STRING)) IS NOT NULL
    AND TRIM(CAST(`会员账号` AS STRING)) != ''
), valid AS (
  SELECT * FROM bet_clean WHERE member_key IS NOT NULL AND member_key != '' AND bet_dt IS NOT NULL
), agg AS (
  SELECT
    member_key,
    ANY_VALUE(member_id) AS member_id,
    SUM(IFNULL(turnover, 0)) AS turnover,
    SUM(IFNULL(valid_turnover, 0)) AS valid_turnover,
    SUM(IFNULL(profit_loss, 0)) AS profit_loss,
    COUNT(*) AS bet_count,
    COUNT(DISTINCT DATE(bet_dt)) AS active_days,
    SAFE_DIVIDE(COUNT(*), NULLIF(COUNT(DISTINCT DATE(bet_dt)), 0)) AS avg_bets_per_day,
    SAFE_DIVIDE(SUM(IFNULL(profit_loss, 0)), NULLIF(SUM(IFNULL(valid_turnover, 0)), 0)) AS rtp,
    SAFE_DIVIDE(SUM(IFNULL(profit_loss, 0)), NULLIF(SUM(IFNULL(turnover, 0)), 0)) AS roi,
    AVG(IFNULL(turnover, 0)) AS avg_bet,
    MAX(IFNULL(turnover, 0)) AS max_bet,
    MAX(bet_dt) AS last_bet_time
  FROM valid
  GROUP BY member_key
), provider_rank AS (
  SELECT member_key, provider AS favorite_provider,
         ROW_NUMBER() OVER (PARTITION BY member_key ORDER BY SUM(IFNULL(valid_turnover,0)) DESC, COUNT(*) DESC) AS rn
  FROM valid
  GROUP BY member_key, provider
), category_rank AS (
  SELECT member_key, category AS favorite_category,
         ROW_NUMBER() OVER (PARTITION BY member_key ORDER BY SUM(IFNULL(valid_turnover,0)) DESC, COUNT(*) DESC) AS rn
  FROM valid
  GROUP BY member_key, category
), game_rank AS (
  SELECT member_key, game_name AS favorite_game,
         ROW_NUMBER() OVER (PARTITION BY member_key ORDER BY SUM(IFNULL(valid_turnover,0)) DESC, COUNT(*) DESC) AS rn
  FROM valid
  GROUP BY member_key, game_name
), hour_rank AS (
  SELECT member_key, EXTRACT(HOUR FROM bet_dt) AS favorite_hour,
         ROW_NUMBER() OVER (PARTITION BY member_key ORDER BY COUNT(*) DESC) AS rn
  FROM valid
  GROUP BY member_key, favorite_hour
)
SELECT
  a.member_key,
  a.member_id,
  '' AS vip_level,
  '' AS agent_name,
  '' AS member_status,
  NULL AS register_time,
  NULL AS last_login_time,
  CAST(a.last_bet_time AS STRING) AS last_bet_time,
  a.turnover,
  a.valid_turnover,
  a.profit_loss,
  a.bet_count,
  a.active_days,
  a.avg_bets_per_day,
  a.rtp,
  a.roi,
  a.avg_bet,
  a.max_bet,
  0.0 AS deposit,
  0.0 AS withdraw,
  CASE
    WHEN a.valid_turnover >= 5000000 THEN 'Whale'
    WHEN a.valid_turnover >= 1000000 THEN '高价值'
    WHEN a.valid_turnover >= 300000 THEN '中高价值'
    ELSE '普通'
  END AS value_level,
  IFNULL(pr.favorite_provider, '未知场馆') AS favorite_provider,
  IFNULL(gr.favorite_game, '未知游戏') AS favorite_game,
  IFNULL(cr.favorite_category, '未知类型') AS favorite_category,
  hr.favorite_hour,
  CONCAT(
    IF(a.valid_turnover >= 5000000, 'Whale,', ''),
    IF(a.valid_turnover >= 1000000, '高价值,', ''),
    IF(a.profit_loss > 300000, '高盈利会员,', ''),
    IF(a.profit_loss < -300000, '高亏损会员,', '')
  ) AS auto_tags,
  CURRENT_TIMESTAMP() AS updated_at
FROM agg a
LEFT JOIN provider_rank pr ON a.member_key = pr.member_key AND pr.rn = 1
LEFT JOIN category_rank cr ON a.member_key = cr.member_key AND cr.rn = 1
LEFT JOIN game_rank gr ON a.member_key = gr.member_key AND gr.rn = 1
LEFT JOIN hour_rank hr ON a.member_key = hr.member_key AND hr.rn = 1
"""



SQL_RISK_MEMBER_SCORE = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.risk_member_score` AS
WITH base AS (
  SELECT
    p.*,
    CASE WHEN p.rtp >= 0.15 AND p.valid_turnover >= 10000 THEN 25 WHEN p.rtp >= 0.08 THEN 12 ELSE 0 END AS rtp_score,
    CASE WHEN p.valid_turnover >= 5000000 THEN 20 WHEN p.valid_turnover >= 1000000 THEN 12 ELSE 0 END AS turnover_score,
    CASE WHEN p.favorite_hour BETWEEN 0 AND 5 THEN 10 ELSE 0 END AS night_score,
    CASE WHEN REGEXP_CONTAINS(IFNULL(p.favorite_category,''), r'真人|Live|Casino') THEN 8 ELSE 0 END AS provider_score,
    CASE WHEN p.profit_loss > 300000 THEN 25 WHEN p.profit_loss > 100000 THEN 12 ELSE 0 END AS profit_score,
    CASE WHEN REGEXP_CONTAINS(IFNULL(p.auto_tags,''), r'高盈利|Whale') THEN 10 ELSE 0 END AS tag_score
  FROM `{BQ_PREFIX}.mart_member_profile` p
)
SELECT
  member_key,
  member_id,
  rtp_score,
  turnover_score,
  night_score,
  provider_score,
  profit_score,
  tag_score,
  LEAST(100, rtp_score + turnover_score + night_score + provider_score + profit_score + tag_score) AS risk_score,
  CASE
    WHEN LEAST(100, rtp_score + turnover_score + night_score + provider_score + profit_score + tag_score) >= 80 THEN 'Critical'
    WHEN LEAST(100, rtp_score + turnover_score + night_score + provider_score + profit_score + tag_score) >= 60 THEN 'High'
    WHEN LEAST(100, rtp_score + turnover_score + night_score + provider_score + profit_score + tag_score) >= 35 THEN 'Medium'
    WHEN LEAST(100, rtp_score + turnover_score + night_score + provider_score + profit_score + tag_score) >= 15 THEN 'Low'
    ELSE 'Normal'
  END AS risk_level,
  valid_turnover,
  profit_loss,
  rtp,
  roi,
  favorite_provider,
  favorite_hour,
  auto_tags,
  CURRENT_TIMESTAMP() AS updated_at
FROM base
"""


def refresh_core_marts(client: bigquery.Client | None = None, *, stop_on_error: bool = False) -> list[RefreshResult]:
    """Rebuild core marts used by the app.

    Returns a list of RefreshResult. It tries a member-report join first and falls back
    to a bet-only member mart if raw_member_report is missing or its schema differs.
    """
    client = client or bigquery.Client(project=PROJECT_ID)
    steps: list[tuple[str, str]] = [
        ("fact_member_daily_v2", SQL_FACT_MEMBER_DAILY_V2),
        ("mart_member_profile", SQL_MART_MEMBER_PROFILE),
        ("risk_member_score", SQL_RISK_MEMBER_SCORE),
    ]
    results: list[RefreshResult] = []
    for table, sql in steps:
        try:
            _run(client, sql)
            results.append(RefreshResult(table, True, "OK"))
        except Exception as exc:
            if table == "mart_member_profile":
                try:
                    _run(client, SQL_MART_MEMBER_PROFILE_NO_MEMBER_RAW)
                    results.append(RefreshResult(table, True, "OK（raw_member_report 不可用，已用投注资料重建）"))
                    continue
                except Exception as exc2:
                    results.append(RefreshResult(table, False, str(exc2)[:300]))
            else:
                results.append(RefreshResult(table, False, str(exc)[:300]))
            if stop_on_error:
                break
    return results


def format_refresh_results(results: Iterable[RefreshResult]) -> str:
    lines = []
    for r in results:
        icon = "✅" if r.ok else "❌"
        lines.append(f"{icon} {r.table}: {r.message}")
    return "\n".join(lines)
