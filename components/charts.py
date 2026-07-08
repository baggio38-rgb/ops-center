"""共用 Plotly 图表组件。"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PLOTLY_TEMPLATE = "plotly_dark"

ZH_LABELS = {
    "game_id": "赛事编号",
    "tournament": "赛事",
    "stage": "赛事阶段",
    "match_name": "比赛名称",
    "home_team": "主队",
    "away_team": "客队",
    "kickoff_time": "开赛时间",
    "match_date": "比赛日期",
    "play_type": "玩法",
    "member_key": "会员账号",
    "vip_level": "VIP等级",
    "agent_name": "代理",
    "risk_level": "风险等级",
    "risk_score": "风险分数",
    "bet_count": "投注笔数",
    "member_count": "投注人数",
    "match_count": "比赛数",
    "game_count": "参与比赛数",
    "play_type_count": "玩法数",
    "provider_count": "场馆数",
    "bet_amount": "下注金额",
    "valid_turnover": "有效投注",
    "member_profit_loss": "会员盈亏",
    "platform_profit_loss": "平台盈亏",
    "member_rtp": "会员RTP",
    "platform_roi": "平台ROI",
    "updated_at": "更新时间",
}


def _labels(*cols: str) -> dict[str, str]:
    return {c: ZH_LABELS.get(c, c) for c in cols if c}



def line_chart(df: pd.DataFrame, x: str, y: str, title: str = "", height: int = 360) -> None:
    if df is None or df.empty or x not in df.columns or y not in df.columns:
        st.caption("暂无图表资料")
        return
    fig = px.line(df, x=x, y=y, markers=True, title=title, template=PLOTLY_TEMPLATE, labels=_labels(x, y))
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=42 if title else 15, b=10))
    st.plotly_chart(fig, use_container_width=True)


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", height: int = 380, orientation: str = "v") -> None:
    if df is None or df.empty or x not in df.columns or y not in df.columns:
        st.caption("暂无图表资料")
        return
    if orientation == "h":
        fig = px.bar(df, x=y, y=x, orientation="h", title=title, template=PLOTLY_TEMPLATE, labels=_labels(x, y))
        fig.update_layout(yaxis=dict(autorange="reversed"))
    else:
        fig = px.bar(df, x=x, y=y, title=title, template=PLOTLY_TEMPLATE, labels=_labels(x, y))
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=42 if title else 15, b=10))
    st.plotly_chart(fig, use_container_width=True)


def dual_axis_bar_line(df: pd.DataFrame, x: str, bar_y: str, line_y: str, title: str = "", height: int = 380) -> None:
    if df is None or df.empty or x not in df.columns or bar_y not in df.columns or line_y not in df.columns:
        st.caption("暂无图表资料")
        return
    fig = go.Figure()
    fig.add_bar(x=df[x], y=df[bar_y], name=ZH_LABELS.get(bar_y, bar_y))
    fig.add_scatter(x=df[x], y=df[line_y], name=ZH_LABELS.get(line_y, line_y), mode="lines+markers", yaxis="y2")
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=42 if title else 15, b=10),
        yaxis=dict(title=ZH_LABELS.get(bar_y, bar_y)),
        yaxis2=dict(title=ZH_LABELS.get(line_y, line_y), overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def donut_chart(df: pd.DataFrame, names: str, values: str, title: str = "", height: int = 360) -> None:
    if df is None or df.empty or names not in df.columns or values not in df.columns:
        st.caption("暂无图表资料")
        return
    fig = px.pie(df, names=names, values=values, hole=.55, title=title, template=PLOTLY_TEMPLATE, labels=_labels(names, values))
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=42 if title else 15, b=10))
    st.plotly_chart(fig, use_container_width=True)
