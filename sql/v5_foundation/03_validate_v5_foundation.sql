-- 亿兆智能决策平台 V5 Data Foundation 验收 SQL

-- 1) raw 与 fact 笔数对比：fact 应等于去重后的注单数。
SELECT
  (SELECT COUNT(*) FROM `mydata-494606.mydata.raw_bet_detail`) AS raw_rows,
  (SELECT COUNT(DISTINCT NULLIF(TRIM(CAST(`注单流水号` AS STRING)), '')) FROM `mydata-494606.mydata.raw_bet_detail`) AS distinct_order_no,
  (SELECT COUNT(*) FROM `mydata-494606.mydata.fact_bet_detail`) AS fact_rows;

-- 2) 检查 fact 是否仍有重复流水号。
SELECT
  order_no,
  COUNT(*) AS duplicate_count
FROM `mydata-494606.mydata.fact_bet_detail`
WHERE order_no IS NOT NULL
GROUP BY order_no
HAVING duplicate_count > 1
LIMIT 20;

-- 3) 美国 v 比利时，按 game_id 汇总，游戏编号已经确认是 5485584。
SELECT
  f.game_id,
  ANY_VALUE(g.stage) AS stage,
  ANY_VALUE(g.match_name) AS match_name,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT f.member_key) AS bettor_count,
  SUM(f.bet_amount) AS total_bet_amount,
  SUM(f.valid_turnover) AS total_valid_turnover,
  SUM(f.profit_loss) AS member_profit_loss,
  SUM(f.platform_profit) AS platform_profit
FROM `mydata-494606.mydata.fact_bet_detail` f
LEFT JOIN `mydata-494606.mydata.dim_game` g
ON f.game_id = g.game_id
WHERE f.game_id = '5485584'
GROUP BY f.game_id;

-- 4) 世界杯赛事维度预览。
SELECT
  game_id,
  stage,
  match_name,
  kickoff_time
FROM `mydata-494606.mydata.dim_game`
WHERE tournament = '世界杯2026'
ORDER BY kickoff_time DESC
LIMIT 50;
