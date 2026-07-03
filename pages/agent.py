"""Agent and channel page wrappers.

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


def render_channel_agent_page():
    return _call('render_channel_agent')

def render_new_member_analysis_page():
    return _call('render_new_member_analysis')

def render_agent_member_matrix_page():
    return _call('render_agent_member_matrix')

def render_agent_market_monthly_page():
    return _call('render_agent_market_monthly')

def render_game_venue_page():
    return _call('render_game_venue')
