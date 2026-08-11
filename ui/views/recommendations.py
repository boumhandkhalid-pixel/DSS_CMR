from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.translations import TITLES, MESSAGES, DECISIONS, METRICS, SECTIONS, BUTTONS, WARNINGS, FILTERS, HELP_TEXT
from ui.components.state import init_session_state
from ui.components.status_cards import render_metric_cards
from ui.components.tables import render_preview_table
from src.pipeline import DSS_Pipeline


def render() -> None:
    """Vue des recommandations - Décisions ACHAT/CONSERVER/VENDRE."""
    init_session_state()
    st.title(TITLES['recommendations_title'])
    st.caption(TITLES['recommendations_caption'])

    # Check if pipeline has been run
    if 'pipeline' not in st.session_state or 'decisions_summary' not in st.session_state:
        st.warning(MESSAGES['no_decisions'])
        
        # Show pipeline requirements
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(SECTIONS['prerequisites'])
            st.markdown("""
            1. **Données Marché** téléchargées et validées
            2. **Composition Indice** téléchargée
            3. **Pipeline** exécuté
            """)
        with col2:
            st.subheader(SECTIONS['next_steps'])
            st.markdown("""
            1. Allez à la page **Données Marché**
            2. Téléchargez le fichier Excel
            3. Allez à la page **Composition Indice**
            4. Téléchargez le fichier de composition
            5. Revenez ici pour lancer le pipeline
            """)
        
        return
    
    # Get decisions from session state
    decisions_summary = st.session_state['decisions_summary']
    pipeline = st.session_state['pipeline']
    reports = pipeline.reports
    
    # Summary metrics
    dec_report = reports.get('decisions', {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(METRICS['buy_signals'], dec_report.get('buy', 0), help=HELP_TEXT['buy_signals'])
    with col2:
        st.metric(METRICS['hold_signals'], dec_report.get('hold', 0), help=HELP_TEXT['hold_signals'])
    with col3:
        st.metric(METRICS['sell_signals'], dec_report.get('sell', 0), help=HELP_TEXT['sell_signals'])
    with col4:
        st.metric(METRICS['insufficient_data'], dec_report.get('insufficient_data', 0), help=HELP_TEXT['insufficient_data'])
    
    st.divider()
    
    # Main recommendations table
    st.subheader(SECTIONS['investment_decisions'])
    
    if len(decisions_summary) > 0:
        # Traduire les décisions en français pour l'affichage
        display_df = decisions_summary.copy()
        display_df['Decision'] = display_df['Decision'].map(lambda x: DECISIONS.get(x, x))
        
        # Add color-coded decision column
        def color_decision(val):
            if val == DECISIONS['BUY']:
                return 'background-color: #d4edda; color: #155724;'
            elif val == DECISIONS['SELL']:
                return 'background-color: #f8d7da; color: #721c24;'
            elif val == DECISIONS['HOLD']:
                return 'background-color: #fff3cd; color: #856404;'
            else:
                return 'background-color: #e2e3e5; color: #383d41;'
        
        # Use map() instead of applymap() (pandas 2.1.0+ compatibility)
        styled_df = display_df.style.map(
            color_decision,
            subset=['Decision']
        )
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Filter controls
        with st.expander(SECTIONS['filter_recommendations']):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                decision_filter = st.multiselect(
                    FILTERS['decision_type'],
                    options=[DECISIONS['BUY'], DECISIONS['HOLD'], DECISIONS['SELL'], DECISIONS['INSUFFICIENT_DATA']],
                    default=[DECISIONS['BUY'], DECISIONS['SELL']]
                )
            
            with col2:
                min_conf = st.slider(FILTERS['min_confidence'], 0, 100, 50)
            
            with col3:
                min_score = st.slider(FILTERS['min_score'], 0, 100, 40)
            
            if st.button(BUTTONS['apply_filters']):
                filtered = display_df[
                    (display_df['Decision'].isin(decision_filter)) &
                    (display_df['Confidence'] >= min_conf) &
                    (display_df['Overall_Score'] >= min_score)
                ]
                st.write(f"Résultats filtrés: {len(filtered)} sociétés")
                st.dataframe(filtered, use_container_width=True)
    else:
        st.info(MESSAGES['no_recommendations'])
    
    st.divider()
    
    # Export options
    st.subheader(SECTIONS['export_decisions'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if len(decisions_summary) > 0:
            csv_data = decisions_summary.to_csv(index=False)
            st.download_button(
                BUTTONS['download_csv'],
                data=csv_data,
                file_name=f"dss_recommendations_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.button(BUTTONS['download_csv'], disabled=True, use_container_width=True)
    
    with col2:
        if len(decisions_summary) > 0:
            json_data = decisions_summary.to_json(orient='records', indent=2)
            st.download_button(
                BUTTONS['download_json'],
                data=json_data,
                file_name=f"dss_recommendations_{pd.Timestamp.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.button(BUTTONS['download_json'], disabled=True, use_container_width=True)
    
    with col3:
        if len(decisions_summary) > 0:
            excel_path = ROOT / 'data' / 'decisions_summary.parquet'
            if excel_path.exists():
                st.download_button(
                    BUTTONS['download_parquet'],
                    data=open(excel_path, 'rb').read(),
                    file_name=f"dss_recommendations_{pd.Timestamp.now().strftime('%Y%m%d')}.parquet",
                    mime="application/octet-stream",
                    use_container_width=True
                )
        else:
            st.button(BUTTONS['download_parquet'], disabled=True, use_container_width=True)
    
    st.divider()
    
    # Evidence panel
    st.subheader(SECTIONS['decision_evidence'])
    
    if len(decisions_summary) > 0:
        selected_company = st.selectbox(
            "Sélectionner une société pour voir les détails",
            options=decisions_summary['Company'].tolist()
        )
        
        company_row = decisions_summary[decisions_summary['Company'] == selected_company].iloc[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Traduire la décision pour l'affichage
            decision_display = DECISIONS.get(company_row['Decision'], company_row['Decision'])
            st.metric(METRICS['decision'], decision_display)
            st.metric(METRICS['overall_score'], f"{company_row['Overall_Score']}/100")
            st.metric(METRICS['confidence'], f"{company_row['Confidence']}%")
            st.metric(METRICS['latest_price'], f"{company_row['Cours']} MAD" if pd.notna(company_row['Cours']) else "N/A")
        
        with col2:
            st.write("**Signaux Individuels:**")
            signals = company_row['Signals']
            if signals and signals != 'no valid signals':
                for sig in signals.split(' | '):
                    st.write(f"• {sig}")
            else:
                st.write("Aucun signal valide disponible")
            
            st.write(f"**{METRICS['data_coverage']}:** {company_row['Data_Coverage']}")
            st.write(f"**Date:** {company_row['Date']}")
    
    st.divider()
    
    # Methodology status warning
    st.warning(WARNINGS['methodology_not_validated'])