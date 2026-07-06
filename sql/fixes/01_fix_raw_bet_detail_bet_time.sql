-- v2.0.1 一次性修复：把 raw_bet_detail.`下注时间` 中的 Excel 日期序号
-- 例如 46209.21663194444 转成 2026-07-06 05:11:57。
-- 跑之前建议先备份表。

CREATE OR REPLACE TABLE `mydata-494606.mydata.raw_bet_detail_backup_before_time_fix` AS
SELECT * FROM `mydata-494606.mydata.raw_bet_detail`;

CREATE OR REPLACE TABLE `mydata-494606.mydata.raw_bet_detail` AS
SELECT
  * REPLACE (
    CASE
      WHEN REGEXP_CONTAINS(TRIM(CAST(`下注时间` AS STRING)), r'^\d+(\.\d+)?$')
           AND SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) BETWEEN 30000 AND 60000
        THEN FORMAT_DATETIME(
          '%Y-%m-%d %H:%M:%S',
          DATETIME_ADD(
            DATETIME '1899-12-30 00:00:00',
            INTERVAL CAST(ROUND(SAFE_CAST(TRIM(CAST(`下注时间` AS STRING)) AS FLOAT64) * 86400) AS INT64) SECOND
          )
        )
      WHEN SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING))) IS NOT NULL
        THEN FORMAT_DATETIME(
          '%Y-%m-%d %H:%M:%S',
          SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING)))
        )
      ELSE TRIM(CAST(`下注时间` AS STRING))
    END AS `下注时间`
  )
FROM `mydata-494606.mydata.raw_bet_detail`;

-- 验收：最新日期应该会到 7 月。
SELECT
  MAX(SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', `下注时间`)) AS latest_bet_time,
  COUNTIF(REGEXP_CONTAINS(`下注时间`, r'^\d+(\.\d+)?$')) AS still_excel_serial_rows
FROM `mydata-494606.mydata.raw_bet_detail`;
