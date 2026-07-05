# v1.4.1 世界杯专区

## 新增内容

- 新增主菜单：`⚽ 世界杯专区`
- 新增页面：
  - 世界杯总览
  - 比赛监控
  - 玩家分析
  - 识别规则

## 数据来源

- `mydata-494606.mydata.raw_bet_detail`

## 世界杯注单识别规则

```sql
投注详情 包含：世界杯2026 / FIFA世界杯2026 / World Cup 2026
并且投注详情不包含：panda
```

## 覆盖文件

```text
features/worldcup_center.py
app_pages/worldcup.py
dashboard.py
docs/V1_4_1_WORLDCUP_CENTER.md
```

## 建议 Commit

```text
Add world cup center v1.4.1
```

## 下一版建议

- 建立 `dim_worldcup_match`
- 建立 `fact_worldcup_bet`
- 串关注单拆单
- 加入赛前/滚球/早盘分类
