from __future__ import annotations

from typing import Optional

import pandas as pd


def fmt_num(v, suffix: str = "") -> str:
    if v is None or pd.isna(v):
        return "N/A"
    v = float(v)
    if abs(v) >= 1e8:
        return f"{v / 1e8:,.2f}亿{suffix}"
    if abs(v) >= 1e4:
        return f"{v / 1e4:,.2f}万{suffix}"
    if float(v).is_integer():
        return f"{int(v):,}{suffix}"
    return f"{v:,.2f}{suffix}"


def fmt_pct(v) -> str:
    if v is None or pd.isna(v):
        return "N/A"
    v = float(v)
    return f"{v * 100:,.2f}%" if abs(v) <= 1 else f"{v:,.2f}%"


def safe_sum(df: pd.DataFrame, col: str) -> float:
    return float(df[col].sum()) if col in df.columns else 0.0


def safe_mean(df: pd.DataFrame, col: str) -> float:
    return float(df[col].mean()) if col in df.columns and len(df) else 0.0


def safe_nunique(df: pd.DataFrame, col: str) -> int:
    return int(df[col].nunique()) if col in df.columns else 0


def member_count(df: pd.DataFrame, account_col: str = "会员账号", agent_col: str = "代理") -> int:
    if account_col not in df.columns:
        return 0
    if agent_col in df.columns:
        return int(df.drop_duplicates(subset=[account_col, agent_col]).shape[0])
    return int(df[account_col].nunique())


def tone_by_sign(v, invert: bool = False) -> Optional[str]:
    if v is None or pd.isna(v):
        return None
    v = float(v)
    if v == 0:
        return None
    positive = v > 0
    if invert:
        positive = not positive
    return "good" if positive else "bad"
