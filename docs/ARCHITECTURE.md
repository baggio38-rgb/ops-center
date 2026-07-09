# 系统架构

```text
CSV / Manual Upload
        ↓
Raw Tables
        ↓
Fact / Dimension
        ↓
Aggregate Layer
        ↓
Service Layer
        ↓
Streamlit Components
        ↓
Pages
```

## 规则

- 页面不得直接读取 Raw。
- 页面不得写业务 SQL。
- 业务计算集中在 BigQuery SQL / Aggregate。
- Streamlit 只做 UI、筛选与展示。
