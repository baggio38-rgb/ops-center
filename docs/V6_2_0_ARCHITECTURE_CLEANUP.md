# V6.2.0 Architecture Cleanup

## 目标

本次整理以「不改业务逻辑、不改 BigQuery 架构」为原则，先清掉 V6.0/V6.1 期间累积的页面与样式重复问题。

## 已完成

- 移除压缩包中的 `.git` 与 `__pycache__`，避免覆盖本机 Git 记录与缓存。
- 将旧 `pages/` Streamlit 多页面目录移到 `_archive/legacy_pages/pages`，避免和 `dashboard.py` 的自定义导航重复。
- 将根目录旧版说明文件移到 `_archive/root_notes`，根目录更干净。
- 修正 `components/kpi_card.py`，补齐 `kpi_card`、`fmt_compact_number`、`fmt_percent` 等 V6 运营总览使用的函数。
- 修正 `features/operation_overview.py`，移除页面内联 CSS，统一改用 `utils/style_loader.load_css()`。
- 将 V6 运营总览相关样式集中到 `assets/css/main.css`。
- 升级 `utils/style_loader.py`，使用绝对路径读取 CSS，并使用 `st.markdown(..., unsafe_allow_html=True)` 注入样式。
- 版本号更新为 `v6.2.0`。

## 重点修正

### CSS 被显示在页面上的问题

原先部分页面在 Python 内拼接 `<style>...</style>`。本次整理后，运营总览相关样式统一进入：

```text
assets/css/main.css
```

页面只调用：

```python
from utils.style_loader import load_css
load_css()
```

### 目录整理

保留当前主入口：

```text
dashboard.py
```

保留当前自定义页面组：

```text
app_pages/
features/
```

旧 Streamlit 多页目录已归档：

```text
_archive/legacy_pages/pages
```

## 使用方式

1. 先备份当前专案。
2. 将本包内容覆盖到 `G:\Projects\ops-center`。
3. 在 PowerShell 执行：

```powershell
cd G:\Projects\ops-center
python -m compileall .
streamlit run dashboard.py
```

4. 确认运营总览页面不再显示 `<style>...</style>`。

## Git 建议

覆盖后建议执行：

```powershell
git status
git add .
git commit -m "refactor: clean V6.2 architecture and centralize CSS"
git tag v6.2.0-cleanup
```
