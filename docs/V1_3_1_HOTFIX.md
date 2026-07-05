# v1.3.1 UI Hotfix

## 修正内容

- 修正顶部导航文字被切掉的问题。
- 修正首页区块标题在深色背景下不清楚的问题。
- 修正「今日警报」白底白字导致文字看不到的问题。
- 修正「快捷入口」区块文字对比不足的问题。
- 修正「系统状态」查询 `risk_member_score.updated_at` 不存在导致 400 错误的问题。

## 覆盖文件

```text
components/ui.py
features/home.py
dashboard.py
docs/V1_3_1_HOTFIX.md
```

## 建议 Commit

```text
Fix v1.3.1 dashboard UI and system status
```
