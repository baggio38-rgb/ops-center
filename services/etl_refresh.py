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


# -----------------------------------------------------------------------------
# V5.3 Auto Refresh Layer
# raw_bet_detail -> fact_bet_detail -> dim_game -> fact_worldcup_bet
#                -> agg_worldcup_match / agg_worldcup_playtype / agg_member_worldcup
#                -> agg_dashboard_daily
# -----------------------------------------------------------------------------

SQL_FACT_BET_DETAIL = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.fact_bet_detail` AS
WITH src AS (
  SELECT
    t.*,
    COALESCE(
      NULLIF(TRIM(CAST(`注单流水号` AS STRING)), ''),
      CONCAT('__NO_ORDER__', CAST(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))) AS STRING))
    ) AS _dedup_order_key
  FROM `{BQ_PREFIX}.raw_bet_detail` AS t
), ranked AS (
  SELECT
    * EXCEPT(_dedup_order_key),
    ROW_NUMBER() OVER (
      PARTITION BY _dedup_order_key
      ORDER BY _imported_at DESC
    ) AS rn
  FROM src
)
SELECT * EXCEPT(rn)
FROM ranked
WHERE rn = 1
"""

SQL_DIM_GAME = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.dim_game` AS
WITH wc AS (
  SELECT
    TRIM(CAST(`游戏编号` AS STRING)) AS game_id,
    CAST(`投注详情` AS STRING) AS bet_detail,
    REPLACE(REPLACE(CAST(`投注详情` AS STRING), '_x000D_', '\\n'), '\\r', '\\n') AS detail_norm
  FROM `{BQ_PREFIX}.fact_bet_detail`
  WHERE TRIM(CAST(`游戏编号` AS STRING)) IS NOT NULL
    AND TRIM(CAST(`游戏编号` AS STRING)) != ''
    AND CAST(`投注详情` AS STRING) LIKE '%世界杯2026(在加拿大、墨西哥&美国)%'
    AND LOWER(CAST(`投注详情` AS STRING)) NOT LIKE '%panda%'
), parsed AS (
  SELECT
    game_id,
    ARRAY_AGG(
      SAFE.PARSE_DATETIME(
        '%Y-%m-%d %H:%M:%S',
        REGEXP_EXTRACT(detail_norm, r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)')
      ) IGNORE NULLS
      ORDER BY SAFE.PARSE_DATETIME(
        '%Y-%m-%d %H:%M:%S',
        REGEXP_EXTRACT(detail_norm, r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)')
      )
      LIMIT 1
    )[SAFE_OFFSET(0)] AS kickoff_time,
    ARRAY_AGG(detail_norm IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS sample_detail,
    ARRAY_AGG(
      NULLIF(TRIM(SPLIT(detail_norm, '\\n')[SAFE_OFFSET(2)]), '')
      IGNORE NULLS
      LIMIT 1
    )[SAFE_OFFSET(0)] AS match_name_raw
  FROM wc
  GROUP BY game_id
), final AS (
  SELECT
    game_id,
    '足球' AS sport,
    '世界杯2026' AS tournament,
    CASE
      WHEN REGEXP_CONTAINS(IFNULL(match_name_raw, ''), r'入围16强|冠军盘口|特别玩法') THEN '特别玩法'
      WHEN kickoff_time >= DATETIME '2026-07-18 00:00:00' THEN '决赛阶段'
      WHEN kickoff_time >= DATETIME '2026-07-14 00:00:00' THEN '4强'
      WHEN kickoff_time >= DATETIME '2026-07-09 00:00:00' THEN '8强'
      WHEN kickoff_time >= DATETIME '2026-07-04 00:00:00' THEN '16强'
      WHEN kickoff_time >= DATETIME '2026-06-28 00:00:00' THEN '32强'
      ELSE '小组赛'
    END AS stage,
    match_name_raw AS match_name,
    TRIM(SPLIT(match_name_raw, ' v ')[SAFE_OFFSET(0)]) AS home_team,
    TRIM(SPLIT(match_name_raw, ' v ')[SAFE_OFFSET(1)]) AS away_team,
    kickoff_time,
    sample_detail,
    CURRENT_TIMESTAMP() AS updated_at
  FROM parsed
)
SELECT *
FROM final
WHERE game_id IS NOT NULL AND game_id != ''
"""

SQL_FACT_WORLDCUP_BET = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.fact_worldcup_bet` AS
SELECT
  f.*
FROM `{BQ_PREFIX}.fact_bet_detail` f
JOIN `{BQ_PREFIX}.dim_game` g
  ON TRIM(CAST(f.`游戏编号` AS STRING)) = g.game_id
WHERE CAST(f.`投注详情` AS STRING) LIKE '%世界杯2026(在加拿大、墨西哥&美国)%'
  AND LOWER(CAST(f.`投注详情` AS STRING)) NOT LIKE '%panda%'
  AND IFNULL(CAST(f.`游戏名称` AS STRING), '') NOT LIKE '%串关%'
"""

SQL_AGG_WORLDCUP_MATCH = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.agg_worldcup_match` AS
SELECT
  g.game_id,
  g.tournament,
  g.stage,
  g.match_name,
  g.home_team,
  g.away_team,
  g.kickoff_time,
  DATE(g.kickoff_time) AS match_date,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT f.`会员账号`) AS member_count,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`下注金额` AS STRING)), ',', '') AS FLOAT64)) AS bet_amount,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`有效投注` AS STRING)), ',', '') AS FLOAT64)) AS valid_turnover,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS member_profit_loss,
  -SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS platform_profit_loss,
  SAFE_DIVIDE(
    SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`盈亏` AS STRING)), ',', '') AS FLOAT64)),
    NULLIF(SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`有效投注` AS STRING)), ',', '') AS FLOAT64)), 0)
  ) AS member_rtp,
  SAFE_DIVIDE(
    -SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`盈亏` AS STRING)), ',', '') AS FLOAT64)),
    NULLIF(SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`有效投注` AS STRING)), ',', '') AS FLOAT64)), 0)
  ) AS platform_roi,
  CURRENT_TIMESTAMP() AS updated_at
FROM `{BQ_PREFIX}.fact_worldcup_bet` f
JOIN `{BQ_PREFIX}.dim_game` g
  ON TRIM(CAST(f.`游戏编号` AS STRING)) = g.game_id
GROUP BY
  g.game_id,
  g.tournament,
  g.stage,
  g.match_name,
  g.home_team,
  g.away_team,
  g.kickoff_time
"""

SQL_AGG_WORLDCUP_PLAYTYPE = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.agg_worldcup_playtype` AS
SELECT
  g.game_id,
  g.tournament,
  g.stage,
  g.match_name,
  COALESCE(NULLIF(TRIM(CAST(f.`玩法` AS STRING)), ''), '未分类') AS play_type,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT f.`会员账号`) AS member_count,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`下注金额` AS STRING)), ',', '') AS FLOAT64)) AS bet_amount,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`有效投注` AS STRING)), ',', '') AS FLOAT64)) AS valid_turnover,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS member_profit_loss,
  -SUM(SAFE_CAST(REPLACE(TRIM(CAST(f.`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS platform_profit_loss,
  CURRENT_TIMESTAMP() AS updated_at
FROM `{BQ_PREFIX}.fact_worldcup_bet` f
JOIN `{BQ_PREFIX}.dim_game` g
  ON TRIM(CAST(f.`游戏编号` AS STRING)) = g.game_id
GROUP BY
  g.game_id,
  g.tournament,
  g.stage,
  g.match_name,
  play_type
"""

SQL_AGG_MEMBER_WORLDCUP = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.agg_member_worldcup` AS
SELECT
  `会员账号` AS member_key,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT TRIM(CAST(`游戏编号` AS STRING))) AS game_count,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64)) AS bet_amount,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64)) AS valid_turnover,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS member_profit_loss,
  -SUM(SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS platform_profit_loss,
  COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(`玩法` AS STRING)), ''), '未分类')) AS play_type_count,
  COUNT(DISTINCT TRIM(CAST(`场馆名称` AS STRING))) AS provider_count,
  CURRENT_TIMESTAMP() AS updated_at
FROM `{BQ_PREFIX}.fact_worldcup_bet`
GROUP BY member_key
"""

SQL_AGG_DASHBOARD_DAILY = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.agg_dashboard_daily` AS
SELECT
  DATE({BET_DT}) AS report_date,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT `会员账号`) AS member_count,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64)) AS bet_amount,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64)) AS valid_turnover,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS member_profit_loss,
  -SUM(SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS platform_profit_loss,
  SUM(CASE
    WHEN CAST(`投注详情` AS STRING) LIKE '%世界杯2026(在加拿大、墨西哥&美国)%'
    THEN SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64)
    ELSE 0
  END) AS worldcup_turnover,
  SUM(CASE
    WHEN TRIM(CAST(`游戏类型` AS STRING)) = '体育'
    THEN SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64)
    ELSE 0
  END) AS sportsbook_turnover,
  SUM(CASE
    WHEN TRIM(CAST(`游戏类型` AS STRING)) != '体育'
    THEN SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64)
    ELSE 0
  END) AS casino_turnover,
  CURRENT_TIMESTAMP() AS updated_at
FROM `{BQ_PREFIX}.fact_bet_detail`
WHERE DATE({BET_DT}) IS NOT NULL
GROUP BY report_date
"""

SQL_AGG_DASHBOARD_KPI = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.agg_dashboard_kpi` AS
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (ORDER BY report_date DESC) AS rn
  FROM `{BQ_PREFIX}.agg_dashboard_daily`
), base AS (
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
  FROM ranked t
  LEFT JOIN ranked y ON y.rn = t.rn + 1
)
SELECT * FROM base
"""

SQL_AGG_DASHBOARD_HOURLY = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.agg_dashboard_hourly` AS
SELECT
  DATE({BET_DT}) AS report_date,
  EXTRACT(HOUR FROM {BET_DT}) AS report_hour,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT `会员账号`) AS member_count,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64)) AS bet_amount,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64)) AS valid_turnover,
  SUM(SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS member_profit_loss,
  -SUM(SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64)) AS platform_profit_loss,
  CURRENT_TIMESTAMP() AS updated_at
FROM `{BQ_PREFIX}.fact_bet_detail`
WHERE DATE({BET_DT}) IS NOT NULL
GROUP BY report_date, report_hour
"""

SQL_AGG_DASHBOARD_TOP = f"""
CREATE OR REPLACE TABLE `{BQ_PREFIX}.agg_dashboard_top` AS
WITH latest_day AS (
  SELECT MAX(DATE({BET_DT})) AS report_date
  FROM `{BQ_PREFIX}.fact_bet_detail`
  WHERE DATE({BET_DT}) IS NOT NULL
), clean AS (
  SELECT
    DATE({BET_DT}) AS report_date,
    TRIM(CAST(`会员账号` AS STRING)) AS member_id,
    TRIM(CAST(`场馆名称` AS STRING)) AS provider_name,
    TRIM(CAST(`游戏名称` AS STRING)) AS game_name,
    SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64) AS bet_amount,
    SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64) AS valid_turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64) AS member_profit_loss
  FROM `{BQ_PREFIX}.fact_bet_detail`
  WHERE DATE({BET_DT}) = (SELECT report_date FROM latest_day)
), provider_top AS (
  SELECT
    report_date,
    '热门场馆' AS metric_type,
    provider_name AS item_id,
    provider_name AS item_name,
    COUNT(*) AS bet_count,
    COUNT(DISTINCT member_id) AS member_count,
    SUM(bet_amount) AS bet_amount,
    SUM(valid_turnover) AS valid_turnover,
    SUM(member_profit_loss) AS member_profit_loss,
    -SUM(member_profit_loss) AS platform_profit_loss
  FROM clean
  WHERE provider_name IS NOT NULL AND provider_name != ''
  GROUP BY report_date, provider_name
), game_top AS (
  SELECT
    report_date,
    '热门游戏' AS metric_type,
    game_name AS item_id,
    game_name AS item_name,
    COUNT(*) AS bet_count,
    COUNT(DISTINCT member_id) AS member_count,
    SUM(bet_amount) AS bet_amount,
    SUM(valid_turnover) AS valid_turnover,
    SUM(member_profit_loss) AS member_profit_loss,
    -SUM(member_profit_loss) AS platform_profit_loss
  FROM clean
  WHERE game_name IS NOT NULL AND game_name != ''
  GROUP BY report_date, game_name
), member_top AS (
  SELECT
    report_date,
    '高贡献会员' AS metric_type,
    member_id AS item_id,
    member_id AS item_name,
    COUNT(*) AS bet_count,
    1 AS member_count,
    SUM(bet_amount) AS bet_amount,
    SUM(valid_turnover) AS valid_turnover,
    SUM(member_profit_loss) AS member_profit_loss,
    -SUM(member_profit_loss) AS platform_profit_loss
  FROM clean
  WHERE member_id IS NOT NULL AND member_id != ''
  GROUP BY report_date, member_id
), match_top AS (
  SELECT
    CURRENT_DATE() AS report_date,
    '热门赛事' AS metric_type,
    game_id AS item_id,
    match_name AS item_name,
    bet_count,
    member_count,
    bet_amount,
    valid_turnover,
    member_profit_loss,
    platform_profit_loss
  FROM `{BQ_PREFIX}.agg_worldcup_match`
)
SELECT *, CURRENT_TIMESTAMP() AS updated_at
FROM (
  SELECT * FROM provider_top
  UNION ALL SELECT * FROM game_top
  UNION ALL SELECT * FROM member_top
  UNION ALL SELECT * FROM match_top
)
QUALIFY ROW_NUMBER() OVER (PARTITION BY metric_type ORDER BY valid_turnover DESC, platform_profit_loss DESC) <= 30
"""


def refresh_worldcup_aggregates(client: bigquery.Client | None = None, *, stop_on_error: bool = False) -> list[RefreshResult]:
    """Rebuild World Cup fact and aggregate tables used by 世界杯专区."""
    client = client or bigquery.Client(project=PROJECT_ID)
    steps: list[tuple[str, str]] = [
        ("fact_bet_detail", SQL_FACT_BET_DETAIL),
        ("dim_game", SQL_DIM_GAME),
        ("fact_worldcup_bet", SQL_FACT_WORLDCUP_BET),
        ("agg_worldcup_match", SQL_AGG_WORLDCUP_MATCH),
        ("agg_worldcup_playtype", SQL_AGG_WORLDCUP_PLAYTYPE),
        ("agg_member_worldcup", SQL_AGG_MEMBER_WORLDCUP),
        ("agg_dashboard_daily", SQL_AGG_DASHBOARD_DAILY),
        ("agg_dashboard_kpi", SQL_AGG_DASHBOARD_KPI),
        ("agg_dashboard_hourly", SQL_AGG_DASHBOARD_HOURLY),
        ("agg_dashboard_top", SQL_AGG_DASHBOARD_TOP),
    ]
    results: list[RefreshResult] = []
    for table, sql in steps:
        try:
            _run(client, sql)
            results.append(RefreshResult(table, True, "OK"))
        except Exception as exc:
            results.append(RefreshResult(table, False, str(exc)[:500]))
            if stop_on_error:
                break
    return results


def refresh_full_warehouse(client: bigquery.Client | None = None, *, stop_on_error: bool = False) -> list[RefreshResult]:
    """V5.3 one-click refresh: core marts + World Cup aggregates + dashboard daily."""
    client = client or bigquery.Client(project=PROJECT_ID)
    results: list[RefreshResult] = []
    results.extend(refresh_core_marts(client, stop_on_error=stop_on_error))
    if stop_on_error and any(not r.ok for r in results):
        return results
    results.extend(refresh_worldcup_aggregates(client, stop_on_error=stop_on_error))
    return results


def format_refresh_results(results: Iterable[RefreshResult]) -> str:
    lines = []
    for r in results:
        icon = "✅" if r.ok else "❌"
        lines.append(f"{icon} {r.table}: {r.message}")
    return "\n".join(lines)
