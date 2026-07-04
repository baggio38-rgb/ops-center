"""Pytest-compatible smoke tests for imports and navigation wiring."""

from __future__ import annotations

import importlib


def test_core_modules_importable():
    modules = [
        "dashboard",
        "components",
        "services",
        "features.finance_results",
        "features.member_value",
        "features.agent_channel",
        "features.upload_admin",
        "features.realtime_health",
    ]
    for module in modules:
        importlib.import_module(module)


def test_navigation_registry_has_callable_pages():
    import dashboard

    assert dashboard.GROUPS
    for pages in dashboard.GROUPS.values():
        assert pages
        for _, render_fn in pages:
            assert callable(render_fn)
