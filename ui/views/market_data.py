from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path
import sys
import tempfile

# Add src to path
ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.translations import TITLES, BUTTONS, MESSAGES, METRICS, TABS, SECTIONS, TABLE_COLUMNS
from ui.components.state import init_session_state, mark_market_uploaded, save_session_state
from ui.components.status_cards import render_metric_cards
from ui.components.tables import render_preview_table
from src.pipeline import DSS_Pipeline


def render() -> None:
    """Vue des données marché - Import et validation."""
    init_session_state()
    st.title(TITLES['market_data_title'])
    st.caption(TITLES['market_data_caption'])

    uploaded_file = st.file_uploader("Importer les Données Marché (Excel)", type=["xlsx", "xls"], accept_multiple_files=False)
    
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
                    
                    # Initialize pipeline
                    if 'pipeline' not in st.session_state:
                        st.session_state['pipeline'] = DSS_Pipeline(data_dir=ROOT / 'data')
                    
                    pipeline = st.session_state['pipeline']
                    
                    # Ingest market data
                    unified, ingest_report = pipeline.ingest_market_data(temp_path)
                    
                    # Validate dataset
                    from src.validation import validate_dataset
                    all_passed, validation_report = validate_dataset(unified, verbose=False)
                    
                    # Store in session state
                    st.session_state['unified_data'] = unified
                    st.session_state['ingest_report'] = ingest_report
                    st.session_state['validation_report'] = validation_report
                    st.session_state['import_status'] = 'success' if all_passed else 'warning'
                    st.session_state['market_imported'] = True
                    st.session_state['market_file_name'] = uploaded_file.name
                    
                    # Sauvegarder l'état pour persistance
                    save_session_state()
                    
                    # Clean up temp file
                    try:
                        Path(temp_path).unlink()
                    except:
                        pass
                    
                    st.success(MESSAGES['success_excel'].format(path='data/market_data_raw.parquet'))
                    st.rerun()
                    
                except Exception as e:
                    st.session_state['import_status'] = 'error'
                    st.session_state['import_error'] = str(e)
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
        if 'import_status' in st.session_state:
            st.divider()
            
            status = st.session_state['import_status']
            
            if status == 'error':
                st.error(MESSAGES['error_import'].format(error=st.session_state.get('import_error', 'Erreur inconnue')))
            
            elif status in ('success', 'warning'):
                ingest_report = st.session_state['ingest_report']
                validation_report = st.session_state['validation_report']
                unified = st.session_state['unified_data']
                
                # Ingestion summary metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric(METRICS['sheets_included'], len(ingest_report['sheets_included']))
                with col2:
                    st.metric(METRICS['total_records'], ingest_report['unified_records'])
                with col3:
                    st.metric(METRICS['companies'], ingest_report['unified_companies'])
                with col4:
                    st.metric(METRICS['sessions'], ingest_report['unified_sessions'])
                with col5:
                    st.metric(METRICS['variables'], len(ingest_report['unified_variables']))
                
                st.divider()
                
                # Tabs for details
                tab1, tab2, tab3 = st.tabs([TABS['ingestion_report'], TABS['data_quality'], TABS['preview']])
                
                with tab1:
                    st.subheader(TABS['included_sheets'])
                    included_data = []
                    for s in ingest_report['sheets_included']:
                        included_data.append({
                            TABLE_COLUMNS['Sheet']: s['name'],
                            TABLE_COLUMNS['Variable']: s['canonical_variable'],
                            'Confiance': s['confidence'],
                            TABLE_COLUMNS['Records']: s['records']
                        })
                    st.dataframe(pd.DataFrame(included_data), use_container_width=True, hide_index=True)
                    
                    if ingest_report['sheets_excluded']:
                        st.subheader(TABS['excluded_sheets'])
                        excluded_data = []
                        for s in ingest_report['sheets_excluded']:
                            excluded_data.append({
                                TABLE_COLUMNS['Sheet']: s['name'],
                                TABLE_COLUMNS['Reason']: s['reason']
                            })
                        st.dataframe(pd.DataFrame(excluded_data), use_container_width=True, hide_index=True)
                
                with tab2:
                    # Validation summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Tests Totaux", validation_report['total_tests'])
                    with col2:
                        st.metric("Réussis", validation_report['passed'], delta_color='off')
                    with col3:
                        st.metric("Avertissements", validation_report['warnings'], delta_color='inverse')
                    with col4:
                        st.metric("Critiques", validation_report['critical'], delta_color='inverse')
                    
                    # Validation details by category
                    for category, results in validation_report['by_category'].items():
                        st.subheader(category)
                        for result in results:
                            status_icon = "✓" if result.passed else ("⚠" if result.severity == 'warning' else "✗")
                            
                            with st.expander(f"{status_icon} {result.name}", expanded=not result.passed):
                                st.write(f"**{result.message}**")
                                if result.details:
                                    detail_df = pd.DataFrame(list(result.details.items()), columns=['Clé', 'Valeur'])
                                    st.dataframe(detail_df, use_container_width=True, hide_index=True)
                
                with tab3:
                    st.subheader(SECTIONS['dataset_preview'])
                    st.dataframe(unified.head(20), use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(SECTIONS['summary_statistics'])
                        stats = {
                            'Métrique': ['Lignes Totales', 'Sociétés Uniques', 'Sessions Uniques', 'Plage de Dates'],
                            'Valeur': [
                                len(unified),
                                unified['CODE_ISIN'].nunique(),
                                unified['Date'].nunique(),
                                f"{unified['Date'].min().date()} à {unified['Date'].max().date()}"
                            ]
                        }
                        st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)
                    
                    with col2:
                        st.subheader(SECTIONS['data_completeness'])
                        completeness = {
                            'Variable': ['Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'],
                            'Couverture': [
                                f"{unified['Cours'].notna().sum() / len(unified) * 100:.1f}%",
                                f"{unified['Bid'].notna().sum() / len(unified) * 100:.1f}%",
                                f"{unified['Ask'].notna().sum() / len(unified) * 100:.1f}%",
                                f"{unified['Volume MC'].notna().sum() / len(unified) * 100:.1f}%",
                                f"{unified['Quantité MC'].notna().sum() / len(unified) * 100:.1f}%"
                            ]
                        }
                        st.dataframe(pd.DataFrame(completeness), use_container_width=True, hide_index=True)
                
                # Final status
                st.divider()
                if status == 'success':
                    st.success("✓ Dataset validé avec succès. Prêt pour l'analyse.")
                else:
                    st.warning("⚠ Le dataset contient des avertissements. Vérifiez les détails de validation avant de continuer.")
    else:
        st.info(MESSAGES['upload_info'])