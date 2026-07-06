-- v2.0.0 World Cup Engine shared parser CTE
-- Use this CTE as the single source of truth for World Cup pages.
WITH raw AS (
  SELECT
    TRIM(CAST(`会员账号` AS STRING)) AS member_id,
    UPPER(REGEXP_REPLACE(TRIM(CAST(`会员账号` AS STRING)), r'[^A-Za-z0-9]', '')) AS member_key,
    IFNULL(TRIM(CAST(`上级代理名称` AS STRING)), '') AS agent_name,
    TRIM(CAST(`场馆名称` AS STRING)) AS provider,
    TRIM(CAST(`游戏名称` AS STRING)) AS game_name,
    IFNULL(TRIM(CAST(`玩法` AS STRING)), '未识别玩法') AS play_type,
    TRIM(CAST(`投注详情` AS STRING)) AS bet_detail,
    REGEXP_REPLACE(REPLACE(TRIM(CAST(`投注详情` AS STRING)), '_x000D_', '\n'), r'\r', '') AS clean_detail,
    SAFE_CAST(`下注金额` AS FLOAT64) AS turnover,
    SAFE_CAST(`有效投注` AS FLOAT64) AS valid_turnover,
    SAFE_CAST(`盈亏` AS FLOAT64) AS profit_loss,
    -SAFE_CAST(`盈亏` AS FLOAT64) AS platform_profit_loss,
    COALESCE(
      SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING))),
      SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING)))
    ) AS bet_time,
    COALESCE(
      SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
      SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
      SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)'))
    ) AS match_time,
    CAST(`注单流水号` AS STRING) AS bet_id
  FROM `mydata-494606.mydata.raw_bet_detail`
  WHERE `投注详情` IS NOT NULL
    AND CAST(`投注详情` AS STRING) LIKE '%世界杯2026(在加拿大、墨西哥&美国)%'
    AND LOWER(CAST(`投注详情` AS STRING)) NOT LIKE '%panda%'
), parsed AS (
  SELECT
    raw.*,
    REGEXP_REPLACE(
      REGEXP_EXTRACT(clean_detail, r'(?:^|\n)([^\n@]+?\s+v\s+[^\n@]+?)(?:\n|$)'),
      r'\s+vs\s+', ' v '
    ) AS parsed_match_name,
    REGEXP_EXTRACT(clean_detail, r'玩法：([^\n]+)') AS parsed_market_name,
    REGEXP_EXTRACT(clean_detail, r'(?:^|\n)([^@\n]+)@\d+(?:\.\d+)?') AS parsed_selection_name,
    REGEXP_CONTAINS(LOWER(CONCAT(IFNULL(game_name, ''), ' ', IFNULL(clean_detail, ''))), r'串关|parlay') AS is_parlay
  FROM raw
), wc AS (
  SELECT
    parsed.*,
    CASE
      WHEN is_parlay THEN '串关/多场'
      WHEN parsed_match_name IS NOT NULL THEN '单场赛事'
      ELSE '阶段盘口'
    END AS event_type,
    CASE
      WHEN is_parlay THEN '串关/多场'
      WHEN parsed_match_name IS NOT NULL THEN parsed_match_name
      ELSE CONCAT('阶段盘口：', IFNULL(parsed_market_name, '冠军/阶段'))
    END AS match_name,
    CASE
      WHEN is_parlay THEN '串关/多场'
      WHEN parsed_match_name IS NULL THEN '阶段盘口'
      WHEN DATE(match_time) <= DATE '2026-06-27' THEN '小组赛'
      WHEN DATE(match_time) BETWEEN DATE '2026-06-28' AND DATE '2026-07-03' THEN '32强'
      WHEN DATE(match_time) BETWEEN DATE '2026-07-04' AND DATE '2026-07-07' THEN '16强'
      WHEN DATE(match_time) BETWEEN DATE '2026-07-09' AND DATE '2026-07-11' THEN '8强'
      WHEN DATE(match_time) BETWEEN DATE '2026-07-14' AND DATE '2026-07-15' THEN '半决赛'
      WHEN DATE(match_time) = DATE '2026-07-18' THEN '季军赛'
      WHEN DATE(match_time) = DATE '2026-07-19' THEN '冠军赛'
      ELSE '未识别阶段'
    END AS match_stage,
    CASE
      WHEN parsed_match_name IS NULL AND NOT is_parlay THEN IFNULL(parsed_market_name, '冠军/阶段')
      ELSE play_type
    END AS market_name,
    CASE
      WHEN parsed_match_name IS NULL AND NOT is_parlay THEN parsed_selection_name
      ELSE NULL
    END AS selection_name
  FROM parsed
)
SELECT * FROM wc;
