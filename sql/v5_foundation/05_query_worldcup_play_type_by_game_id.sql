-- 单场世界杯玩法拆分查询模板
-- 美国 v 比利时 = 5485584

DECLARE target_game_id STRING DEFAULT '5485584';

SELECT
  f.game_id,
  ANY_VALUE(g.match_name) AS match_name,
  f.play_type,
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
GROUP BY f.game_id, f.play_type
ORDER BY total_valid_turnover DESC;
