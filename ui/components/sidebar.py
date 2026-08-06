from __future__ import annotations

from pathlib import Path

import streamlit as st

from config.settings import NAVIGATION_PAGES
from ui.components.state import reset_session_state


def _set_current_page(page: str) -> None:
    st.session_state.current_page = page
    st.rerun()


def render_sidebar() -> str:
    with st.sidebar:
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
        st.image(str(logo_path), use_container_width=True)
        st.title("BVC DSS")
        st.caption("Portfolio Management Decision Support System")
        st.divider()
        st.subheader("Navigation")
        current_page = st.session_state.current_page
        for page in NAVIGATION_PAGES:
            if st.button(
                page,
                key=f"nav_{page}",
                use_container_width=True,
                type="primary" if page == current_page else "secondary",
            ):
                _set_current_page(page)
        st.divider()
        st.subheader("Session")
        st.write(f"Market imported: {'Yes' if st.session_state.market_imported else 'No'}")
        st.write(f"Index imported: {'Yes' if st.session_state.index_imported else 'No'}")
        if st.button("Reset session", use_container_width=True):
            reset_session_state()
            st.rerun()
        return st.session_state.current_page
