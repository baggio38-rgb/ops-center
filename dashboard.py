"""亿兆智能决策平台主入口。"""

from __future__ import annotations

import streamlit as st

from app_pages.agent_channel import AGENT_CHANNEL_PAGES
from app_pages.data_admin import DATA_ADMIN_PAGES
from app_pages.finance_results import FINANCE_RESULT_PAGES
from app_pages.home import HOME_PAGES
from app_pages.member_value import MEMBER_VALUE_PAGES
from app_pages.risk_center import RISK_CENTER_PAGES
from app_pages.worldcup import WORLD_CUP_PAGES

try:
    from version import APP_VERSION, APP_VERSION_DATE
except Exception:
    APP_VERSION = "v1.6.0"
    APP_VERSION_DATE = "2026-07-06"


GROUPS = {
    "🏠 首页": HOME_PAGES,
    "🅰️ 财务中心": FINANCE_RESULT_PAGES,
    "👤 会员中心": MEMBER_VALUE_PAGES,
    "🛡 风控中心": RISK_CENTER_PAGES,
    "⚽ 世界杯专区": WORLD_CUP_PAGES,
    "🅲 代理中心": AGENT_CHANNEL_PAGES,
    "🗂 数据管理": DATA_ADMIN_PAGES,
}


def _page_style() -> None:
    st.set_page_config(
        page_title="亿兆智能决策平台",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        div[data-testid="stHorizontalBlock"] {gap: 0.75rem;}
        /* v1.3.1 hotfix: 顶部导航文字被切掉 */
        div[data-testid="stRadio"] [role="radiogroup"] {
            display: flex;
            align-items: center;
            gap: 14px;
            flex-wrap: wrap;
            min-height: 48px;
            overflow: visible;
            padding: 4px 0 6px 0;
        }
        div[data-testid="stRadio"] label {
            min-height: 36px !important;
            height: auto !important;
            display: flex !important;
            align-items: center !important;
            overflow: visible !important;
            padding: 5px 6px !important;
            white-space: nowrap !important;
        }
        div[data-testid="stRadio"] label p {
            line-height: 1.35 !important;
            margin: 0 !important;
            overflow: visible !important;
            white-space: nowrap !important;
        }
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
    st.caption(f"亿兆智能决策平台 {APP_VERSION}（{APP_VERSION_DATE}）· Dashboard、Member360、风控中心、世界杯作战中心")


if __name__ == "__main__":
    main()
