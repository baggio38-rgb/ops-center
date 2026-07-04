# V7.0 Stable Foundation

本包是 v7 的穩定化基礎，不改現有功能邏輯，重點是建立後續長期維護需要的落點。

## 本次新增

- `components/`
  - `ui.py`：Hero、Section、Metric Card、Badge 等 UI helper 的穩定入口
  - `filters.py`：日期篩選、多選篩選等 helper 的穩定入口
  - `metrics.py`：指標口徑說明 helper
- `services/loader.py`
  - `load_table`、`query_bq`、`latest_imported_at` 的穩定入口
- `sql/README.md`
  - 下一階段 SQL 模組化規劃
- `scripts/smoke_test.py`
  - 本機 / CI 可用的 import 與導航煙霧測試
- `tests/test_smoke_imports.py`
  - pytest 形式煙霧測試
- `.github/workflows/smoke-test.yml`
  - Push / PR 自動做 compile 與 smoke test

## 設計原則

目前 `components` 與 `services.loader` 先委派到 `core.legacy`，這是刻意的：

1. 不改任何既有頁面的行為。
2. 先建立穩定 import path。
3. 後續再把實作逐步從 `core.legacy` 移入 components / services。

## 建議 Commit Message

```text
v7.0 add stable components and smoke tests
```
