import streamlit as st
from config.settings import APP_NAME, APP_NAME_EN, VERSION, BUILD


def show_hero_banner(title: str = "运营总览", subtitle: str = "管理层首页，快速掌握今日投注、盈亏、会员活跃与重点风险。") -> None:
    st.markdown(
        f"""
        <div class="yz-hero">
            <div class="yz-hero-title">{APP_NAME}</div>
            <div class="yz-hero-subtitle">{APP_NAME_EN} · v{VERSION} · Build {BUILD}</div>
            <hr style="border:0;border-top:1px solid rgba(255,255,255,.18);margin:18px 0;">
            <div style="font-size:26px;font-weight:900;">{title}</div>
            <div style="margin-top:8px;color:#D7EAFE;font-weight:700;">{subtitle}</div>
            <div style="margin-top:18px;display:flex;gap:12px;flex-wrap:wrap;">
                <span><span class="yz-status-dot"></span>BigQuery 正常</span>
                <span><span class="yz-status-dot"></span>ETL 正常</span>
                <span><span class="yz-status-dot"></span>Aggregate 正常</span>
                <span><span class="yz-status-dot"></span>AI 在线</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
