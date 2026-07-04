# SQL 模組化規劃

`sql/` 目前先作為 SQL 集中管理的落點。

下一階段可以依功能拆成：

- `sql/finance.py`
- `sql/member.py`
- `sql/agent.py`
- `sql/upload.py`

原則：

1. Feature 頁面只呼叫函式，不直接拼大量 SQL。
2. SQL 參數化，避免字串散落在 UI 程式中。
3. BigQuery 查詢統一經過 `services.loader` 或 `services.bigquery_client`。
