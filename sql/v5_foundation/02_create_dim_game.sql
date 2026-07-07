-- 亿兆智能决策平台 V5 Data Foundation
-- 02_create_dim_game.sql
-- 目的：建立赛事维度表。世界杯单场比赛以后只用 game_id 汇整，比赛名称只负责显示。

CREATE OR REPLACE TABLE `mydata-494606.mydata.dim_game` AS
WITH wc AS (
  SELECT
    game_id,
    bet_detail,
    kickoff_time,
    -- 统一换行符，处理 Excel XML 的 _x000D_
    REPLACE(REPLACE(CAST(bet_detail AS STRING), '_x000D_', '\n'), '\r', '\n') AS detail_norm
  FROM `mydata-494606.mydata.fact_bet_detail`
  WHERE game_id IS NOT NULL
    AND bet_detail LIKE '%世界杯2026(在加拿大、墨西哥&美国)%'
), parsed AS (
  SELECT
    game_id,
    ANY_VALUE(kickoff_time) AS kickoff_time,
    ARRAY_AGG(detail_norm IGNORE NULLS LIMIT 1)[OFFSET(0)] AS sample_detail,
    -- 从投注详情中取第三行作为比赛名称：足球时间 / 世界杯名称 / 比赛名称
    ARRAY_AGG(
      NULLIF(TRIM(SPLIT(detail_norm, '\n')[SAFE_OFFSET(2)]), '')
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
      WHEN REGEXP_CONTAINS(match_name_raw, r'入围16强|冠军盘口') THEN '冠军盘口'
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
FROM final;
