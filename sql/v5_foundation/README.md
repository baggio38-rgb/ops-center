# V5.3 Auto Refresh SQL

SQL 已内建在：

```text
services/etl_refresh.py
```

请优先在系统页面执行：

```text
数据中心 → 数据上传 → V5.3 自动刷新
```

不要再手动输入 `CREATE OR REPLACE TABLE ... AS SELECT ...` 的半截 SQL，避免把聚合表覆盖成错误版本。
