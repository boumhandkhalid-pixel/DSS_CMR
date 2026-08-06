from __future__ import annotations

import streamlit as st

from ui.components.charts import render_pipeline_steps
from ui.components.state import init_session_state
from ui.components.status_cards import render_metric_cards, render_stat_list


def render() -> None:
    init_session_state()
    st.title("Dashboard")
    st.caption("Operational overview of the BVC DSS workflow.")

    market_status = "Ready" if st.session_state.market_imported else "Waiting"
    index_status = "Ready" if st.session_state.index_imported else "Waiting"
    readiness = "Ready" if st.session_state.market_imported and st.session_state.index_imported else "Not ready"

    render_metric_cards(
        [
            ("Market workbook", market_status, "Import the official market workbook."),
            ("Index composition", index_status, "Import the index composition workbook."),
            ("Pipeline readiness", readiness, "Both inputs are needed before analysis."),
            ("Recommendations", "Pending", "Generated after the analysis pipeline runs."),
        ]
    )

    st.divider()
    left, right = st.columns(2)
    with left:
        render_stat_list(
            "Latest imports",
            [
                ("Market file", st.session_state.market_file_name or "Not imported"),
                ("Market import time", st.session_state.market_imported_at or "—"),
                ("Index file", st.session_state.index_file_name or "Not imported"),
                ("Index import time", st.session_state.index_imported_at or "—"),
            ],
        )
    with right:
        render_stat_list(
            "Dataset summary",
            [
                ("Accepted market sheets", str(st.session_state.market_summary["accepted_sheets"])),
                ("Ignored market sheets", str(st.session_state.market_summary["ignored_sheets"])),
                ("Market companies", str(st.session_state.market_summary["companies"])),
                ("Trading sessions", str(st.session_state.market_summary["sessions"])),
            ],
        )

    st.divider()
    st.subheader("Pipeline status")
    render_pipeline_steps(
        [
            ("Market parse", "Waiting" if not st.session_state.market_imported else "Imported"),
            ("Normalization", "Waiting"),
            ("Market metrics", "Waiting"),
            ("Dynamic filtering", "Waiting"),
            ("Decision engine", "Waiting"),
        ]
    )