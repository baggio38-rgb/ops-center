# 系统架构设计

## Data Flow

```text
CSV Upload
  -> raw_*
  -> fact_*
  -> dim_*
  -> agg_*
  -> Service Layer
  -> Streamlit Dashboard
```

## Layers

### Raw Layer
保留原始上传资料，不直接提供 Dashboard 使用。

### Fact Layer
清洗后、去重后的事实资料，例如 `fact_bet_detail`。

### Dimension Layer
维度主档，例如 `dim_game`、`dim_member`。

### Aggregate Layer
Dashboard 唯一主要读取来源，例如：

- `agg_dashboard_daily`
- `agg_worldcup_match`
- `agg_worldcup_playtype`
- `agg_member_worldcup`

### Service Layer
Python 服务层，页面不得直接写复杂 SQL。

### UI Layer
Streamlit 页面只负责展示和互动。
