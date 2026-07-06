# v3.0.0 V7 上传引擎

## 本版重点

本版针对 Streamlit Cloud 上传大型 Excel/CSV 时出现 `Oh no. Error running app` 的问题，重构数据上传流程。

## 修正内容

1. 新增 V7 大档案稳定上传模式。
2. 上传流程从「全部文件先读入内存」改成「逐档处理、逐档写入、逐档释放」。
3. BigQuery 写入改为分批写入，可选择 10,000 / 20,000 / 50,000 / 100,000 rows。
4. 每个文件完成后自动 `del DataFrame` 与 `gc.collect()`，降低 RAM 峰值。
5. 上传完成后可自动同步核心资料表：
   - `fact_member_daily_v2`
   - `mart_member_profile`
   - `risk_member_score`
6. 上传完成后自动清除 Streamlit cache。
7. 新增 `upload_history` 写入逻辑，记录文件、行数、耗时、状态。
8. 保留原本上传流程，可通过关闭 V7 toggle 回到兼容模式。

## 使用方式

进入：

```text
🗂 数据管理 → 数据上传
```

确认开启：

```text
🚀 使用 V7 大档案稳定上传引擎
```

建议设置：

```text
BigQuery 分批写入大小：50000
上传完成后自动同步核心资料表：开启
```

然后按：

```text
🚀 开始 V7 稳定上传
```

## 注意事项

- V7 模式适合大型普通报表、投注记录、平台报表、财务报表等。
- 代理佣金、代理结算这类需要整月读改写的特殊报表，若 V7 提示不处理，请关闭 V7 使用兼容模式上传。
- 若上传非常大的单一 xlsx，Streamlit 仍需要先读取该 xlsx，但 V7 不会再把多个 DataFrame 长时间堆在 session 里。

## Commit 建议

```text
Add V7 stable upload engine v3.0.0
```
