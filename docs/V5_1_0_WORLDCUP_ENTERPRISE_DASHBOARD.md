# V5.1.0 World Cup Enterprise Dashboard

本版将世界杯专区升级为企业级 BI 页面。

## 新增

- `services/worldcup_service.py`：世界杯专区 BigQuery 服务层。
- `components/charts.py`：共用 Plotly 图表组件。
- `components/worldcup_cards.py`：世界杯专区 KPI 与版面组件。
- `features/worldcup_enterprise.py`：世界杯 V2 页面渲染。

## 修改

- `app_pages/worldcup.py` 改为使用 V2 页面。
- `version.py` 升级为 `v5.1.0`。

## 数据来源

- `agg_worldcup_match`
- `agg_worldcup_playtype`
- `agg_member_worldcup`
- `dim_member`
- `dim_game`

## 设计原则

世界杯专区不再直接查询 `raw_bet_detail`，也不再从投注详情解析比赛作为汇总依据。
所有单场比赛统计一律以 `game_id` 为唯一识别，并读取 V5 Data Warehouse 的 Aggregate Layer。
