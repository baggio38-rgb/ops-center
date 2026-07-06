-- v2.0.0 optional mart table for faster dashboards
CREATE OR REPLACE TABLE `mydata-494606.mydata.mart_worldcup_match` AS
WITH wc AS (
  -- Paste contents of 01_worldcup_engine_cte.sql here, or replace this CTE with your scheduled parser view.
  SELECT * FROM `mydata-494606.mydata.raw_bet_detail` WHERE FALSE
)
SELECT
  match_stage,
  match_name,
  MIN(match_time) AS match_time,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT member_key) AS members,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS member_profit_loss,
  -SUM(profit_loss) AS platform_profit_loss,
  SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS rtp
FROM wc
WHERE event_type = '单场赛事'
GROUP BY match_stage, match_name;
