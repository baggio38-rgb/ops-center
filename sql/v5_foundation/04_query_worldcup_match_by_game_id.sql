-- 单场世界杯比赛查询模板
-- 使用方式：把 @game_id 改成目标游戏编号，或在 BigQuery 参数中设置 game_id。
-- 美国 v 比利时 = 5485584

DECLARE target_game_id STRING DEFAULT '5485584';

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
WHERE f.game_id = target_game_id
GROUP BY f.game_id;
