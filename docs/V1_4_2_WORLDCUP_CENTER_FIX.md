# v1.4.2 世界杯专区修正版

## 修正内容

1. 世界杯注单识别规则统一为：

```sql
`投注详情` LIKE '%世界杯2026(在加拿大、墨西哥&美国)%'
AND LOWER(`投注详情`) NOT LIKE '%panda%'
```

2. 修正世界杯总览 KPI：

- 总流水
- 有效投注
- 会员盈亏
- 平台盈亏
- RTP
- 投注会员

3. 新增阶段汇总：

- 小组赛
- 32强
- 16强
- 8强
- 半决赛
- 季军赛
- 冠军赛
- 串关/多场

4. 新增世界杯资料库页面，可查看每场比赛数据。

## 盈亏定义

- 会员盈亏 = `SUM(盈亏)`
- 平台盈亏 = `-SUM(盈亏)`

## 部署文件

覆盖：

```text
features/worldcup_center.py
app_pages/worldcup.py
docs/V1_4_2_WORLDCUP_CENTER_FIX.md
```

建议 Commit：

```text
Fix world cup center metrics v1.4.2
```
