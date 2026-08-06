from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import MARKET_WORKBOOK_EXCLUDED, MARKET_WORKBOOK_EXAMPLES
from ui.components.state import init_session_state, mark_market_uploaded
from ui.components.status_cards import render_metric_cards
from ui.components.tables import render_preview_table


def render() -> None:
    init_session_state()
    st.title("Market Data")
    st.caption("Upload the official market workbook, classify the sheets, and prepare the normalized market dataset.")

    uploaded_file = st.file_uploader("Import Market Data", type=["xlsx"], accept_multiple_files=False)
    import_clicked = st.button("Register market workbook", use_container_width=True, disabled=uploaded_file is None)

    if import_clicked and uploaded_file is not None:
        mark_market_uploaded(uploaded_file.name)
        st.success("Market workbook registered in the UI. Backend parsing will be connected later.")

    render_metric_cards(
        [
            ("Accepted sheets", st.session_state.market_summary["accepted_sheets"], "Family A sheets only."),
            ("Ignored sheets", st.session_state.market_summary["ignored_sheets"], "Family B sheets such as Data."),
            ("Companies", st.session_state.market_summary["companies"], "Populated after backend validation."),
            ("Trading sessions", st.session_state.market_summary["sessions"], "Populated after normalization."),
        ]
    )

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Expected market sheets")
        for sheet_name in MARKET_WORKBOOK_EXAMPLES:
            st.markdown(f"- {sheet_name}")
    with right:
        st.subheader("Detected and ignored")
        for sheet_name in MARKET_WORKBOOK_EXCLUDED:
            st.markdown(f"- {sheet_name}")

    st.divider()
    render_preview_table(
        "Unified market dataset preview",
        pd.DataFrame(columns=["Date", "CODE ISIN", "Company", "Bid", "Ask", "Close", "Volume MC", "Quantity MC"]),
        "The unified market dataset will appear here after the backend parser and normalizer are connected.",
    )

    with st.expander("Validation report"):
        st.info("This area will show sheet classification, accepted Family A sheets, ignored Family B sheets, and any structural warnings.")