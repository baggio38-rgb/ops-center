# V5.1.1 World Cup Enterprise Dashboard Fix

本版修正世界杯专区 V2 在读取筛选条件时，BigQuery ARRAY 栏位与 Pandas / numpy array 的兼容问题。

## 修正

- 修正 `services/worldcup_service.py` 的球队筛选。
- 新增 `_as_list()`，安全处理 `None`、list、tuple、set、numpy array 与 scalar。
- 修正 `get_worldcup_kpi()` 的会员数口径，筛选阶段 / 球队后会从 `fact_worldcup_bet` 重新计算去重会员数。
- 版本升级为 `v5.1.1`。

## 影响范围

- `services/worldcup_service.py`
- `version.py`
- `docs/V5_1_1_WORLDCUP_ENTERPRISE_DASHBOARD_FIX.md`

## 数据来源

- `agg_worldcup_match`
- `agg_worldcup_playtype`
- `agg_member_worldcup`
- `fact_worldcup_bet`
- `dim_member`
