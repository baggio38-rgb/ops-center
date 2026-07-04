"""Member value page group."""

from __future__ import annotations

from features.member_value import (
    render_member_value,
    render_bet_analysis,
    render_cs_analysis,
    render_winback,
)
from features.realtime_health import render_realtime


MEMBER_VALUE_PAGES = [
    ("会员结构 & ARPU", render_member_value),
    ("投注分析", render_bet_analysis),
    ("客服分析", render_cs_analysis),
    ("电访召回", render_winback),
    ("实时波动 & DAU", render_realtime),
]
