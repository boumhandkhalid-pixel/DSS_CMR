from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import streamlit as st


def render_preview_table(title: str, dataframe: pd.DataFrame | None, empty_message: str) -> None:
    st.subheader(title)
    if dataframe is None or dataframe.empty:
        st.info(empty_message)
        return
    st.dataframe(dataframe, use_container_width=True, hide_index=True)


def render_bullet_table(title: str, rows: Sequence[tuple[str, str]]) -> None:
    st.subheader(title)
    if not rows:
        st.info("No rows available yet.")
        return
    for left, right in rows:
        st.markdown(f"- **{left}**: {right}")
