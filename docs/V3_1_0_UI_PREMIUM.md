# v3.1.0 UI Premium

本版重点是统一「亿兆智能决策平台」的企业级 UI 风格，不改 BigQuery、ETL、上传逻辑，降低上线风险。

## 更新内容

1. 全平台统一简体中文 UI。
2. 新增企业级顶部状态栏：BigQuery、ETL、数据同步状态。
3. 统一 Header、KPI 卡片、提示卡、摘要卡、快速入口卡片样式。
4. 优化顶部导航：间距、圆角、换行、文字不再被切掉。
5. 修复 version.py 必要变量：APP_NAME、APP_VERSION、APP_VERSION_DATE。
6. 世界杯专区可继续沿用深绿 + 金色主题辅助类。

## 覆盖文件

```text
dashboard.py
components/ui.py
version.py
docs/V3_1_0_UI_PREMIUM.md
```

## 上线后检查

```text
1. App 可以正常启动
2. 顶部显示「亿兆智能决策平台」
3. 首页 KPI 卡片样式更新
4. 导航文字没有被切掉
5. 世界杯专区、数据中心、会员中心可正常进入
```

## Commit

```text
Apply UI Premium design system v3.1.0
```
