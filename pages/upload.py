"""Data upload page entry point.

Thin wrapper that delegates to the upload implementation in dashboard.py.
Works in both local Streamlit and Streamlit Cloud runtimes.
"""

from __future__ import annotations

import sys


def render_data_upload():
    for module_name in ("dashboard", "__main__"):
        app = sys.modules.get(module_name)
        if app is None:
            continue
        impl = getattr(app, "_render_data_upload_impl", None)
        if impl is not None:
            return impl()
    raise RuntimeError("_render_data_upload_impl is not available in the loaded Streamlit app module")
