from __future__ import annotations

import streamlit as st

from ui.components.charts import render_pipeline_steps
from ui.components.state import init_session_state, mark_analysis_requested, mark_analysis_completed


def render() -> None:
    init_session_state()
    st.title("Analysis")
    st.caption("Run the analysis pipeline once both datasets are available.")

    ready = st.session_state.market_imported and st.session_state.index_imported
    if not ready:
        st.warning("Import both the market workbook and the index composition workbook before running analysis.")

    render_pipeline_steps(
        [
            ("Market metrics", "Ready" if st.session_state.market_imported else "Pending"),
            ("Dynamic filtering", "Ready" if st.session_state.index_imported else "Pending"),
            ("Technical indicators", "Pending"),
            ("Business rules", "Pending"),
            ("Decision engine", "Pending"),
        ]
    )

    run_clicked = st.button("Run Portfolio Analysis", use_container_width=True, disabled=not ready)
    if run_clicked:
        mark_analysis_requested()
        st.info("The backend pipeline will be connected here later. This UI already reserves the workflow slot.")
        mark_analysis_completed()