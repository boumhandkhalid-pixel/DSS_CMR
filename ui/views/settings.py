from __future__ import annotations

import streamlit as st

from config.settings import BUSINESS_RULE_DEFAULTS, DYNAMIC_FILTER_DEFAULTS, TECHNICAL_INDICATORS_DEFAULT
from ui.components.state import init_session_state


def render() -> None:
    init_session_state()
    st.title("Settings")
    st.caption("Configure future indicators, filters, and rules without changing the UI structure.")

    with st.form("settings_form"):
        st.subheader("Technical indicators")
        indicators = st.multiselect("Enabled indicators", TECHNICAL_INDICATORS_DEFAULT, default=st.session_state.settings["technical_indicators"])

        st.subheader("Dynamic filters")
        min_liquidity = st.number_input("Minimum liquidity", min_value=0.0, value=float(DYNAMIC_FILTER_DEFAULTS["min_liquidity"]), step=0.1)
        min_volume = st.number_input("Minimum average volume", min_value=0.0, value=float(DYNAMIC_FILTER_DEFAULTS["min_average_volume"]), step=0.1)
        min_free_float = st.number_input("Minimum free float", min_value=0.0, value=float(DYNAMIC_FILTER_DEFAULTS["min_free_float"]), step=0.01)

        st.subheader("Business rules")
        rsi_threshold = st.slider("RSI buy threshold", 0, 100, int(BUSINESS_RULE_DEFAULTS["rsi_buy_threshold"]))
        rvol_threshold = st.number_input("RVOL buy threshold", min_value=0.0, value=float(BUSINESS_RULE_DEFAULTS["rvol_buy_threshold"]), step=0.1)

        save_clicked = st.form_submit_button("Save UI settings")

    if save_clicked:
        st.session_state.settings = {
            "technical_indicators": indicators,
            "dynamic_filters": {
                "min_liquidity": min_liquidity,
                "min_average_volume": min_volume,
                "min_free_float": min_free_float,
            },
            "business_rules": {
                "rsi_buy_threshold": rsi_threshold,
                "rvol_buy_threshold": rvol_threshold,
            },
        }
        st.success("Settings saved for the current session. Backend integration can read them later.")