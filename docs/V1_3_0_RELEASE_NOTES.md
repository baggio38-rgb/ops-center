# v1.3.0 CEO Dashboard Plus

## 更新内容

- 新增统一 UI 组件：`components/ui.py`
- 升级首页视觉与 KPI 卡片
- 升级总裁驾驶舱
- 新增 AI 经营摘要（规则版）
- 新增今日警报
- 新增经营健康度
- 新增 Top10 高价值会员
- 新增 Top10 代理
- 新增场馆分析
- 新增趋势区间切换：最近7天、最近30天、最近90天、今年

## 数据来源

- `fact_member_daily_v2`
- `mart_member_profile`
- `risk_member_score`

## 覆盖文件

```text
components/__init__.py
components/ui.py
features/home.py
app_pages/home.py
dashboard.py
docs/V1_3_0_RELEASE_NOTES.md
```

## 建议 Commit

```text
Add CEO dashboard plus v1.3.0
```

## 测试清单

- 首页可以打开
- 总裁驾驶舱可以打开
- 版本信息可以打开
- KPI 正常显示
- AI经营摘要正常显示
- 今日警报正常显示
- 风险分布正常显示
- Top10会员 / Top10代理正常显示
- 场馆分析正常显示
