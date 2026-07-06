# 亿兆智能决策平台 v4.0.0 Enterprise UI

## 本版重点

- 改为企业级左侧导航，不再依赖顶部 Radio 作为主导航。
- 新增 Enterprise Header，显示当前位置、系统状态与全局搜索占位。
- 全站深色企业风格，强化 BI / 数据中台质感。
- 统一 Design System：颜色、卡片、状态、侧边栏、Footer。
- 保留原有功能页面与 BigQuery / ETL 逻辑，降低上线风险。

## 覆盖文件

```text
dashboard.py
components/ui.py
version.py
docs/V4_0_0_ENTERPRISE_UI.md
```

## 验收清单

1. App 能正常启动。
2. 左侧显示企业级导航菜单。
3. 顶部显示「亿兆智能决策平台」和系统状态。
4. 首页 KPI、AI 摘要、警报能正常显示。
5. 数据中心、世界杯专区、会员中心、风控中心都能进入。
6. 页面文字维持简体中文。

## Commit 建议

```text
Apply Enterprise UI layout v4.0.0
```
