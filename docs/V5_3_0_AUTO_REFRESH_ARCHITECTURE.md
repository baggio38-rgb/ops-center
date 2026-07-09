# V5.3.0 Auto Refresh Architecture

本版新增「V5.3 自动刷新」：上传资料后，一次重建从 Raw 到 Dashboard 所需的核心表，避免上传 CSV 后世界杯专区仍显示旧数字。

## 自动刷新流程

```text
raw_bet_detail
  ↓
fact_bet_detail                # 按注单流水号去重
  ↓
dim_game                       # 按游戏编号建立世界杯赛事维度
  ↓
fact_worldcup_bet              # 世界杯专用事实表
  ↓
agg_worldcup_match             # 世界杯单场汇总
agg_worldcup_playtype          # 世界杯玩法汇总
agg_member_worldcup            # 世界杯会员汇总
agg_dashboard_daily            # 首页日汇总
```

同时保留并执行既有核心表：

```text
fact_member_daily_v2
mart_member_profile
risk_member_score
```

## 使用方式

进入：

```text
数据中心 → 数据上传
```

点击：

```text
V5.3 自动刷新（raw → fact → dim → agg → Dashboard）
立即执行 V5.3 自动刷新
```

或在上传资料时勾选：

```text
上传完成后自动执行 V5.3 全量刷新
```

## 解决的问题

过去上传新投注记录后，如果没有手动重建 `agg_worldcup_match`，Dashboard 仍会显示旧数字。

V5.3 会统一重建：

- `fact_bet_detail`
- `dim_game`
- `fact_worldcup_bet`
- `agg_worldcup_match`
- `agg_worldcup_playtype`
- `agg_member_worldcup`
- `agg_dashboard_daily`

这样世界盃专区、首页和会员/风控相关数据会同步更新。

## 验证 SQL

```sql
SELECT
  game_id,
  match_name,
  bet_count,
  member_count,
  bet_amount,
  valid_turnover,
  member_profit_loss,
  platform_profit_loss,
  updated_at
FROM `mydata-494606.mydata.agg_worldcup_match`
WHERE game_id = '5488402';
```

若 `updated_at` 是刚刚刷新后的时间，代表聚合表已重建。
