# v2.0.1 下注时间清洗修正

## 修正内容

- 修正 Streamlit 上传写入 BigQuery 前没有转换 Excel 日期序号的问题。
- 修正 `raw_bet_detail.下注时间` 混合出现：
  - `2026-06-29 23:52:05`
  - `46209.21663194444`
- 新增 `services/data_cleaner.py`。
- 上传页面写入 BigQuery 前会自动把 `下注时间` 统一成 `YYYY-MM-DD HH:MM:SS`。

## 覆盖文件

```text
features/upload_admin.py
services/data_cleaner.py
sql/fixes/01_fix_raw_bet_detail_bet_time.sql
docs/V2_0_1_DATE_CLEANER.md
```

## 上线后要做一次

到 BigQuery 执行：

```text
sql/fixes/01_fix_raw_bet_detail_bet_time.sql
```

执行完成后，首页的最新经营日应该可以抓到 7 月。
