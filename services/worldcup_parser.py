"""World Cup parser utilities for YiZhao Intelligent Decision Platform.

This module is intentionally pure-Python so it can be unit-tested without
Streamlit or BigQuery. The Streamlit page still uses a BigQuery CTE parser for
speed, but the same rules live here as the source of truth for future ETL.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Optional

WORLD_CUP_KEYWORD = "世界杯2026(在加拿大、墨西哥&美国)"

@dataclass(frozen=True)
class WorldCupParsedBet:
    is_worldcup: bool
    is_panda: bool
    event_type: str
    stage: str
    match_name: str
    home_team: Optional[str]
    away_team: Optional[str]
    market_name: str
    selection_name: Optional[str]
    kickoff_text: Optional[str]


def normalize_detail(detail: str | None) -> str:
    text = "" if detail is None else str(detail)
    text = text.replace("_x000D_", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def parse_stage_by_kickoff(kickoff_text: str | None, event_type: str) -> str:
    if event_type == "阶段盘口":
        return "阶段盘口"
    if event_type == "串关/多场":
        return "串关/多场"
    if not kickoff_text:
        return "未识别阶段"
    try:
        d = datetime.strptime(kickoff_text[:10], "%Y-%m-%d").date()
    except Exception:
        return "未识别阶段"
    if d <= datetime(2026, 6, 27).date():
        return "小组赛"
    if datetime(2026, 6, 28).date() <= d <= datetime(2026, 7, 3).date():
        return "32强"
    if datetime(2026, 7, 4).date() <= d <= datetime(2026, 7, 7).date():
        return "16强"
    if datetime(2026, 7, 9).date() <= d <= datetime(2026, 7, 11).date():
        return "8强"
    if datetime(2026, 7, 14).date() <= d <= datetime(2026, 7, 15).date():
        return "半决赛"
    if d == datetime(2026, 7, 18).date():
        return "季军赛"
    if d == datetime(2026, 7, 19).date():
        return "冠军赛"
    return "未识别阶段"


def parse_worldcup_bet(detail: str | None, game_name: str | None = "") -> WorldCupParsedBet:
    clean = normalize_detail(detail)
    lower = clean.lower()
    is_worldcup = WORLD_CUP_KEYWORD in clean
    is_panda = "panda" in lower
    is_parlay = bool(re.search(r"串关|parlay", f"{game_name or ''} {clean}", re.I))

    kickoff_match = re.search(r"足球\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)", clean)
    kickoff_text = kickoff_match.group(1) if kickoff_match else None

    match = re.search(r"(?:^|\n)([^\n@]+?\s+v\s+[^\n@]+?)(?:\n|$)", clean)
    parsed_match = re.sub(r"\s+vs\s+", " v ", match.group(1).strip(), flags=re.I) if match else None

    market_match = re.search(r"玩法：([^\n]+)", clean)
    market_name = market_match.group(1).strip() if market_match else "未识别玩法"

    selection_match = re.search(r"(?:^|\n)([^@\n]+)@\d+(?:\.\d+)?", clean)
    selection_name = selection_match.group(1).strip() if selection_match else None

    if is_parlay:
        event_type = "串关/多场"
        match_name = "串关/多场"
        home = away = None
    elif parsed_match:
        event_type = "单场赛事"
        match_name = parsed_match
        parts = re.split(r"\s+v\s+", parsed_match, maxsplit=1)
        home = parts[0].strip() if parts else None
        away = parts[1].strip() if len(parts) > 1 else None
    else:
        event_type = "阶段盘口"
        match_name = f"阶段盘口：{market_name or '冠军/阶段'}"
        home = away = None

    stage = parse_stage_by_kickoff(kickoff_text, event_type)
    return WorldCupParsedBet(
        is_worldcup=is_worldcup,
        is_panda=is_panda,
        event_type=event_type,
        stage=stage,
        match_name=match_name,
        home_team=home,
        away_team=away,
        market_name=market_name,
        selection_name=selection_name,
        kickoff_text=kickoff_text,
    )
