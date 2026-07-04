"""Data loading facade for Ops Center.

This module is intentionally independent from core.legacy to avoid circular
imports. Feature modules and future services should import BigQuery helpers from
here instead of importing them from core.legacy.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import BQ_PREFIX
from constants import TEXT_COLUMNS
from services.bigquery_client import get_bq_client
from utils.dataframe import normalize_dataframe, to_datetime_safe


@st.cache_data(ttl=300)
def query_bq(sql: str) -> pd.DataFrame:
    """Run a BigQuery SQL query and normalize numeric/text columns."""
    client = get_bq_client()
    df = client.query(sql).to_dataframe()
    return normalize_dataframe(df, TEXT_COLUMNS)


@st.cache_data(ttl=300)
def load_table(table_name: str) -> pd.DataFrame:
    """Read a BigQuery table. Missing or failed tables return an empty DataFrame."""
    sql = f"SELECT * FROM `{BQ_PREFIX}.{table_name}`"
    try:
        return query_bq(sql)
    except Exception:
        return pd.DataFrame()


def latest_imported_at(*dfs: pd.DataFrame) -> str:
    """Return latest _imported_at timestamp across DataFrames, or blank if absent."""
    vals = []
    for df in dfs:
        if df is not None and not df.empty and "_imported_at" in df.columns:
            ts = to_datetime_safe(df["_imported_at"])
            if ts.notna().any():
                vals.append(ts.max())
    if not vals:
        return ""
    return max(vals).strftime("%Y-%m-%d %H:%M")


__all__ = ["latest_imported_at", "load_table", "query_bq"]
