# v2.0.0 World Cup Engine

## 修正重点

1. 修正 BigQuery `Unclosed string literal`，所有 Regex 里的换行都改成 BigQuery 可执行的 `\\n`。
2. 世界杯注单统一识别：`世界杯2026(在加拿大、墨西哥&美国)`。
3. 排除 `panda`。
4. 注单分类：
   - 单场赛事：投注详情包含 `A队 v B队`
   - 阶段盘口：入围16强、冠军盘口等，没有 A v B
   - 串关/多场：串关、parlay
5. 战情室、TOP10、比赛监控只统计真正的单场赛事，阶段盘口不会再污染赛事排行。

## 覆盖文件

- `features/worldcup_center.py`
- `app_pages/worldcup.py`
- `dashboard.py`
- `services/worldcup_parser.py`
- `assets/fifa2026_logo.png`
- `sql/worldcup/01_worldcup_engine_cte.sql`
- `sql/worldcup/02_create_mart_worldcup_match.sql`

## 上线后验收

1. 世界杯专区可以打开，不再出现 `Unclosed string literal`。
2. 战情室不再出现 `未识别赛事`。
3. `入围16强` 显示为 `阶段盘口`，不进入赛事 TOP10。
4. TOP10 流水赛事只显示 `巴西 v 日本` 这种单场比赛。
5. 总览 KPI 与 BigQuery 验证 SQL 数字一致。

## Commit

```text
Build world cup engine v2.0.0
```
