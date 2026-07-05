"""首页与总裁驾驶舱页面组。"""

from __future__ import annotations

from features.home import render_executive_dashboard, render_home_page, render_version_page


HOME_PAGES = [
    ("首页", render_home_page),
    ("总裁驾驶舱", render_executive_dashboard),
    ("版本信息", render_version_page),
]
