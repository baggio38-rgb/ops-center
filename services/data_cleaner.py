"""Upload data cleaning helpers for 亿兆智能决策平台.

Purpose:
- Normalize mixed Excel serial dates and normal datetime strings before writing to BigQuery.
- Current known issue: raw_bet_detail.`下注时间` may contain values like
  "46209.21663194444" instead of "2026-07-06 05:11:57".
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

EXCEL_ORIGIN = "1899-12-30"


def normalize_bet_time(value: Any) -> str | None:
    """Return YYYY-MM-DD HH:MM:SS or None.

    Handles:
    - pandas Timestamp / Python datetime-like values
    - normal strings: 2026-07-04 23:48:10
    - Excel serial numbers: 46209.21663194444
    - dirty strings with tabs, CRLF markers, commas, wrapping quotes
    """
    if value is None or pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    s = str(value).strip()
    s = (
        s.replace("\t", "")
         .replace("_x000D_", " ")
         .replace("\r", " ")
         .replace("\n", " ")
         .replace('="', "")
         .replace('"', "")
         .strip()
    )
    if not s or s.lower() in {"nan", "none", "null"}:
        return None

    # Excel serial date, e.g. 46209.21663194444
    try:
        num = float(s.replace(",", ""))
        if math.isfinite(num) and 30000 <= num <= 60000:
            dt = pd.to_datetime(num, unit="D", origin=EXCEL_ORIGIN, errors="coerce")
            if not pd.isna(dt):
                return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    # Normal datetime string
    dt = pd.to_datetime(s, errors="coerce")
    if pd.isna(dt):
        return s
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def clean_upload_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean upload dataframe before BigQuery load.

    Safe to call for every report. It only modifies known time columns when present.
    """
    if df is None or df.empty:
        return df

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Betting detail key column
    if "下注时间" in df.columns:
        df["下注时间"] = df["下注时间"].map(normalize_bet_time)

    # Optional: clean common related time columns but keep them as strings.
    for col in ("结算时间", "开赛时间"):
        if col in df.columns:
            df[col] = df[col].map(normalize_bet_time)

    return df
