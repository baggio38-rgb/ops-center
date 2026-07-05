"""博彩智能决策平台主入口。"""

from __future__ import annotations

import streamlit as st

from app_pages.agent_channel import AGENT_CHANNEL_PAGES
from app_pages.data_admin import DATA_ADMIN_PAGES
from app_pages.finance_results import FINANCE_RESULT_PAGES
from app_pages.home import HOME_PAGES
from app_pages.member_value import MEMBER_VALUE_PAGES
from app_pages.risk_center import RISK_CENTER_PAGES

try:
    from version import APP_VERSION, APP_VERSION_DATE
except Exception:
    APP_VERSION = "v1.3.0"
    APP_VERSION_DATE = "2026-07-05"


GROUPS = {
    "🏠 首页": HOME_PAGES,
    "🅰️ 财务中心": FINANCE_RESULT_PAGES,
    "👤 会员中心": MEMBER_VALUE_PAGES,
    "🛡 风控中心": RISK_CENTER_PAGES,
    "🅲 代理中心": AGENT_CHANNEL_PAGES,
    "🗂 数据管理": DATA_ADMIN_PAGES,
}


def _page_style() -> None:
    st.set_page_config(
        page_title="博彩智能决策平台",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        div[data-testid="stHorizontalBlock"] {gap: 0.75rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """渲染中文顶部导航并调用页面。"""
    _page_style()

    group = st.radio(
        "大类",
        list(GROUPS.keys()),
        horizontal=True,
        label_visibility="collapsed",
        key="nav_group",
    )

    sub_options = [name for name, _ in GROUPS[group]]
    sub_renderers = {name: fn for name, fn in GROUPS[group]}

    st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)

    sub = st.radio(
        "细项",
        sub_options,
        horizontal=True,
        label_visibility="collapsed",
        key=f"nav_sub_{group}",
    )

    sub_renderers[sub]()
    st.divider()
    st.caption(f"博彩智能决策平台 {APP_VERSION}（{APP_VERSION_DATE}）· 首页、总裁驾驶舱、会员中心、风控中心")


if __name__ == "__main__":
    main()
