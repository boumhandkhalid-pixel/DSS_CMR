from __future__ import annotations

from collections.abc import Sequence

import streamlit as st


def render_pipeline_steps(steps: Sequence[tuple[str, str]]) -> None:
    if not steps:
        return
    columns = st.columns(len(steps))
    for column, (label, status) in zip(columns, steps, strict=False):
        with column:
            st.markdown(f"**{label}**")
            st.write(status)
