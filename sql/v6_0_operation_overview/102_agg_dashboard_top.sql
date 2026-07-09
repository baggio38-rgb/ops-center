CREATE OR REPLACE TABLE `mydata-494606.mydata.agg_dashboard_top` AS
WITH latest_day AS (
  SELECT MAX(DATE(
CASE
  WHEN REGEXP_CONTAINS(TRIM(CAST(`下注时间` AS STRING)), r'^\d+(\.\d+)?$')
       AND SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) BETWEEN 30000 AND 60000
    THEN DATETIME_ADD(
      DATETIME '1899-12-30 00:00:00',
      INTERVAL CAST(ROUND(SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) * 86400) AS INT64) SECOND
    )
  ELSE SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING)))
END
)) AS report_date
  FROM `mydata-494606.mydata.fact_bet_detail`
  WHERE DATE(
CASE
  WHEN REGEXP_CONTAINS(TRIM(CAST(`下注时间` AS STRING)), r'^\d+(\.\d+)?$')
       AND SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) BETWEEN 30000 AND 60000
    THEN DATETIME_ADD(
      DATETIME '1899-12-30 00:00:00',
      INTERVAL CAST(ROUND(SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) * 86400) AS INT64) SECOND
    )
  ELSE SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING)))
END
) IS NOT NULL
), clean AS (
  SELECT
    DATE(
CASE
  WHEN REGEXP_CONTAINS(TRIM(CAST(`下注时间` AS STRING)), r'^\d+(\.\d+)?$')
       AND SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) BETWEEN 30000 AND 60000
    THEN DATETIME_ADD(
      DATETIME '1899-12-30 00:00:00',
      INTERVAL CAST(ROUND(SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) * 86400) AS INT64) SECOND
    )
  ELSE SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING)))
END
) AS report_date,
    TRIM(CAST(`会员账号` AS STRING)) AS member_id,
    TRIM(CAST(`场馆名称` AS STRING)) AS provider_name,
    TRIM(CAST(`游戏名称` AS STRING)) AS game_name,
    SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64) AS bet_amount,
    SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64) AS valid_turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64) AS member_profit_loss
  FROM `mydata-494606.mydata.fact_bet_detail`
  WHERE DATE(
CASE
  WHEN REGEXP_CONTAINS(TRIM(CAST(`下注时间` AS STRING)), r'^\d+(\.\d+)?$')
       AND SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) BETWEEN 30000 AND 60000
    THEN DATETIME_ADD(
      DATETIME '1899-12-30 00:00:00',
      INTERVAL CAST(ROUND(SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) * 86400) AS INT64) SECOND
    )
  ELSE SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING)))
END
) = (SELECT report_date FROM latest_day)
), provider_top AS (
  SELECT report_date, '热门场馆' AS metric_type, provider_name AS item_id, provider_name AS item_name,
         COUNT(*) AS bet_count, COUNT(DISTINCT member_id) AS member_count,
         SUM(bet_amount) AS bet_amount, SUM(valid_turnover) AS valid_turnover,
         SUM(member_profit_loss) AS member_profit_loss, -SUM(member_profit_loss) AS platform_profit_loss
  FROM clean WHERE provider_name IS NOT NULL AND provider_name != '' GROUP BY report_date, provider_name
), game_top AS (
  SELECT report_date, '热门游戏' AS metric_type, game_name AS item_id, game_name AS item_name,
         COUNT(*) AS bet_count, COUNT(DISTINCT member_id) AS member_count,
         SUM(bet_amount) AS bet_amount, SUM(valid_turnover) AS valid_turnover,
         SUM(member_profit_loss) AS member_profit_loss, -SUM(member_profit_loss) AS platform_profit_loss
  FROM clean WHERE game_name IS NOT NULL AND game_name != '' GROUP BY report_date, game_name
), member_top AS (
  SELECT report_date, '高贡献会员' AS metric_type, member_id AS item_id, member_id AS item_name,
         COUNT(*) AS bet_count, 1 AS member_count,
         SUM(bet_amount) AS bet_amount, SUM(valid_turnover) AS valid_turnover,
         SUM(member_profit_loss) AS member_profit_loss, -SUM(member_profit_loss) AS platform_profit_loss
  FROM clean WHERE member_id IS NOT NULL AND member_id != '' GROUP BY report_date, member_id
), match_top AS (
  SELECT CURRENT_DATE() AS report_date, '热门赛事' AS metric_type, game_id AS item_id, match_name AS item_name,
         bet_count, member_count, bet_amount, valid_turnover, member_profit_loss, platform_profit_loss
  FROM `mydata-494606.mydata.agg_worldcup_match`
)
SELECT *, CURRENT_TIMESTAMP() AS updated_at
FROM (
  SELECT * FROM provider_top
  UNION ALL SELECT * FROM game_top
  UNION ALL SELECT * FROM member_top
  UNION ALL SELECT * FROM match_top
)
QUALIFY ROW_NUMBER() OVER (PARTITION BY metric_type ORDER BY valid_turnover DESC, platform_profit_loss DESC) <= 30;
