from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import INDEX_COMPOSITION_EXAMPLES
from ui.components.state import init_session_state, mark_index_uploaded
from ui.components.status_cards import render_metric_cards
from ui.components.tables import render_preview_table


def render() -> None:
    init_session_state()
    st.title("Index Composition")
    st.caption("Upload the official index composition workbook and keep it independent from the market dataset.")

    uploaded_file = st.file_uploader("Import Index Composition", type=["xlsx"], accept_multiple_files=False, key="index_upload")
    validate_clicked = st.button("Register index workbook", use_container_width=True, disabled=uploaded_file is None)

    if validate_clicked and uploaded_file is not None:
        mark_index_uploaded(uploaded_file.name)
        st.success("Index workbook registered in the UI. Validation will be connected later.")

    render_metric_cards(
        [
            ("Indices", st.session_state.index_summary["indices"], "Validated after backend import."),
            ("Companies", st.session_state.index_summary["companies"], "Validated after backend import."),
            ("Import status", "Ready" if st.session_state.index_imported else "Waiting", "Independent dataset."),
        ]
    )

    st.divider()
    st.subheader("Expected index structures")
    for item in INDEX_COMPOSITION_EXAMPLES:
        st.markdown(f"- {item}")

    st.divider()
    render_preview_table(
        "Index composition dataset preview",
        pd.DataFrame(columns=["Trading Session", "Index", "CODE ISIN", "Instrument", "Weight", "Free Float Factor", "Capping Factor"]),
        "The index composition preview will appear here after the backend validator is connected.",
    )

    with st.expander("Validation report"):
        st.info("This area will display workbook-level validation messages and structural checks for the index composition workbook.")