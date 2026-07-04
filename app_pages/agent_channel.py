"""Agent and channel page group."""

from __future__ import annotations

from ops_core import (
    render_channel_agent,
    render_new_member_analysis,
    render_agent_member_matrix,
    render_agent_market_monthly,
    render_game_venue,
)

AGENT_CHANNEL_PAGES = [
    ("代理团队 & 渠道", render_channel_agent),
    ("新注册分析", render_new_member_analysis),
    ("代理 × 会员 明细", render_agent_member_matrix),
    ("市代月度结算", render_agent_market_monthly),
    ("游戏 & 场馆", render_game_venue),
]
