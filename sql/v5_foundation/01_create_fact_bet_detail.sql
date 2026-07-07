-- 亿兆智能决策平台 V5 Data Foundation
-- 01_create_fact_bet_detail.sql
-- 目的：建立全平台唯一投注事实表。
-- 规则：所有统计先按「注单流水号」去重，只保留 _imported_at 最新一笔。

CREATE OR REPLACE TABLE `mydata-494606.mydata.fact_bet_detail` AS
WITH src AS (
  SELECT
    t.*,
    NULLIF(TRIM(CAST(`注单流水号` AS STRING)), '') AS order_no_raw,
    NULLIF(TRIM(CAST(`游戏编号` AS STRING)), '') AS game_id_raw,
    NULLIF(TRIM(CAST(`会员账号` AS STRING)), '') AS member_account_raw,
    SAFE_CAST(`下注金额` AS FLOAT64) AS bet_amount_raw,
    SAFE_CAST(`有效投注` AS FLOAT64) AS valid_turnover_raw,
    SAFE_CAST(`盈亏` AS FLOAT64) AS profit_loss_raw,
    COALESCE(
      SAFE_CAST(_imported_at AS TIMESTAMP),
      TIMESTAMP '1970-01-01 00:00:00 UTC'
    ) AS imported_at_ts
  FROM `mydata-494606.mydata.raw_bet_detail` t
), keyed AS (
  SELECT
    *,
    -- 正常情况下以注单流水号去重；若极少数资料缺流水号，用整列 hash 避免把空白流水号全部合并成一笔。
    COALESCE(order_no_raw, CONCAT('__NO_ORDER__', CAST(FARM_FINGERPRINT(TO_JSON_STRING(src)) AS STRING))) AS dedup_key
  FROM src
)
SELECT
  -- 唯一键
  order_no_raw AS order_no,
  game_id_raw AS game_id,
  UPPER(TRIM(member_account_raw)) AS member_key,
  LOWER(TRIM(member_account_raw)) AS member_id,

  -- 原始显示字段
  member_account_raw AS member_account,
  CAST(`VIP等级` AS STRING) AS vip_level_raw,
  CAST(`场馆名称` AS STRING) AS provider_name,
  CAST(`场馆类型` AS STRING) AS provider_type,
  CAST(`游戏名称` AS STRING) AS game_name,
  CAST(`游戏类型` AS STRING) AS game_type,
  CAST(`货币类型` AS STRING) AS currency,
  CAST(`投注详情` AS STRING) AS bet_detail,
  CAST(`玩法` AS STRING) AS play_type,
  CAST(`盘口` AS STRING) AS handicap,
  SAFE_CAST(`欧赔` AS FLOAT64) AS odds,
  CAST(`状态` AS STRING) AS bet_status,

  -- 金额指标，会员视角
  bet_amount_raw AS bet_amount,
  SAFE_CAST(`手续费` AS FLOAT64) AS fee,
  SAFE_CAST(`场馆活动` AS FLOAT64) AS provider_promo,
  valid_turnover_raw AS valid_turnover,
  profit_loss_raw AS profit_loss,

  -- 平台视角
  -profit_loss_raw AS platform_profit,

  -- 时间字段：raw 目前为字符串，fact 统一尝试转 DATETIME，保留原始字符串
  CAST(`下注时间` AS STRING) AS bet_time_raw,
  SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING))) AS bet_time,
  DATE(SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING)))) AS report_date,

  CAST(`开赛时间` AS STRING) AS kickoff_time_raw,
  SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))) AS kickoff_time,

  CAST(`结算时间` AS STRING) AS settle_time_raw,
  SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`结算时间` AS STRING))) AS settle_time,

  -- 代理字段
  CAST(`上级代理ID` AS STRING) AS agent_id,
  CAST(`上级代理名称` AS STRING) AS agent_name,
  CAST(`上级代理编号` AS STRING) AS agent_code,

  -- 上传追踪
  CAST(_source_file AS STRING) AS source_file,
  imported_at_ts AS imported_at,
  CURRENT_TIMESTAMP() AS fact_updated_at
FROM keyed
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY dedup_key
  ORDER BY imported_at_ts DESC
) = 1;
