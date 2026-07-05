"""风控中心页面组。"""

from __future__ import annotations

from features.risk_center import render_risk_overview, render_risk_rules


RISK_CENTER_PAGES = [
    ("风险总览", render_risk_overview),
    ("规则说明", render_risk_rules),
]
