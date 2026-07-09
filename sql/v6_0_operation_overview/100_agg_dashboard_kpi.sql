CREATE OR REPLACE TABLE `mydata-494606.mydata.agg_dashboard_kpi` AS
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (ORDER BY report_date DESC) AS rn
  FROM `mydata-494606.mydata.agg_dashboard_daily`
), base AS (
  SELECT
    t.report_date,
    t.bet_count,
    t.member_count,
    t.bet_amount,
    t.valid_turnover,
    t.member_profit_loss,
    t.platform_profit_loss,
    t.worldcup_turnover,
    t.sportsbook_turnover,
    t.casino_turnover,
    SAFE_DIVIDE(t.platform_profit_loss, NULLIF(t.valid_turnover, 0)) AS platform_roi,
    SAFE_DIVIDE(t.member_profit_loss, NULLIF(t.valid_turnover, 0)) AS member_rtp,
    y.bet_amount AS prev_bet_amount,
    y.valid_turnover AS prev_valid_turnover,
    y.platform_profit_loss AS prev_platform_profit_loss,
    y.member_count AS prev_member_count,
    SAFE_DIVIDE(t.bet_amount - y.bet_amount, NULLIF(y.bet_amount, 0)) AS bet_amount_delta,
    SAFE_DIVIDE(t.valid_turnover - y.valid_turnover, NULLIF(y.valid_turnover, 0)) AS valid_turnover_delta,
    SAFE_DIVIDE(t.platform_profit_loss - y.platform_profit_loss, NULLIF(ABS(y.platform_profit_loss), 0)) AS platform_profit_delta,
    SAFE_DIVIDE(t.member_count - y.member_count, NULLIF(y.member_count, 0)) AS member_count_delta,
    t.updated_at
  FROM ranked t
  LEFT JOIN ranked y ON y.rn = t.rn + 1
)
SELECT * FROM base;
