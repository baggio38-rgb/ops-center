# V6.0.0 Operation Overview

## 新增

- 新首页：运营总览
- 新组件：page_header、kpi_card、status_badge、section_title、chart_card
- 新服务：services/dashboard_service.py
- 新 SQL：agg_dashboard_kpi、agg_dashboard_hourly、agg_dashboard_top
- V5.3 自动刷新流程新增 V6 三张运营总览 Aggregate

## 数据来源

运营总览只读取 Aggregate：

- `agg_dashboard_kpi`
- `agg_dashboard_hourly`
- `agg_dashboard_top`

若新表尚未建立，页面会优雅退回 `agg_dashboard_daily` 或世界杯排行，保证旧系统不中断。

## 验收

1. 左侧菜单显示「运营总览」
2. 进入后默认副功能为「运营总览」
3. KPI 卡片可显示今日投注金额、有效投注、平台盈亏、活跃会员
4. 若已执行 V6 SQL，可显示小时趋势与排行榜
5. 数据中心执行 V5.3 自动刷新后，会同步重建 V6 运营总览 Aggregate
