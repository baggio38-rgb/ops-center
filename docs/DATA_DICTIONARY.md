# 数据字典

| Table | Layer | Purpose | Dashboard Usage |
|---|---|---|---|
| raw_bet_detail | Raw | 原始投注记录 | No |
| fact_bet_detail | Fact | 流水号去重后的投注明细 | No |
| fact_worldcup_bet | Fact | 世界杯投注明细 | No |
| dim_game | Dimension | 比赛维度，game_id 识别赛事 | Yes |
| dim_member | Dimension | 会员主档 | Yes |
| agg_dashboard_daily | Aggregate | 运营总览每日汇总 | Yes |
| agg_worldcup_match | Aggregate | 世界杯单场汇总 | Yes |
| agg_worldcup_playtype | Aggregate | 世界杯玩法汇总 | Yes |
| agg_member_worldcup | Aggregate | 世界杯会员汇总 | Yes |

## Metric Definition

| Metric | Definition |
|---|---|
| bet_count | 去重后的注单数量 |
| member_count | 去重后投注会员数 |
| bet_amount | SUM(下注金额) |
| valid_turnover | SUM(有效投注) |
| member_profit_loss | SUM(盈亏) |
| platform_profit_loss | -SUM(盈亏) |
| platform_roi | platform_profit_loss / valid_turnover |
