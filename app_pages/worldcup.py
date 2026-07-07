"""世界杯专区页面组。"""

from __future__ import annotations

from features.worldcup_enterprise import (
    render_worldcup_v2_overview,
    render_worldcup_v2_matches,
    render_worldcup_v2_playtypes,
    render_worldcup_v2_members,
    render_worldcup_v2_risk,
)


WORLD_CUP_PAGES = [
    ("运营总览 V2", render_worldcup_v2_overview),
    ("单场比赛", render_worldcup_v2_matches),
    ("玩法分析", render_worldcup_v2_playtypes),
    ("会员分析", render_worldcup_v2_members),
    ("风险会员", render_worldcup_v2_risk),
]
