"""Data upload page entry point.

This module is intentionally thin in this step: it routes the upload page
from dashboard.py so the navigation can start using the pages/ package
without changing upload behavior.
"""

from __future__ import annotations

import sys


def render_data_upload():
    app = sys.modules.get("__main__")
    impl = getattr(app, "_render_data_upload_impl", None)
    if impl is None:
        raise RuntimeError("_render_data_upload_impl is not available in the main Streamlit module")
    return impl()
