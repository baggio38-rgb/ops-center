# v1.4.3 世界杯专区主题与 Logo 整合

## 更新内容

1. 使用用户提供的 PNG 原图作为世界杯专区 Logo。
2. Logo 不重新绘制、不改变内容、不套滤镜。
3. 新增世界杯专区专属配色：深绿、墨绿、金色、浅金。
4. 世界杯专区 Banner 改为 FIFA 2026 Logo + 世界杯专区标题。
5. 世界杯 KPI 卡片改为深绿金色风格。
6. 世界杯图表颜色改为：
   - 流水：金色
   - 有效投注：绿色
   - 会员盈亏：红色
   - 平台盈亏：浅金
7. 识别规则与 v1.4.2 保持一致：完整世界杯字串 + 排除 panda。

## 新增文件

```text
assets/fifa2026_logo.png
```

## 覆盖文件

```text
features/worldcup_center.py
assets/fifa2026_logo.png
docs/V1_4_3_WORLDCUP_THEME_LOGO.md
```

## 建议 Commit

```text
Add world cup theme and logo v1.4.3
```
