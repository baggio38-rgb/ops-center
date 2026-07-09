# YEIP V6 数据字典

| 表名 | 层级 | 用途 | 使用页面 |
|---|---|---|---|
| raw_bet_detail | Raw | 原始投注上传 | 不直接给 Dashboard 使用 |
| fact_bet_detail | Fact | 去重投注明细 | ETL / Aggregate |
| dim_game | Dimension | 赛事维度，game_id 对应比赛 | 世界杯专区 / 运营总览 |
| dim_member | Dimension | 会员主档 | 会员中心 / 风控中心 |
| agg_dashboard_daily | Aggregate | 每日运营汇总 | 兼容旧首页 / V6 基础 |
| agg_dashboard_kpi | Aggregate | 运营总览 KPI | 运营总览 |
| agg_dashboard_hourly | Aggregate | 小时趋势 | 运营总览 |
| agg_dashboard_top | Aggregate | 排行榜 | 运营总览 |
| agg_worldcup_match | Aggregate | 世界杯单场汇总 | 世界杯专区 |
| agg_worldcup_playtype | Aggregate | 世界杯玩法汇总 | 世界杯专区 |
| agg_member_worldcup | Aggregate | 世界杯会员汇总 | 世界杯专区 |
