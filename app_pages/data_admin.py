"""Data admin page group."""

from __future__ import annotations

from features.upload_admin import (
    render_data_source_guide,
    _render_data_upload_impl,
    render_data_manage,
)
from features.realtime_health import render_data_health


DATA_ADMIN_PAGES = [
    ("🩺 数据健康", render_data_health),
    ("📖 数据说明", render_data_source_guide),
    ("月度报表上传", _render_data_upload_impl),
    ("删除数据", render_data_manage),
]
