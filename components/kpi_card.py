import streamlit as st


def show_kpi_card(label: str, value: str, delta: str = "", icon: str = "📊") -> None:
    st.markdown(
        f"""
        <div class="yz-kpi-card">
            <div class="yz-kpi-label">{icon} {label}</div>
            <div class="yz-kpi-value">{value}</div>
            <div style="margin-top:10px;color:#16A34A;font-weight:800;">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
