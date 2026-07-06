-- v2.1.0 Core ETL: rebuild Dashboard / Member360 / Risk Center marts from raw_bet_detail.
-- Use this only if you want to run manually in BigQuery.
-- Streamlit upload page now runs the same refresh automatically after successful uploads.

CREATE OR REPLACE TABLE `mydata-494606.mydata.fact_member_daily_v2` AS
WITH clean AS (
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
    UPPER(REGEXP_REPLACE(TRIM(CAST(`会员账号` AS STRING)), r'[^A-Za-z0-9]', '')) AS member_key,
    TRIM(CAST(`会员账号` AS STRING)) AS member_id,
    SAFE_CAST(REPLACE(TRIM(CAST(`下注金额` AS STRING)), ',', '') AS FLOAT64) AS turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`有效投注` AS STRING)), ',', '') AS FLOAT64) AS valid_turnover,
    SAFE_CAST(REPLACE(TRIM(CAST(`盈亏` AS STRING)), ',', '') AS FLOAT64) AS profit_loss
  FROM `mydata-494606.mydata.raw_bet_detail`
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
  0 AS active_minutes,
  CURRENT_TIMESTAMP() AS updated_at
FROM clean
WHERE report_date IS NOT NULL AND member_key IS NOT NULL AND member_key != ''
GROUP BY report_date, member_key;

SELECT
  MAX(report_date) AS latest_report_date,
  COUNT(*) AS total_rows
FROM `mydata-494606.mydata.fact_member_daily_v2`;
