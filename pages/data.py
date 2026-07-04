"""Data operations page wrappers.

This v4 step keeps behavior stable by delegating to the existing
implementation functions in dashboard.py. Later steps can move the
actual implementation into these modules one page at a time.
"""

from __future__ import annotations

import sys


def _call(name: str):
    # Streamlit Cloud may load the app as module name "dashboard" instead of "__main__".
    # Try both names so thin wrappers work in both local and Cloud runtimes.
    for module_name in ("dashboard", "__main__"):
        app = sys.modules.get(module_name)
        if app is None:
            continue
        impl = getattr(app, name, None)
        if impl is not None:
            return impl()
    raise RuntimeError(f"{name} is not available in the loaded Streamlit app module")

def render_data_health_page():
    return _call('render_data_health')

def render_data_source_guide_page():
    return _call('render_data_source_guide')

def render_data_manage_page():
    return _call('render_data_manage')
