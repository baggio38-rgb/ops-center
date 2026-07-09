# v4 fix3

- 修正 dashboard.py 的上传函数名称。
- 如果 Streamlit App 不小心用 constants.py 当 main file，也会自动转回 dashboard.py。
- pages/*.py 改成兼容入口，避免左侧英文页造成空白。
- 新增 .streamlit/config.toml，关闭 Streamlit 内建 sidebar navigation。

建议 Streamlit Cloud 的 Main file path 仍然填写：dashboard.py
