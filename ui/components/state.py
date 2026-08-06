from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import streamlit as st

STATE_DEFAULTS: dict[str, Any] = {
    "current_page": "Dashboard",
    "market_file_name": None,
    "market_imported": False,
    "market_imported_at": None,
    "market_summary": {
        "accepted_sheets": 0,
        "ignored_sheets": 0,
        "companies": 0,
        "sessions": 0,
    },
    "index_file_name": None,
    "index_imported": False,
    "index_imported_at": None,
    "index_summary": {
        "indices": 0,
        "companies": 0,
    },
    "analysis_requested": False,
    "analysis_completed": False,
    "recommendations_ready": False,
    "settings": {
        "technical_indicators": [
            "RSI14",
            "SMA20",
            "SMA50",
            "EMA20",
            "MACD",
            "MACD Signal",
            "MACD Histogram",
            "RVOL",
            "VWAP",
            "Historical Volatility",
        ],
        "dynamic_filters": {},
        "business_rules": {},
    },
}


def init_session_state() -> None:
    for key, value in STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, dict) else value


def reset_session_state() -> None:
    for key in list(STATE_DEFAULTS.keys()):
        st.session_state.pop(key, None)
    init_session_state()


def _utc_now_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def mark_market_uploaded(file_name: str) -> None:
    st.session_state.market_file_name = file_name
    st.session_state.market_imported = True
    st.session_state.market_imported_at = _utc_now_label()


def mark_index_uploaded(file_name: str) -> None:
    st.session_state.index_file_name = file_name
    st.session_state.index_imported = True
    st.session_state.index_imported_at = _utc_now_label()


def set_market_summary(*, accepted_sheets: int | None = None, ignored_sheets: int | None = None, companies: int | None = None, sessions: int | None = None) -> None:
    summary = dict(st.session_state.market_summary)
    if accepted_sheets is not None:
        summary["accepted_sheets"] = accepted_sheets
    if ignored_sheets is not None:
        summary["ignored_sheets"] = ignored_sheets
    if companies is not None:
        summary["companies"] = companies
    if sessions is not None:
        summary["sessions"] = sessions
    st.session_state.market_summary = summary


def set_index_summary(*, indices: int | None = None, companies: int | None = None) -> None:
    summary = dict(st.session_state.index_summary)
    if indices is not None:
        summary["indices"] = indices
    if companies is not None:
        summary["companies"] = companies
    st.session_state.index_summary = summary


def mark_analysis_requested() -> None:
    st.session_state.analysis_requested = True
    st.session_state.analysis_completed = False


def mark_analysis_completed() -> None:
    st.session_state.analysis_completed = True
    st.session_state.recommendations_ready = True
