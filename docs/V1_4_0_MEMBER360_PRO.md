# v1.4.0 Member360 Pro

## 本次更新

新增 Member360 Pro 第一版，目标是让客服、VIP、风控人员在 30 秒内完成会员判断。

## 覆盖文件

- `features/member360.py`
- `docs/V1_4_0_MEMBER360_PRO.md`

## 主要功能

- 新版会员总览
- 风险分、会员价值、忠诚度三大评分
- 规则版 AI 会员摘要
- 自动标签
- 风险原因说明
- 核心 KPI 卡片
- 7 / 30 / 90 天趋势切换
- 游戏类型偏好
- 最近 80 笔注单
- 注单搜索与 CSV 下载

## 数据来源

- `mart_member_profile`
- `risk_member_score`
- `fact_member_daily_v2`
- `raw_bet_detail`

## 验收清单

- 可以搜索会员
- 会员总览正常显示
- 三大评分正常显示
- AI 摘要正常生成
- KPI 正常显示
- 趋势图正常显示
- 游戏偏好正常显示
- 最近投注正常显示
