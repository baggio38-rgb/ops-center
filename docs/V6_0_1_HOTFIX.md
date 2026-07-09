# V6.0.1 Hotfix

## 修正内容

- 修正运营总览 CSS 被页面显示为代码区块的问题。
- 运营总览改为读取既有稳定表 `agg_dashboard_daily`。
- 移除运营总览对 `agg_dashboard_kpi`、`agg_dashboard_hourly`、`agg_dashboard_top` 的强依赖。
- 排行榜改用既有 `agg_worldcup_match` 与 `agg_member_worldcup` 作为兼容来源。
- 数据查询异常不再直接把 BigQuery 404 错误显示给使用者。

## 部署方式

直接覆盖现有项目后重新部署 Streamlit。

## BigQuery

本版不需要新增 BigQuery 表。
