"""共用 Plotly 图表组件。"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PLOTLY_TEMPLATE = "plotly_dark"


def line_chart(df: pd.DataFrame, x: str, y: str, title: str = "", height: int = 360) -> None:
    if df is None or df.empty or x not in df.columns or y not in df.columns:
        st.caption("暂无图表资料")
        return
    fig = px.line(df, x=x, y=y, markers=True, title=title, template=PLOTLY_TEMPLATE)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=42 if title else 15, b=10))
    st.plotly_chart(fig, use_container_width=True)


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", height: int = 380, orientation: str = "v") -> None:
    if df is None or df.empty or x not in df.columns or y not in df.columns:
        st.caption("暂无图表资料")
        return
    if orientation == "h":
        fig = px.bar(df, x=y, y=x, orientation="h", title=title, template=PLOTLY_TEMPLATE)
        fig.update_layout(yaxis=dict(autorange="reversed"))
    else:
        fig = px.bar(df, x=x, y=y, title=title, template=PLOTLY_TEMPLATE)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=42 if title else 15, b=10))
    st.plotly_chart(fig, use_container_width=True)


def dual_axis_bar_line(df: pd.DataFrame, x: str, bar_y: str, line_y: str, title: str = "", height: int = 380) -> None:
    if df is None or df.empty or x not in df.columns or bar_y not in df.columns or line_y not in df.columns:
        st.caption("暂无图表资料")
        return
    fig = go.Figure()
    fig.add_bar(x=df[x], y=df[bar_y], name=bar_y)
    fig.add_scatter(x=df[x], y=df[line_y], name=line_y, mode="lines+markers", yaxis="y2")
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=42 if title else 15, b=10),
        yaxis=dict(title=bar_y),
        yaxis2=dict(title=line_y, overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def donut_chart(df: pd.DataFrame, names: str, values: str, title: str = "", height: int = 360) -> None:
    if df is None or df.empty or names not in df.columns or values not in df.columns:
        st.caption("暂无图表资料")
        return
    fig = px.pie(df, names=names, values=values, hole=.55, title=title, template=PLOTLY_TEMPLATE)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=42 if title else 15, b=10))
    st.plotly_chart(fig, use_container_width=True)
