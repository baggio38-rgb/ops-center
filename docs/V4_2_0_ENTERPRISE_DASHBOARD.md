# v4.2.0 Enterprise Dashboard UI

本版重点：

- 副功能从左侧移到页面顶部 Tabs。
- 删除页面内重复的大型 Header，只保留全局企业 Header。
- 首页 KPI 卡片改为深色玻璃风格。
- KPI 卡片上下间距加大，解决卡片太靠近的问题。
- AI 经营摘要改成暗色 AI 卡片风格。
- 今日警报改成暗色通知卡风格。
- 页面最大宽度提升到 1840px，更适合 2K / 4K 屏幕。
- 全站 UI 文案保持简体中文。

覆盖文件：

- dashboard.py
- components/ui.py
- version.py
- docs/V4_2_0_ENTERPRISE_DASHBOARD.md

上线后验收：

1. App 可以正常启动。
2. 左侧只显示主功能，不再显示副功能列表。
3. 副功能出现在页面顶部。
4. 首页不再出现两个「亿兆智能决策平台」Header。
5. 今日经营概况 KPI 上下两排间距明显变大。
6. 首页卡片变成深色玻璃风格。
