from pathlib import Path
import streamlit as st


def load_css(path: str = "assets/css/main.css") -> None:
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
