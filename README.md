# Ops Center

Streamlit-based operations data platform.

## Current structure

- `dashboard.py`：主入口與中文導航
- `app_pages/`：頁面群組註冊
- `features/`：各功能模組實作
- `components/`：共用 UI / filter / metric helpers
- `services/`：BigQuery 與資料載入服務
- `utils/`：格式化與 DataFrame 工具
- `core/legacy.py`：過渡期相容核心，後續會逐步清空
- `sql/`：SQL 模組化預留位置

## Smoke test

```bash
python -m compileall .
python scripts/smoke_test.py
```

## Deployment

Main file path:

```text
dashboard.py
```

Streamlit secrets must include `gcp_service_account` when service-account access is required.
