"""Reusable Streamlit UI helpers.

V7.0 introduces this module as the stable import location for shared layout
and card helpers. The implementations are still delegated to core.legacy so
all existing pages keep the exact same behavior while future cleanup can move
code here safely.
"""

from __future__ import annotations

from core.legacy import (
    add_info_box,
    hero,
    section_header,
    show_metric,
    source_note,
    status_badge,
)

__all__ = [
    "add_info_box",
    "hero",
    "section_header",
    "show_metric",
    "source_note",
    "status_badge",
]
