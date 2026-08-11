from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.translations import TITLES, BUTTONS, MESSAGES, METRICS, SECTIONS, PIPELINE_STAGES
from ui.components.state import init_session_state, mark_index_uploaded, save_session_state
from ui.components.status_cards import render_metric_cards
from ui.components.tables import render_preview_table
from src.pipeline import DSS_Pipeline


def render() -> None:
    """Vue de la composition d'indice - Import et validation."""
    init_session_state()
    st.title(TITLES['index_composition_title'])
    st.caption(TITLES['index_composition_caption'])

    uploaded_file = st.file_uploader("Importer la Composition d'Indice (Excel)", type=["xlsx"], accept_multiple_files=False, key="index_upload")
    
    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📁 Fichier: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        with col2:
            process_clicked = st.button(BUTTONS['parse_validate'], use_container_width=True)
        
        if process_clicked:
            with st.spinner(MESSAGES['processing']):
                try:
                    # Create temp file with proper suffix
                    suffix = '.xlsx' if uploaded_file.name.endswith('.xlsx') else '.xls'
                    
                    # Write uploaded file to temporary location
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='wb') as tmp:
                        tmp.write(uploaded_file.getvalue())
                        temp_path = tmp.name
                    
                    # Get or create pipeline
                    if 'pipeline' not in st.session_state:
                        st.session_state['pipeline'] = DSS_Pipeline(data_dir=ROOT / 'data')
                    
                    pipeline = st.session_state['pipeline']
                    
                    # Ingest composition
                    composition_df, comp_report = pipeline.ingest_index_composition(temp_path)
                    
                    # Store in session state
                    st.session_state['composition_data'] = composition_df
                    st.session_state['composition_report'] = comp_report
                    st.session_state['index_imported'] = True
                    st.session_state['index_file_name'] = uploaded_file.name
                    
                    # Sauvegarder l'état pour persistance
                    save_session_state()
                    
                    # Clean up temp file
                    try:
                        Path(temp_path).unlink()
                    except:
                        pass
                    
                    st.success(MESSAGES['success_excel'].format(path='data/index_composition.parquet'))
                    st.rerun()
                    
                except Exception as e:
                    import traceback
                    st.error(MESSAGES['error_import'].format(error=str(e)))
                    with st.expander(MESSAGES['error_details']):
                        st.code(traceback.format_exc())
                    
                    # Clean up temp file on error
                    try:
                        if 'temp_path' in locals():
                            Path(temp_path).unlink()
                    except:
                        pass
        
        # Display results if available
        if 'composition_data' in st.session_state:
            comp_df = st.session_state['composition_data']
            comp_report = st.session_state['composition_report']
            
            st.divider()
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(METRICS['index'], comp_report['index'])
            with col2:
                st.metric(METRICS['total_securities'], comp_report['total_securities'])
            with col3:
                st.metric(METRICS['columns'], len(comp_report['columns']))
            
            st.divider()
            
            # Preview table
            st.subheader(SECTIONS['composition_preview'])
            st.dataframe(comp_df.head(20), use_container_width=True)
            
            # Statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(SECTIONS['summary_statistics'])
                stats = {
                    'Métrique': ['Titres Totaux', 'FF Médian', 'Cap. Marché FF Médiane (MAD)', 'Poids Total'],
                    'Valeur': [
                        len(comp_df),
                        f"{comp_df['FF'].median():.3f}" if 'FF' in comp_df.columns else 'N/A',
                        f"{comp_df['FF_MarketCap'].median():,.0f}" if 'FF_MarketCap' in comp_df.columns else 'N/A',
                        f"{comp_df['Weight'].sum():.2f}%" if 'Weight' in comp_df.columns else 'N/A'
                    ]
                }
                st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader(SECTIONS['top_10_weight'])
                if 'Weight' in comp_df.columns and 'Company' in comp_df.columns:
                    top10 = comp_df.nlargest(10, 'Weight')[['Company', 'Weight']]
                    top10['Weight'] = top10['Weight'].map(lambda x: f"{x:.2f}%")
                    st.dataframe(top10, use_container_width=True, hide_index=True)
                else:
                    st.info("Colonne Weight ou Company non disponible")
    
    else:
        st.info(MESSAGES['upload_info'].replace("Excel", "Excel de composition d'indice"))
    
    st.divider()
    
    # Run pipeline button (only if both files uploaded)
    if st.session_state.get('market_imported', False) and st.session_state.get('index_imported', False):
        st.success(MESSAGES['pipeline_ready'])
        
        if st.button(BUTTONS['run_pipeline'], use_container_width=True, type="primary"):
            run_complete_pipeline()
    else:
        st.warning(MESSAGES['no_decisions'].replace('Veuillez télécharger les données marché et la composition de l\'indice, puis lancer le pipeline', 'Téléchargez à la fois les données marché et la composition d\'indice pour lancer le pipeline'))


def run_complete_pipeline():
    """Exécuter le pipeline DSS complet."""
    with st.spinner(MESSAGES['running_pipeline']):
        try:
            pipeline = st.session_state['pipeline']
            market_df = st.session_state['unified_data']
            composition_df = st.session_state['composition_data']
            
            # Progress bar avec étapes en français
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate progress with French stage names
            stages = [
                (20, PIPELINE_STAGES['quality_filter']),
                (40, PIPELINE_STAGES['dynamic_filter']),
                (60, PIPELINE_STAGES['indicators']),
                (80, PIPELINE_STAGES['signals']),
                (100, PIPELINE_STAGES['decisions']),
            ]
            
            import time
            for progress, stage_text in stages:
                status_text.text(stage_text)
                progress_bar.progress(progress)
                time.sleep(0.5)
            
            # Run pipeline
            results = pipeline.run_pipeline(market_df, composition_df)
            
            # Store results
            st.session_state['decisions_summary'] = results['decisions_summary']
            st.session_state['pipeline_results'] = results
            st.session_state['pipeline_complete'] = True
            
            # Sauvegarder l'état complet
            save_session_state()
            
            progress_bar.progress(100)
            status_text.text("✅ Terminé!")
            
            st.success(MESSAGES['pipeline_complete'])
            
            # Show summary in French
            dec_report = pipeline.reports['decisions']
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("ACHAT", dec_report['buy'])
            with col2:
                st.metric("CONSERVER", dec_report['hold'])
            with col3:
                st.metric("VENDRE", dec_report['sell'])
            with col4:
                st.metric("Données Insuffisantes", dec_report['insufficient_data'])
            
            # Note about sample data
            st.info(MESSAGES['insufficient_data_note'])
            
        except Exception as e:
            import traceback
            st.error(f"❌ Échec du pipeline: {str(e)}")
            with st.expander("Détails de l'erreur"):
                st.code(traceback.format_exc())