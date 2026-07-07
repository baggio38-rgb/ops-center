# 亿兆智能决策平台 v5.0.0 Data Foundation

## 本版目的

建立统一数据底座，修正过去各页面直接读取 `raw_bet_detail` 导致数字不一致的问题。

## 核心规则

1. Raw 永远保存原始资料，不直接做 Dashboard 汇整。
2. 所有投注统计先按 `注单流水号` 去重。
3. 去重规则：同一 `注单流水号` 保留 `_imported_at` 最新一笔。
4. 世界杯单场比赛一律使用 `游戏编号` 汇整，不再用投注详情或比赛名称。
5. 比赛名称只用于显示，来自 `dim_game`。

## 新增 BigQuery 表

### `fact_bet_detail`

全平台唯一投注事实表。

来源：

```text
raw_bet_detail -> 注单流水号去重 -> fact_bet_detail
```

主要字段：

| 字段 | 说明 |
|---|---|
| order_no | 注单流水号 |
| game_id | 游戏编号 |
| member_key | 会员唯一 Key，统一大写 |
| bet_amount | 下注金额 |
| valid_turnover | 有效投注 |
| profit_loss | 会员盈亏 |
| platform_profit | 平台盈亏，等于 -profit_loss |
| bet_detail | 投注详情，仅显示和分析使用 |
| source_file | 来源文件 |
| imported_at | 导入时间 |

### `dim_game`

赛事维度表。

世界杯专区以后通过：

```text
game_id -> dim_game.match_name
```

显示比赛名称。

## 执行顺序

在 BigQuery 依序执行：

1. `sql/v5_foundation/01_create_fact_bet_detail.sql`
2. `sql/v5_foundation/02_create_dim_game.sql`
3. `sql/v5_foundation/03_validate_v5_foundation.sql`

## 美国 v 比利时验收

已确认：

```text
美国 v 比利时 game_id = 5485584
```

执行：

```sql
SELECT *
FROM `mydata-494606.mydata.fact_bet_detail`
WHERE game_id = '5485584'
LIMIT 10;
```

或使用：

```text
sql/v5_foundation/04_query_worldcup_match_by_game_id.sql
```

## 后续开发规范

从 v5 开始，Dashboard、世界杯专区、风控中心、AI 分析都应优先读取：

```text
fact_bet_detail
```

不再直接读取：

```text
raw_bet_detail
```
