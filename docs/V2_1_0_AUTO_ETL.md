# v2.1.0 自动 ETL 修正版

## 修正重点

本版解决首页「最新经营日停在 2026-06-29」的问题。

根因：

```text
raw_bet_detail 已经有 7 月资料
但是 fact_member_daily_v2 没有重新产生
首页读取 fact_member_daily_v2
所以首页仍然显示 6/29
```

## 本版新增

- `services/etl_refresh.py`
- 上传成功后自动重建：
  - `fact_member_daily_v2`
  - `mart_member_profile`
  - `risk_member_score`
- 数据上传页新增「同步核心资料表」按钮
- `import_tool.py` 上传投注记录前自动修正 Excel 日期序号
- `import_tool.py` CLI 上传后自动刷新核心资料表
- 新增手动 SQL：`sql/fixes/02_rebuild_core_marts.sql`

## 使用方式

覆盖文件后，进：

```text
🗂 数据管理 → 数据上传
```

按：

```text
同步核心资料表
```

或以后直接上传 Excel，系统会自动同步。

## 验收 SQL

```sql
SELECT
  MAX(report_date) AS latest_report_date,
  COUNT(*) AS total_rows
FROM `mydata-494606.mydata.fact_member_daily_v2`;
```

应显示 2026-07-06 或最新投注日。
