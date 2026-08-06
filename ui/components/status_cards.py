from __future__ import annotations

from collections.abc import Sequence

import streamlit as st


def render_metric_cards(items: Sequence[tuple[str, str | int | float, str | None]]) -> None:
    if not items:
        return
    columns = st.columns(len(items))
    for column, (label, value, help_text) in zip(columns, items, strict=False):
        with column:
            st.metric(label, value, help=help_text)


def render_stat_list(title: str, items: Sequence[tuple[str, str]]) -> None:
    st.subheader(title)
    for label, value in items:
        st.markdown(f"**{label}**: {value}")
