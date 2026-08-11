"""
BVC Portfolio DSS - Interface Minimaliste
Analyse quotidienne du marché et génération de recommandations.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.components.state import init_session_state, save_session_state
from ui.components.persistence import get_state_manager
from src.pipeline import DSS_Pipeline
import pandas as pd
import tempfile
import traceback

ANALYSIS_STAGES = [
    ("Données", "import"),
    ("Normalisation", "normalization"),
    ("Contrôle qualité", "quality_filter"),
    ("Métriques de marché", "metrics"),
    ("Filtrage dynamique", "filtering"),
    ("Calcul des indicateurs", "indicators"),
    ("Signaux", "signals"),
    ("Décisions", "decisions"),
]


def ensure_pipeline() -> None:
    """Ensure a DSS pipeline object exists in session state."""
    if 'pipeline' not in st.session_state:
        st.session_state['pipeline'] = DSS_Pipeline(data_dir=ROOT / 'data')


def render_header():
    """En-tête minimaliste de l'application."""
    logo_path = ROOT / "ui" / "assets" / "logo.png"
    st.set_page_config(
        page_title="BVC Portfolio DSS",
        page_icon=Image.open(logo_path),
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    init_session_state()
    ensure_pipeline()

    st.title("BVC Portfolio DSS")
    st.caption("Analyse quotidienne du marché et génération de recommandations")
    st.divider()


def render_data_import():
    """Section d'importation des données (minimaliste)."""
    st.subheader("1. Données")

    market_file = st.session_state.get('market_file_name')
    index_file = st.session_state.get('index_file_name')
    market_imported = st.session_state.get('market_imported', False)
    index_imported = st.session_state.get('index_imported', False)
    ready_to_analyze = market_imported and index_imported

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Données marché**")
        uploaded_market = st.file_uploader(
            "📁 Importer le fichier marché",
            type=["xlsx", "xls"],
            key="market_upload",
            label_visibility="collapsed"
        )
        if market_imported:
            st.success(f"✓ {market_file or 'Fichier marché chargé'}")
        elif uploaded_market is not None:
            st.info(f"Fichier sélectionné : {uploaded_market.name}")
            # Persist uploaded file to a temporary path for previewing pages
            if ('market_upload_temp_path' not in st.session_state) or (st.session_state.get('market_upload_name') != uploaded_market.name):
                tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
                tmp.write(uploaded_market.getvalue())
                tmp.flush()
                tmp.close()
                st.session_state['market_upload_temp_path'] = tmp.name
                st.session_state['market_upload_name'] = uploaded_market.name
                st.session_state['market_preview_page'] = 0

            temp_path = st.session_state.get('market_upload_temp_path')
            try:
                xls = pd.ExcelFile(temp_path, engine='openpyxl')
                sheets = xls.sheet_names
                selected_sheet = st.selectbox('Feuille à prévisualiser', sheets, key='market_preview_sheet')
                page = st.session_state.get('market_preview_page', 0)

                colp1, colp2 = st.columns([1, 8])
                with colp1:
                    if st.button('◀', key='market_prev'):
                        if page > 0:
                            st.session_state['market_preview_page'] = page - 1
                    if st.button('▶', key='market_next'):
                        st.session_state['market_preview_page'] = page + 1
                with colp2:
                    from src.ingestion import read_sheet_page, get_sheet_row_count
                    df_page, total = read_sheet_page(temp_path, selected_sheet, page=st.session_state.get('market_preview_page', 0), page_size=10)
                    total_pages = (total + 9) // 10 if total > 0 else 0
                    st.write(f"Page {st.session_state.get('market_preview_page', 0)+1} / {total_pages} — {total} lignes")
                    st.dataframe(df_page.fillna(''), use_container_width=True, height=200)

            except Exception:
                st.info(f"Fichier sélectionné : {uploaded_market.name}")

            if st.button("Importer marché", key="import_market", use_container_width=True):
                ensure_pipeline()
                import_market_data(uploaded_market)

    with col2:
        st.write("**Composition des indices**")
        uploaded_comp = st.file_uploader(
            "📁 Importer la composition",
            type=["xlsx", "xls"],
            key="comp_upload",
            label_visibility="collapsed"
        )
        if index_imported:
            st.success(f"✓ {index_file or 'Composition chargée'}")
        elif uploaded_comp is not None:
            st.info(f"Fichier sélectionné : {uploaded_comp.name}")
            # write temp file for preview
            if ('comp_upload_temp_path' not in st.session_state) or (st.session_state.get('comp_upload_name') != uploaded_comp.name):
                tmpc = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
                tmpc.write(uploaded_comp.getvalue())
                tmpc.flush()
                tmpc.close()
                st.session_state['comp_upload_temp_path'] = tmpc.name
                st.session_state['comp_upload_name'] = uploaded_comp.name
                st.session_state['comp_preview_page'] = 0

            tempc_path = st.session_state.get('comp_upload_temp_path')
            try:
                xls_c = pd.ExcelFile(tempc_path, engine='openpyxl')
                sheets_c = xls_c.sheet_names
                selc = st.selectbox('Feuille à prévisualiser', sheets_c, key='comp_preview_sheet')
                pagec = st.session_state.get('comp_preview_page', 0)
                colp1, colp2 = st.columns([1, 8])
                with colp1:
                    if st.button('◀', key='comp_prev'):
                        if pagec > 0:
                            st.session_state['comp_preview_page'] = pagec - 1
                    if st.button('▶', key='comp_next'):
                        st.session_state['comp_preview_page'] = pagec + 1
                with colp2:
                    from src.ingestion import read_sheet_page, get_sheet_row_count
                    df_page_c, total_c = read_sheet_page(tempc_path, selc, page=st.session_state.get('comp_preview_page', 0), page_size=10)
                    total_pages_c = (total_c + 9) // 10 if total_c > 0 else 0
                    st.write(f"Page {st.session_state.get('comp_preview_page', 0)+1} / {total_pages_c} — {total_c} lignes")
                    st.dataframe(df_page_c.fillna(''), use_container_width=True, height=200)
            except Exception:
                st.info(f"Fichier sélectionné : {uploaded_comp.name}")

            if st.button("Importer composition", key="import_comp", use_container_width=True):
                ensure_pipeline()
                import_composition_data(uploaded_comp)

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"{'✓' if market_imported else '○'} Marché")
    with col2:
        st.write(f"{'✓' if index_imported else '○'} Composition")
    with col3:
        st.write(f"{'✓' if ready_to_analyze else '○'} Prêt à analyser")


def render_analysis():
    """Section d'analyse unique."""
    st.divider()
    st.subheader("2. Analyse")

    market_imported = st.session_state.get('market_imported', False)
    index_imported = st.session_state.get('index_imported', False)
    ready_to_analyze = market_imported and index_imported
    pipeline_complete = st.session_state.get('pipeline_complete', False)

    if ready_to_analyze:
        if pipeline_complete:
            st.success("Analyse du portefeuille terminée")
            if st.button("Relancer l'analyse", use_container_width=True):
                run_pipeline_analysis()
        else:
            if st.button("Analyser le portefeuille", use_container_width=True):
                ensure_pipeline()
                run_pipeline_analysis()
    else:
        st.info("Importer les deux fichiers pour lancer l'analyse")

    if st.session_state.get('analysis_in_progress') or pipeline_complete:
        render_analysis_progress()


def render_recommendations():
    """Section des recommandations (essentiel)."""
    st.divider()
    st.subheader("3. Recommandations")

    if st.session_state.get('pipeline_complete') and 'decisions_summary' in st.session_state:
        decisions_df = st.session_state['decisions_summary']
        if len(decisions_df) == 0:
            st.info("Aucune recommandation disponible après l'analyse.")
            return

        buy_count = (decisions_df['Decision'] == 'BUY').sum()
        hold_count = (decisions_df['Decision'] == 'HOLD').sum()
        sell_count = (decisions_df['Decision'] == 'SELL').sum()
        insuf_count = (decisions_df['Decision'] == 'INSUFFICIENT_DATA').sum()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("ACHAT", buy_count)
        with col2:
            st.metric("CONSERVER", hold_count)
        with col3:
            st.metric("VENDRE", sell_count)
        with col4:
            st.metric("INSUFFISANT", insuf_count)

        st.divider()
        st.write("**Décisions d'investissement**")

        display_df = decisions_df.copy()
        decision_map = {
            'BUY': 'ACHAT',
            'HOLD': 'CONSERVER',
            'SELL': 'VENDRE',
            'INSUFFICIENT_DATA': 'INSUFFISANT'
        }
        display_df['Décision'] = display_df['Decision'].map(decision_map)
        essential_cols = ['Company', 'Overall_Score', 'Confidence', 'Décision']
        display_df = display_df[essential_cols].copy()
        display_df.columns = ['Société', 'Score', 'Confiance %', 'Décision']
        display_df['Score'] = display_df['Score'].round(1)
        display_df['Confiance %'] = display_df['Confiance %'].round(0).astype(int)

        def color_decision(val):
            if val == 'ACHAT':
                return 'background-color: #d4edda;'
            if val == 'VENDRE':
                return 'background-color: #f8d7da;'
            if val == 'CONSERVER':
                return 'background-color: #fff3cd;'
            return 'background-color: #e2e3e5;'

        styled_df = display_df.style.map(color_decision, subset=['Décision'])
        st.dataframe(styled_df, use_container_width=True, height=380)

        st.download_button(
            "Exporter en CSV",
            data=decisions_df.to_csv(index=False),
            file_name="recommandations_dss.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.divider()
        companies = decisions_df['Company'].unique()
        selected_company = st.selectbox("Voir les détails pour une société", companies)
        if selected_company:
            render_company_details(selected_company, decisions_df)

    elif st.session_state.get('pipeline_complete'):
        st.info("Analyse terminée, mais aucune recommandation disponible")
    else:
        st.info("Lancez d'abord l'analyse pour voir les recommandations")


def render_company_details(company_name, decisions_df):
    """Afficher les détails d'une société sélectionnée."""
    company_data = decisions_df[decisions_df['Company'] == company_name].iloc[0]
    
    decision_map = {
        'BUY': 'ACHAT',
        'HOLD': 'CONSERVER', 
        'SELL': 'VENDRE',
        'INSUFFICIENT_DATA': 'DONNÉES INSUFFISANTES'
    }
    decision_display = decision_map.get(company_data['Decision'], company_data['Decision'])

    st.markdown(f"### {company_name}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Décision", decision_display)
    with col2:
        st.metric("Score", f"{company_data['Overall_Score']:.1f}/100")
    with col3:
        st.metric("Confiance", f"{company_data['Confidence']:.0f}%")

    st.write("**Pourquoi ?**")
    signals = company_data.get('Signals')
    if pd.notna(signals) and signals != 'no valid signals':
        for signal in signals.split(' | '):
            st.write(f"- {signal}")
    else:
        st.write("Aucun signal détaillé disponible")

    with st.expander("Voir les indicateurs détaillés"):
        decisions_full = st.session_state.get('pipeline_results', {}).get('decisions')
        if decisions_full is not None:
            detail_row = decisions_full[decisions_full['Company'] == company_name]
            if not detail_row.empty:
                detail_row = detail_row.iloc[0]
                known_indicators = [
                    'RSI14', 'SMA20', 'SMA50', 'EMA20', 'MACD',
                    'MACD Signal', 'MACD Histogram', 'RVOL', 'VWAP', 'HV'
                ]
                shown = False
                for indicator in known_indicators:
                    if indicator in detail_row.index and pd.notna(detail_row[indicator]):
                        st.write(f"- **{indicator}:** {detail_row[indicator]}")
                        shown = True
                if not shown:
                    st.write("Aucun indicateur détaillé disponible pour cette société.")
            else:
                st.write("Aucun détail trouvé pour cette société.")
        else:
            st.write("Détails techniques non disponibles.")


def render_analysis_progress():
    """Afficher la progression de l'analyse."""
    st.divider()
    st.write("**Progression de l'analyse**")

    current_step = st.session_state.get('analysis_step')
    pipeline_complete = st.session_state.get('pipeline_complete', False)
    step_order = {key: idx for idx, (_, key) in enumerate(ANALYSIS_STAGES)}
    current_index = step_order.get(current_step, -1)

    cols = st.columns(len(ANALYSIS_STAGES))
    for idx, (name, key) in enumerate(ANALYSIS_STAGES):
        if key == 'import':
            done = st.session_state.get('market_imported', False) and st.session_state.get('index_imported', False)
            status = '✓' if done else '○'
        elif pipeline_complete or (current_index > idx):
            status = '✓'
        elif current_step == key:
            status = '●'
        else:
            status = '○'

        with cols[idx]:
            st.write(f"{status} {name}")


# Fonctions d'importation
def import_market_data(uploaded_file):
    """Importer les données marché."""
    with st.spinner("Importation des données marché..."):
        try:
            # Créer fichier temporaire
            suffix = '.xlsx' if uploaded_file.name.endswith('.xlsx') else '.xls'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='wb') as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name
            
            # Initialiser pipeline
            if 'pipeline' not in st.session_state:
                st.session_state['pipeline'] = DSS_Pipeline(data_dir=ROOT / 'data')
            
            pipeline = st.session_state['pipeline']
            
            # Importer données
            unified, ingest_report = pipeline.ingest_market_data(temp_path)
            
            # Valider
            from src.validation import validate_dataset
            all_passed, validation_report = validate_dataset(unified, verbose=False)
            
            # Stocker
            st.session_state['unified_data'] = unified
            st.session_state['ingest_report'] = ingest_report
            st.session_state['market_imported'] = True
            st.session_state['market_file_name'] = uploaded_file.name
            
            # Sauvegarder
            save_session_state()
            
            # Nettoyer
            try:
                Path(temp_path).unlink()
            except:
                pass
            
            st.success(f"Données marché importées: {len(unified)} enregistrements, {unified['Company'].nunique()} sociétés")
            st.rerun()
            
        except Exception as e:
            st.error(f"Erreur d'importation: {str(e)}")
            with st.expander("Détails"):
                st.code(traceback.format_exc())


def import_composition_data(uploaded_file):
    """Importer la composition des indices."""
    with st.spinner("Importation de la composition..."):
        try:
            # Créer fichier temporaire
            suffix = '.xlsx' if uploaded_file.name.endswith('.xlsx') else '.xls'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='wb') as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name
            
            # Initialiser pipeline si nécessaire
            if 'pipeline' not in st.session_state:
                st.session_state['pipeline'] = DSS_Pipeline(data_dir=ROOT / 'data')
            
            pipeline = st.session_state['pipeline']
            
            # Importer composition
            composition_df, comp_report = pipeline.ingest_index_composition(temp_path)
            
            # Stocker
            st.session_state['composition_data'] = composition_df
            st.session_state['composition_report'] = comp_report
            st.session_state['index_imported'] = True
            st.session_state['index_file_name'] = uploaded_file.name
            
            # Sauvegarder
            save_session_state()
            
            # Nettoyer
            try:
                Path(temp_path).unlink()
            except:
                pass
            
            st.success(f"Composition importée: {comp_report['index']}, {len(composition_df)} titres")
            st.rerun()
            
        except Exception as e:
            st.error(f"Erreur d'importation: {str(e)}")
            with st.expander("Détails"):
                st.code(traceback.format_exc())


def run_pipeline_analysis():
    """Exécuter le pipeline d'analyse."""
    ensure_pipeline()
    st.session_state['analysis_in_progress'] = True
    st.session_state['analysis_step'] = 'normalization'
    
    try:
        pipeline = st.session_state['pipeline']
        market_df = st.session_state['unified_data']
        composition_df = st.session_state['composition_data']

        progress = st.progress(0)
        status = st.empty()

        status.markdown("**Normalisation...**")
        progress.progress(10)

        st.session_state['analysis_step'] = 'quality_filter'
        status.markdown("**Contrôle qualité...**")
        progress.progress(20)
        unified_df, _ = pipeline.apply_quality_filter(market_df)

        st.session_state['analysis_step'] = 'metrics'
        status.markdown("**Calcul des métriques...**")
        progress.progress(40)

        st.session_state['analysis_step'] = 'filtering'
        status.markdown("**Filtrage dynamique...**")
        progress.progress(55)
        investable_df, _ = pipeline.apply_dynamic_filter(unified_df, composition_df)

        st.session_state['analysis_step'] = 'indicators'
        status.markdown("**Calcul des indicateurs...**")
        progress.progress(70)
        indicators_df, _ = pipeline.compute_indicators(investable_df)

        st.session_state['analysis_step'] = 'signals'
        status.markdown("**Calcul des signaux...**")
        progress.progress(85)
        signals_df, _ = pipeline.compute_signals_and_scores(indicators_df)

        st.session_state['analysis_step'] = 'decisions'
        status.markdown("**Génération des décisions...**")
        progress.progress(95)
        decisions_df, decisions_summary, _ = pipeline.make_decisions(signals_df)

        progress.progress(100)
        status.markdown("**Analyse terminée**")

        st.session_state['decisions_summary'] = decisions_summary
        st.session_state['pipeline_results'] = {
            'decisions': decisions_df,
            'signals': signals_df,
            'indicators': indicators_df,
            'investable_universe': investable_df,
            'unified_dataset': unified_df,
        }
        st.session_state['pipeline_complete'] = True

        st.session_state['analysis_in_progress'] = False
        st.session_state['analysis_step'] = None

        save_session_state()
        st.experimental_rerun()

    except Exception as e:
        st.error(f"Erreur d'analyse: {str(e)}")
        with st.expander("Détails"):
            st.code(traceback.format_exc())
        st.session_state['analysis_in_progress'] = False
        st.session_state['analysis_step'] = None


def main():
    """Fonction principale."""
    render_header()
    render_data_import()
    render_analysis()
    render_recommendations()
    
    # Pied de page minimaliste
    st.divider()
    st.caption("BVC Portfolio DSS v2.0 • Interface minimaliste")


if __name__ == "__main__":
    main()