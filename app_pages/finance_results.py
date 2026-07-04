"""Finance results page group.

This module intentionally imports stable render implementations from ops_core.
It is not a Streamlit multipage file, so it will not appear in the sidebar.
"""

from __future__ import annotations

from ops_core import (
    render_overview,
    render_recent_trend,
    render_finance_channel,
    render_bonus_analysis,
    render_bonus_roi_agent_quality,
    render_agent_commission,
)

FINANCE_RESULT_PAGES = [
    ("经营总览", render_overview),
    ("近期走势(日报)", render_recent_trend),
    ("存取款分析", render_finance_channel),
    ("红利分析", render_bonus_analysis),
    ("红利 ROI & 代理质量", render_bonus_roi_agent_quality),
    ("代理佣金 & 退成", render_agent_commission),
]
