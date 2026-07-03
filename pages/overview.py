"""Finance overview page wrappers.

This v4 step keeps behavior stable by delegating to the existing
implementation functions in dashboard.py. Later steps can move the
actual implementation into these modules one page at a time.
"""

from __future__ import annotations

import sys


def _call(name: str):
    app = sys.modules.get("__main__")
    impl = getattr(app, name, None)
    if impl is None:
        raise RuntimeError(f"{name} is not available in the main Streamlit module")
    return impl()


def render_overview_page():
    return _call('render_overview')

def render_recent_trend_page():
    return _call('render_recent_trend')

def render_finance_channel_page():
    return _call('render_finance_channel')

def render_bonus_analysis_page():
    return _call('render_bonus_analysis')

def render_bonus_roi_agent_quality_page():
    return _call('render_bonus_roi_agent_quality')

def render_agent_commission_page():
    return _call('render_agent_commission')
