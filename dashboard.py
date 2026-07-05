"""Ops Center main entry point.

Small navigation shell. Logical page groups live under app_pages/.
"""

from __future__ import annotations

import streamlit as st

from app_pages.agent_channel import AGENT_CHANNEL_PAGES
from app_pages.data_admin import DATA_ADMIN_PAGES
from app_pages.finance_results import FINANCE_RESULT_PAGES
from app_pages.member_value import MEMBER_VALUE_PAGES
from app_pages.risk_center import RISK_CENTER_PAGES
from version import APP_VERSION, APP_VERSION_DATE


GROUPS = {
    "🅰️ 财务结果": FINANCE_RESULT_PAGES,
    "🅱️ 会员价值": MEMBER_VALUE_PAGES,
    "🛡 风控中心": RISK_CENTER_PAGES,
    "🅲 代理 / 渠道": AGENT_CHANNEL_PAGES,
    "🗂 数据上传": DATA_ADMIN_PAGES,
}


def main():
    """Render the top-level Chinese navigation and call the selected page."""
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
    st.caption(f"运营数据面板 {APP_VERSION}（{APP_VERSION_DATE}）· 更新内容见仓库 CHANGELOG.md")


if __name__ == "__main__":
    main()
