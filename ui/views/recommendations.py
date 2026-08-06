from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components.state import init_session_state
from ui.components.status_cards import render_metric_cards
from ui.components.tables import render_preview_table


def render() -> None:
    init_session_state()
    st.title("Recommendations")
    st.caption("Review final BUY / HOLD / SELL outputs and export them once the backend is connected.")

    render_metric_cards(
        [
            ("Signal", "Pending", "Populated by the decision engine."),
            ("Confidence", "—", "Confidence score appears after analysis."),
            ("Filtered securities", "—", "Output of the dynamic filter stage."),
        ]
    )

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Recommendation summary")
        st.info("The recommendation table will be populated after the validated backend modules are integrated.")
    with right:
        st.subheader("Evidence panel")
        st.info("Display the indicators, filtering decisions, and rule outcomes that justify the final recommendation.")

    st.divider()
    render_preview_table(
        "Recommendations table",
        pd.DataFrame(columns=["CODE ISIN", "Company", "Signal", "Confidence", "Reason"]),
        "No recommendations are available yet.",
    )

    left, right = st.columns(2)
    with left:
        st.download_button("Export CSV", data="CODE_ISIN,Company,Signal,Confidence\n", file_name="recommendations.csv", mime="text/csv", use_container_width=True)
    with right:
        st.download_button("Export JSON", data="{}", file_name="recommendations.json", mime="application/json", use_container_width=True)