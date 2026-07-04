"""Lightweight import smoke test for Ops Center.

This test intentionally avoids BigQuery calls. It only checks that the app
module graph can import and that the navigation registry is populated.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


MODULES = [
    "dashboard",
    "app_pages.finance_results",
    "app_pages.member_value",
    "app_pages.agent_channel",
    "app_pages.data_admin",
    "features.finance_results",
    "features.member_value",
    "features.agent_channel",
    "features.upload_admin",
    "features.realtime_health",
    "components",
    "services",
    "utils.formatter",
    "utils.dataframe",
]


def main() -> None:
    for name in MODULES:
        importlib.import_module(name)

    import dashboard

    assert dashboard.GROUPS, "dashboard.GROUPS is empty"
    for group_name, pages in dashboard.GROUPS.items():
        assert pages, f"{group_name} has no registered pages"
        for page_name, render_fn in pages:
            assert callable(render_fn), f"{group_name}/{page_name} renderer is not callable"

    print("Smoke test passed: imports and navigation registry are healthy.")


if __name__ == "__main__":
    main()
