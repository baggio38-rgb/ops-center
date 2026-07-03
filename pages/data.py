"""Data operations page wrappers.

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


def render_data_health_page():
    return _call('render_data_health')

def render_data_source_guide_page():
    return _call('render_data_source_guide')

def render_data_manage_page():
    return _call('render_data_manage')
