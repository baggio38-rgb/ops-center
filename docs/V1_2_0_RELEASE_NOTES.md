# v1.2.0 首页与总裁驾驶舱

## 新增功能

- 新增 `features/home.py`
- 新增 `app_pages/home.py`
- 更新 `dashboard.py` 顶部导航
- 新增首页：经营概况、AI经营摘要、快捷入口、今日预警、系统状态
- 新增总裁驾驶舱：经营趋势、风险分布、高风险会员排行、高流水会员排行、AI经营建议
- 新增版本信息页

## 数据来源

- `fact_member_daily_v2`
- `mart_member_profile`
- `risk_member_score`

## 覆盖文件

```text
features/home.py
app_pages/home.py
dashboard.py
```

## Commit 建议

```text
Add homepage and executive dashboard v1.2.0
```

## 测试清单

- 首页可以打开
- 总裁驾驶舱可以打开
- 经营 KPI 有数据
- 风险分布图有数据
- 高风险会员排行有数据
- 高流水会员排行有数据
- 会员中心仍可打开
- 风控中心仍可打开
