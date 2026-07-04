"""Data loading facade.

V7.0 adds this stable import path for BigQuery/table loading helpers. The
implementation remains delegated to core.legacy during the transition to avoid
behavior changes.
"""

from __future__ import annotations

from core.legacy import latest_imported_at, load_table, query_bq

__all__ = ["latest_imported_at", "load_table", "query_bq"]
