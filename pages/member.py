"""Member value page wrappers.

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


def render_member_value_page():
    return _call('render_member_value')

def render_bet_analysis_page():
    return _call('render_bet_analysis')

def render_cs_analysis_page():
    return _call('render_cs_analysis')

def render_winback_page():
    return _call('render_winback')

def render_realtime_page():
    return _call('render_realtime')
