"""Compatibility launcher for Streamlit multipage routing.

The real navigation lives in dashboard.py. If Streamlit opens this file from
the sidebar, delegate back to the main dashboard to keep the Chinese top-nav UI.
"""

from __future__ import annotations

import dashboard

dashboard.main()
