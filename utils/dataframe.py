from __future__ import annotations

import pandas as pd


def normalize_dataframe(df: pd.DataFrame, text_columns=None) -> pd.DataFrame:
    if text_columns is None:
        text_columns = set()

    out = df.copy()

    for col in out.columns:
        if col in text_columns:
            continue

        if pd.api.types.is_numeric_dtype(out[col]):
            continue

        out[col] = pd.to_numeric(out[col], errors="coerce")

    return out


def clean_text_series(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .replace(
            {
                "nan": None,
                "None": None,
                "": None,
            }
        )
    )


def to_datetime_safe(series: pd.Series) -> pd.Series:
    s = series.copy()

    if s.dtype == object:
        s = (
            s.astype(str)
            .str.replace('="', "", regex=False)
            .str.replace('"', "", regex=False)
        )

    return pd.to_datetime(
        s,
        errors="coerce",
    )


def normalize_month_key(series: pd.Series) -> pd.Series:
    s = series.copy()

    s = s.astype(str).str.strip()

    s = s.replace(
        {
            "nan": None,
            "None": None,
            "": None,
        }
    )

    mask = s.notna() & s.str.fullmatch(r"\d{6}")

    s.loc[mask] = (
        s.loc[mask].str.slice(0, 4)
        + "-"
        + s.loc[mask].str.slice(4, 6)
    )

    return s


def month_start_end(month_key: str):
    start = pd.Timestamp(f"{month_key}-01")
    end = (start + pd.offsets.MonthEnd(1)).normalize()
    return start, end
