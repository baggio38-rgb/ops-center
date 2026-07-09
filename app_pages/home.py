"""运营总览页面组。"""

from __future__ import annotations

from features.operation_overview import render_operation_overview
from features.home import render_version_page


HOME_PAGES = [
    ("运营总览", render_operation_overview),
    ("版本信息", render_version_page),
]
