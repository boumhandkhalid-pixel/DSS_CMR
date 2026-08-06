from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import APP_SUBTITLE, APP_TITLE
from ui.components.sidebar import render_sidebar
from ui.components.state import init_session_state
from ui.components.styles import inject_styles
from ui.views.analysis import render as render_analysis
from ui.views.dashboard import render as render_dashboard
from ui.views.index_composition import render as render_index_composition
from ui.views.market_data import render as render_market_data
from ui.views.recommendations import render as render_recommendations
from ui.views.settings import render as render_settings

PAGE_RENDERERS = {
    "Dashboard": render_dashboard,
    "Market Data": render_market_data,
    "Index Composition": render_index_composition,
    "Analysis": render_analysis,
    "Recommendations": render_recommendations,
    "Settings": render_settings,
}


def main() -> None:
    logo_path = ROOT / "ui" / "assets" / "logo.png"
    st.set_page_config(page_title=APP_TITLE, page_icon=Image.open(logo_path), layout="wide", initial_sidebar_state="expanded")
    init_session_state()
    inject_styles()

    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    selected_page = render_sidebar()
    st.divider()

    renderer = PAGE_RENDERERS.get(selected_page, render_dashboard)
    renderer()


if __name__ == "__main__":
    main()
