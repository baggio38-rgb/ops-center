"""亿兆智能决策平台 Enterprise UI 主入口。"""

from __future__ import annotations

import streamlit as st

try:
    from version import APP_NAME, APP_VERSION, APP_VERSION_DATE, APP_SUBTITLE
except Exception:
    APP_NAME = "亿兆智能决策平台"
    APP_VERSION = "v4.2.0"
    APP_VERSION_DATE = "2026-07-07"
    APP_SUBTITLE = "Enterprise Intelligence Platform"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app_pages.agent_channel import AGENT_CHANNEL_PAGES
from app_pages.data_admin import DATA_ADMIN_PAGES
from app_pages.finance_results import FINANCE_RESULT_PAGES
from app_pages.home import HOME_PAGES
from app_pages.member_value import MEMBER_VALUE_PAGES
from app_pages.risk_center import RISK_CENTER_PAGES
from app_pages.worldcup import WORLD_CUP_PAGES

try:
    from components.ui import apply_theme, enterprise_header, sidebar_brand, footer
except Exception:
    apply_theme = None
    enterprise_header = None
    sidebar_brand = None
    footer = None


NAV_GROUPS = {
    "🏠 首页": HOME_PAGES,
    "💰 财务中心": FINANCE_RESULT_PAGES,
    "👥 会员中心": MEMBER_VALUE_PAGES,
    "🛡 风控中心": RISK_CENTER_PAGES,
    "⚽ 世界杯专区": WORLD_CUP_PAGES,
    "🧭 代理中心": AGENT_CHANNEL_PAGES,
    "📂 数据中心": DATA_ADMIN_PAGES,
}


def _safe_apply_theme() -> None:
    if apply_theme:
        apply_theme()
    else:
        st.markdown(
            """
            <style>
            .block-container {max-width: 1680px; padding-top: 1.15rem; padding-bottom: 2rem;}
            </style>
            """,
            unsafe_allow_html=True,
        )


def _render_sidebar() -> str:
    with st.sidebar:
        if sidebar_brand:
            sidebar_brand(APP_NAME, APP_SUBTITLE, APP_VERSION)
        else:
            st.markdown(f"### {APP_NAME}")
            st.caption(f"{APP_SUBTITLE} · {APP_VERSION}")

        group = st.radio(
            "功能模块",
            list(NAV_GROUPS.keys()),
            label_visibility="collapsed",
            key="enterprise_nav_group",
        )

        st.markdown('<div class="yz-side-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="yz-side-caption">副功能已移到页面顶部</div>', unsafe_allow_html=True)

        st.markdown('<div class="yz-side-spacer"></div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="yz-side-status">
              <div class="yz-side-status-title">系统状态</div>
              <div><span class="yz-dot yz-dot-ok"></span> BigQuery 正常</div>
              <div><span class="yz-dot yz-dot-ok"></span> ETL 正常</div>
              <div><span class="yz-dot yz-dot-ok"></span> 数据同步</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return group


def main() -> None:
    _safe_apply_theme()
    group = _render_sidebar()

    sub_options = [name for name, _ in NAV_GROUPS[group]]
    default_sub = st.session_state.get(f"enterprise_nav_sub_{group}", sub_options[0])
    if default_sub not in sub_options:
        default_sub = sub_options[0]

    if enterprise_header:
        enterprise_header(
            title=APP_NAME,
            subtitle=APP_SUBTITLE,
            version=APP_VERSION,
            date=APP_VERSION_DATE,
            active_group=group,
            active_page=default_sub,
        )
    else:
        st.title(APP_NAME)
        st.caption(f"{APP_SUBTITLE} · {APP_VERSION} · {APP_VERSION_DATE}")

    sub = st.radio(
        "副功能",
        sub_options,
        index=sub_options.index(default_sub),
        horizontal=True,
        label_visibility="collapsed",
        key=f"enterprise_nav_sub_{group}",
    )
    st.markdown('<div class="yz-topnav-spacer"></div>', unsafe_allow_html=True)

    renderer = {name: fn for name, fn in NAV_GROUPS[group]}[sub]
    renderer()

    if footer:
        footer(APP_NAME, APP_VERSION, APP_VERSION_DATE)
    else:
        st.divider()
        st.caption(f"{APP_NAME} {APP_VERSION}（{APP_VERSION_DATE}）")


if __name__ == "__main__":
    main()
