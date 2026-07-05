"""世界杯专区页面组。"""

from __future__ import annotations

from features.worldcup_center import (
    render_worldcup_overview,
    render_match_monitor,
    render_worldcup_database,
    render_worldcup_players,
    render_worldcup_rules,
)


WORLD_CUP_PAGES = [
    ("世界杯总览", render_worldcup_overview),
    ("比赛监控", render_match_monitor),
    ("世界杯资料库", render_worldcup_database),
    ("玩家分析", render_worldcup_players),
    ("识别规则", render_worldcup_rules),
]
