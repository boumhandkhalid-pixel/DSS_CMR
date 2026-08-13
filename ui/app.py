"""
DSS BVC - Système d'Aide à la Décision
Pôle Gestion du Portefeuille - CMR
Interface professionnelle pour l'analyse de portefeuille.
"""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import tempfile
import logging
from typing import Optional
from datetime import datetime
import uuid

# Configuration du logger pour les erreurs techniques (côté développeur)
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dss_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration DOIT être la première commande Streamlit
# Déterminer le chemin du favicon
_current_file = Path(__file__).resolve()
_favicon_path = _current_file.parents[1] / 'ui' / 'assets' / 'CMR-logo.png'

st.set_page_config(
    page_title="DSS Gestion de Portefeuille - CMR",
    page_icon=str(_favicon_path) if _favicon_path.exists() else "📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ajout du path APRÈS set_page_config
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.components.state import init_session_state, save_session_state, reset_session_state
from src.pipeline import DSS_Pipeline


def load_css():
    """Charge le CSS institutionnel CMR."""
    css_file = ROOT / 'ui' / 'assets' / 'styles.css'
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def generate_error_reference() -> str:
    """Génère un ID d'incident unique pour le support."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"DSS-{timestamp}-{unique_id}"


def show_user_error(message: str, error_ref: Optional[str] = None):
    """
    Affiche une erreur métier à l'utilisateur (sans détails techniques).
    Les détails techniques sont loggés pour le développeur.
    """
    st.error(f"❌ {message}")
    if error_ref:
        st.caption(f"Référence incident : `{error_ref}`")
        st.caption("Si le problème persiste, contactez l'équipe support avec cette référence.")


def init_app():
    """Initialisation de l'application."""
    init_session_state()
    
    # Créer pipeline si nécessaire
    if 'pipeline' not in st.session_state:
        st.session_state['pipeline'] = DSS_Pipeline(data_dir=ROOT / 'data')
    
    # Initialiser l'état de sélection d'indice
    if 'selected_index' not in st.session_state:
        st.session_state['selected_index'] = None
    if 'available_indices' not in st.session_state:
        st.session_state['available_indices'] = []


def render_header():
    """En-tête professionnel avec logo CMR utilisant les classes CSS."""
    # TEST: Utiliser le logo CMR au lieu du logo portefeuille
    logo_path = ROOT / 'ui' / 'assets' / 'CMR-logo.png'
    # Original: logo_path = ROOT / 'ui' / 'assets' / 'gestion-portefeuille_logo.png'
    
    if logo_path.exists():
        # Utiliser les classes CSS pour un affichage propre
        st.markdown(f"""
            <div class="cmr-logo-header">
                <div class="cmr-logo-container">
                    <img src="data:image/png;base64,{get_base64_image(logo_path)}" alt="Logo CMR">
                </div>
                <div class="cmr-logo-header-text">
                    <h1>Système d'Aide à la Décision</h1>
                    <p class="caption">Pôle Gestion de Portefeuille - Caisse Marocaine des Retraites</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback sans logo
        st.title("Système d'Aide à la Décision")
        st.caption("Pôle Gestion de Portefeuille - Caisse Marocaine des Retraites")
    
    st.divider()


def get_base64_image(image_path: Path) -> str:
    """Convertit une image en base64 pour l'embedding HTML."""
    import base64
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def render_import_section():
    """
    Section 1: Importation des Données
    Interface minimaliste et professionnelle.
    """
    st.subheader("📥 Importer les Données")
    
    col1, col2 = st.columns(2)
    
    # Colonne 1: Données Marché
    with col1:
        st.markdown("**Données Marché**")
        
        market_imported = st.session_state.get('market_imported', False)
        
        market_file = st.file_uploader(
            "Fichier Excel contenant l'historique des cours",
            type=["xlsx", "xls"],
            key=f"market_upload_{st.session_state.get('reset_counter', 0)}",
            help="Données historiques : Date, Cours, Volume, etc."
        )
        
        if market_file:
            if st.button("📤 Importer le Marché", key="btn_import_market", use_container_width=True, type="primary"):
                import_market_data(market_file)
        elif market_imported:
            filename = st.session_state.get('market_file_name', 'Fichier marché')
            unified = st.session_state.get('unified_data')
            if unified is not None:
                n_companies = unified['Company'].nunique()
                n_records = len(unified)
                st.success(f"✓ {filename}")
                st.caption(f"📊 {n_companies} sociétés · {n_records:,} observations")
    
    # Colonne 2: Composition Indices
    with col2:
        st.markdown("**Composition des Indices**")
        
        index_imported = st.session_state.get('index_imported', False)
        
        comp_file = st.file_uploader(
            "Fichier Excel de composition des indices",
            type=["xlsx", "xls"],
            key=f"comp_upload_{st.session_state.get('reset_counter', 0)}",
            help="Composition MASI, MADEX et autres indices de référence"
        )
        
        if comp_file:
            if st.button("📤 Importer la Composition", key="btn_import_comp", use_container_width=True, type="primary"):
                import_composition_data(comp_file)
        elif index_imported:
            filename = st.session_state.get('index_file_name', 'Composition')
            comp_data = st.session_state.get('composition_data')
            if comp_data is not None:
                n_securities = len(comp_data)
                indices = comp_data['Index'].nunique() if 'Index' in comp_data.columns else 'N/A'
                st.success(f"✓ {filename}")
                st.caption(f"📋 {n_securities} titres · {indices} indices")
    
    # Statut global
    market_ok = st.session_state.get('market_imported', False)
    comp_ok = st.session_state.get('index_imported', False)
    
    if market_ok or comp_ok:
        st.divider()
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if market_ok:
                st.markdown("✅ **Données marché chargées**")
            else:
                st.markdown("⏳ Données marché en attente")
        
        with col2:
            if comp_ok:
                st.markdown("✅ **Composition chargée**")
            else:
                st.markdown("⏳ Composition en attente")
        
        with col3:
            if st.button("🔄 Réinitialiser", use_container_width=True, type="secondary"):
                reset_session_state()
                st.rerun()


def render_analysis_section():
    """
    Section 2: Analyse du Portefeuille
    Action unique : Analyser le portefeuille
    """
    st.divider()
    st.subheader("⚙️ Analyser le Portefeuille")
    
    market_ok = st.session_state.get('market_imported', False)
    comp_ok = st.session_state.get('index_imported', False)
    ready = market_ok and comp_ok
    pipeline_complete = st.session_state.get('pipeline_complete', False)
    in_progress = st.session_state.get('analysis_in_progress', False)
    
    if not ready:
        st.info("📋 Veuillez d'abord importer les données marché et la composition des indices pour lancer l'analyse.")
        return
    
    if in_progress:
        st.warning("⏳ Analyse en cours, veuillez patien ter...")
        render_progress()
        return
    
    # Interface selon état
    if pipeline_complete:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success("✅ Analyse terminée avec succès")
            decisions = st.session_state.get('decisions_summary')
            if decisions is not None:
                n_analyzed = len(decisions)
                st.caption(f"📊 {n_analyzed} titres analysés")
        with col2:
            if st.button("🔄 Relancer l'Analyse", use_container_width=True):
                run_analysis()
    else:
        st.markdown("""
        L'analyse complète du portefeuille comprend :
        - ✓ Normalisation et validation des données
        - ✓ Contrôle qualité et métriques de marché
        - ✓ Filtrage dynamique de l'univers investissable
        - ✓ Calcul des indicateurs techniques
        - ✓ Génération des signaux et scoring
        - ✓ Décisions finales : **BUY / HOLD / SELL**
        """)
        st.divider()
        if st.button("🚀 Analyser le Portefeuille", type="primary", use_container_width=True):
            run_analysis()


def render_recommendations_section():
    """
    Section 3: Recommandations
    Affichage professionnel avec filtres.
    """
    st.divider()
    st.subheader("📈 Recommandations d'Investissement")
    
    if not st.session_state.get('pipeline_complete', False):
        st.info("📊 Les recommandations apparaîtront après l'analyse du portefeuille.")
        return
    
    decisions = st.session_state.get('decisions_summary')
    
    if decisions is None or len(decisions) == 0:
        st.warning("⚠️ Aucune recommandation disponible")
        return
    
    # Métriques principales - Cards institutionnels
    buy = (decisions['Decision'] == 'BUY').sum()
    hold = (decisions['Decision'] == 'HOLD').sum()
    sell = (decisions['Decision'] == 'SELL').sum()
    insuf = (decisions['Decision'] == 'INSUFFICIENT_DATA').sum()
    total = len(decisions)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Total", total)
    with col2:
        st.metric("🟢 BUY", buy)
    with col3:
        st.metric("🟡 HOLD", hold)
    with col4:
        st.metric("🔴 SELL", sell)
    with col5:
        st.metric("⚪ INSUFFICIENT", insuf)
    
    st.divider()
    
    # Filtres
    st.markdown("**Filtrer les recommandations**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        show_all = st.checkbox("Tout afficher", value=True, key="filter_all")
    with col2:
        show_buy = st.checkbox(f"BUY ({buy})", value=False, key="filter_buy", disabled=show_all)
    with col3:
        show_hold = st.checkbox(f"HOLD ({hold})", value=False, key="filter_hold", disabled=show_all)
    with col4:
        show_sell = st.checkbox(f"SELL ({sell})", value=False, key="filter_sell", disabled=show_all)
    with col5:
        show_insuf = st.checkbox(f"INSUFFICIENT ({insuf})", value=False, key="filter_insuf", disabled=show_all)
    
    # Appliquer les filtres
    filtered_decisions = decisions.copy()
    
    if not show_all:
        filters = []
        if show_buy:
            filters.append('BUY')
        if show_hold:
            filters.append('HOLD')
        if show_sell:
            filters.append('SELL')
        if show_insuf:
            filters.append('INSUFFICIENT_DATA')
        
        if filters:
            filtered_decisions = decisions[decisions['Decision'].isin(filters)]
        else:
            filtered_decisions = pd.DataFrame()  # Aucun filtre = table vide
    
    st.caption(f"Affichage : {len(filtered_decisions)} / {total} titres")
    
    # Tableau
    if len(filtered_decisions) > 0:
        display_df = prepare_display_table(filtered_decisions)
        styled_df = style_decisions_table(display_df)
        
        st.dataframe(styled_df, use_container_width=True, height=400, hide_index=True)
    else:
        st.info("Aucun titre ne correspond aux filtres sélectionnés.")
    
    st.divider()
    
    # Actions
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sélection d'une société pour détails
        if len(filtered_decisions) > 0:
            company = st.selectbox(
                "Voir les détails d'une société",
                options=[""] + list(filtered_decisions['Company'].unique()),
                key="company_select"
            )
            if company:
                render_company_details(company, decisions)
    
    with col2:
        # Export CSV
        csv_data = decisions.to_csv(index=False).encode('utf-8')
        st.download_button(
            "💾 Exporter en CSV",
            data=csv_data,
            file_name="recommandations_dss.csv",
            mime="text/csv",
            use_container_width=True
        )


def prepare_display_table(decisions_df: pd.DataFrame) -> pd.DataFrame:
    """Prépare le tableau d'affichage avec colonnes essentielles."""
    display = decisions_df.copy()
    
    # Simplifier INSUFFICIENT_DATA
    display['Decision'] = display['Decision'].replace('INSUFFICIENT_DATA', 'INSUFFICIENT')
    
    # Colonnes essentielles
    cols = ['Company', 'Overall_Score', 'Confidence', 'Decision']
    display = display[cols].copy()
    display.columns = ['Société', 'Score Global', 'Confiance (%)', 'Décision']
    
    # Formatage
    display['Score Global'] = display['Score Global'].round(1)
    display['Confiance (%)'] = display['Confiance (%)'].round(0).astype(int)
    
    # Tri par Score décroissant
    display = display.sort_values('Score Global', ascending=False)
    
    return display


def style_decisions_table(df: pd.DataFrame):
    """Applique les couleurs institutionnelles au tableau."""
    def color_decision(val):
        if val == 'BUY':
            return 'background-color: #D1FAE5; color: #065F46; font-weight: 600;'
        elif val == 'SELL':
            return 'background-color: #FEE2E2; color: #991B1B; font-weight: 600;'
        elif val == 'HOLD':
            return 'background-color: #FEF3C7; color: #92400E; font-weight: 600;'
        else:  # INSUFFICIENT
            return 'background-color: #F3F4F6; color: #4B5563; font-weight: 600;'
    
    def color_score(val):
        """Gradient pour le score : rouge → jaune → vert."""
        if pd.isna(val):
            return ''
        if val >= 70:
            return 'background-color: #D1FAE5; color: #065F46;'
        elif val >= 50:
            return 'background-color: #FEF3C7; color: #92400E;'
        else:
            return 'background-color: #FEE2E2; color: #991B1B;'
    
    def color_confidence(val):
        """Gradient pour la confiance."""
        if pd.isna(val):
            return ''
        if val >= 70:
            return 'background-color: #D1FAE5; color: #065F46;'
        elif val >= 50:
            return 'background-color: #FEF3C7; color: #92400E;'
        else:
            return 'background-color: #FEE2E2; color: #991B1B;'
    
    styled = df.style.map(color_decision, subset=['Décision']) \
                     .map(color_score, subset=['Score Global']) \
                     .map(color_confidence, subset=['Confiance (%)'])
    
    return styled


def render_company_details(company: str, decisions_df: pd.DataFrame):
    """Affiche les détails d'une société sélectionnée."""
    row = decisions_df[decisions_df['Company'] == company].iloc[0]
    
    decision = row['Decision']
    if decision == 'INSUFFICIENT_DATA':
        decision = 'INSUFFICIENT'
    
    st.markdown(f"### 📊 Détails : **{company}**")
    
    # Métriques principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        decision_color = {
            'BUY': '🟢',
            'HOLD': '🟡',
            'SELL': '🔴',
            'INSUFFICIENT': '⚪'
        }.get(decision, '')
        st.metric("Décision", f"{decision_color} {decision}")
    
    with col2:
        score = row.get('Overall_Score', 0)
        st.metric("Score Global", f"{score:.1f} / 100")
    
    with col3:
        conf = row.get('Confidence', 0)
        st.metric("Confiance", f"{conf:.0f} %")
    
    # Signaux détaillés
    with st.expander("📋 Signaux Techniques"):
        signals = row.get('Signals', '')
        if pd.notna(signals) and signals and signals != 'no valid signals':
            for sig in str(signals).split(' | '):
                st.write(f"• {sig}")
        else:
            st.info("Aucun signal valide disponible")
    
    # Informations supplémentaires
    with st.expander("ℹ️ Informations Complémentaires"):
        info_cols = st.columns(2)
        
        with info_cols[0]:
            if 'Cours' in row.index and pd.notna(row['Cours']):
                st.write(f"**Dernier cours :** {row['Cours']:.2f} MAD")
            if 'Date' in row.index and pd.notna(row['Date']):
                st.write(f"**Date :** {row['Date']}")
        
        with info_cols[1]:
            if 'Data_Coverage' in row.index and pd.notna(row['Data_Coverage']):
                st.write(f"**Couverture données :** {row['Data_Coverage']}")
            if 'Free_Float' in row.index and pd.notna(row['Free_Float']):
                st.write(f"**Free Float :** {row['Free_Float']:.1%}")


def render_progress():
    """Affiche la progression de l'analyse en français."""
    steps = [
        ("✓", "Données importées"),
        ("✓", "Normalisation"),
        ("●", "Contrôle qualité"),
        ("●", "Métriques de marché"),
        ("●", "Filtrage dynamique"),
        ("○", "Indicateurs techniques"),
        ("○", "Signaux"),
        ("○", "Scoring"),
        ("○", "Décision")
    ]
    
    current = st.session_state.get('analysis_step', 0)
    
    progress_text = ""
    for i, (symbol, label) in enumerate(steps):
        if i < current:
            progress_text += f"✅ {label}\n"
        elif i == current:
            progress_text += f"⏳ **{label}** (en cours)\n"
        else:
            progress_text += f"⏸️ {label}\n"
    
    st.markdown(progress_text)


def import_market_data(uploaded_file):
    """Import et validation des données marché."""
    with st.spinner("⏳ Import des données marché en cours..."):
        try:
            # Fichier temporaire
            suffix = '.xlsx' if uploaded_file.name.endswith('.xlsx') else '.xls'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='wb') as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name
            
            # Pipeline
            pipeline = st.session_state['pipeline']
            unified, report = pipeline.ingest_market_data(temp_path)
            
            # Validation
            from src.validation import validate_dataset
            valid, val_report = validate_dataset(unified, verbose=False)
            
            if not valid:
                st.warning("⚠️ Données importées mais des problèmes de qualité ont été détectés.")
            
            # Stockage
            st.session_state['unified_data'] = unified
            st.session_state['ingest_report'] = report
            st.session_state['market_imported'] = True
            st.session_state['market_file_name'] = uploaded_file.name
            
            # Sauvegarde
            save_session_state()
            
            # Nettoyage
            Path(temp_path).unlink(missing_ok=True)
            
            # Message de succès avec détails
            n_companies = unified['Company'].nunique()
            n_records = len(unified)
            date_min = unified['Date'].min() if 'Date' in unified.columns else 'N/A'
            date_max = unified['Date'].max() if 'Date' in unified.columns else 'N/A'
            
            st.success(f"✅ Données marché importées : **{n_companies} sociétés**, **{n_records:,} observations**")
            st.info(f"📅 Période couverte : {date_min} → {date_max}")
            
            # Diagnostic: Afficher quelques exemples
            with st.expander("📊 Aperçu des données importées"):
                st.write(f"**Colonnes disponibles :** {', '.join(unified.columns.tolist())}")
                st.write(f"**Sociétés :** {', '.join(unified['Company'].unique()[:5].tolist())}{'...' if n_companies > 5 else ''}")
                st.dataframe(unified.head(10), use_container_width=True)
            
            st.rerun()
            
        except Exception as e:
            # Logger l'erreur technique pour les développeurs
            incident_id = str(uuid.uuid4())[:8]
            logger.error(f"[{incident_id}] Erreur import données marché: {str(e)}", exc_info=True)
            
            # Message simple pour le gestionnaire
            st.error("❌ **Format de fichier inattendu**")
            st.warning("⚠️ Veuillez vérifier que le fichier des **données marché** contient les colonnes attendues (Date, CODE_ISIN, Cours, Volume, etc.)")
            st.info(f"🆔 Référence incident : `{incident_id}`")


def import_composition_data(uploaded_file):
    """Import de la composition des indices."""
    with st.spinner("⏳ Import de la composition des indices en cours..."):
        try:
            # Fichier temporaire
            suffix = '.xlsx' if uploaded_file.name.endswith('.xlsx') else '.xls'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='wb') as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name
            
            # Pipeline
            pipeline = st.session_state['pipeline']
            comp_df, report = pipeline.ingest_index_composition(temp_path)
            
            # Stockage
            st.session_state['composition_data'] = comp_df
            st.session_state['composition_report'] = report
            st.session_state['index_imported'] = True
            st.session_state['index_file_name'] = uploaded_file.name
            
            # Sauvegarde
            save_session_state()
            
            # Nettoyage
            Path(temp_path).unlink(missing_ok=True)
            
            # Message de succès avec détails
            n_indices = comp_df['Index'].nunique() if 'Index' in comp_df.columns else 'N/A'
            n_securities = len(comp_df)
            
            st.success(f"✅ Composition importée : **{n_securities} titres**, **{n_indices} indices**")
            
            # Diagnostic: Afficher détails
            with st.expander("📊 Aperçu de la composition"):
                st.write(f"**Colonnes disponibles :** {', '.join(comp_df.columns.tolist())}")
                if 'Index' in comp_df.columns:
                    indices = comp_df['Index'].value_counts()
                    st.write("**Répartition par indice :**")
                    for idx, count in indices.items():
                        st.write(f"  - {idx}: {count} titres")
                st.dataframe(comp_df.head(10), use_container_width=True)
            
            st.rerun()
            
        except Exception as e:
            # Logger l'erreur technique pour les développeurs
            incident_id = str(uuid.uuid4())[:8]
            logger.error(f"[{incident_id}] Erreur import composition d'indice: {str(e)}", exc_info=True)
            
            # Message simple pour le gestionnaire
            st.error("❌ **Format de fichier inattendu**")
            st.warning("⚠️ Veuillez vérifier que le fichier de **composition d'indice** contient les colonnes attendues :")
            st.markdown("""
            - **Indice** (nom de l'indice : MASI, MASI 20, etc.)
            - **Code ISIN** (identifiant unique des titres)
            - **Facteur flottant** (free float)
            - **Capitalisation flottante** (en MAD)
            - **Poids** (pondération dans l'indice)
            """)
            st.info(f"🆔 Référence incident : `{incident_id}`")


def run_analysis():
    """Exécution du pipeline d'analyse complet."""
    st.session_state['analysis_in_progress'] = True
    st.session_state['analysis_step'] = 0
    
    try:
        pipeline = st.session_state['pipeline']
        market_df = st.session_state['unified_data']
        comp_df = st.session_state['composition_data']
        
        # Progress bar
        progress = st.progress(0, text="Initialisation...")
        
        # Étape 1: Normalisation (déjà faite à l'import)
        st.session_state['analysis_step'] = 1
        progress.progress(10, text="✓ Normalisation terminée")
        
        # Étape 2: Contrôle qualité
        st.session_state['analysis_step'] = 2
        progress.progress(20, text="⏳ Contrôle qualité temporelle en cours...")
        unified_clean, quality_report = pipeline.apply_quality_filter(market_df)
        n_after_quality = len(unified_clean['Company'].unique()) if len(unified_clean) > 0 else 0
        progress.progress(30, text=f"✓ Contrôle qualité terminé ({n_after_quality} titres)")
        
        # Logger détails qualité pour diagnostic
        logger.info(f"Contrôle qualité - Titres avant: {market_df['CODE_ISIN'].nunique()}, après: {n_after_quality}")
        logger.info(f"Quality report: {quality_report}")
        
        # Diagnostic: Vérifier si des données restent
        if len(unified_clean) == 0:
            removed = quality_report.get('removed_companies', [])
            max_gap = quality_report.get('max_gap_days', 7)
            
            raise ValueError(
                f"❌ Aucun titre n'a passé le contrôle qualité temporelle.\n\n"
                f"Titres rejetés: {len(removed)}\n"
                f"Critère: Continuité temporelle (gap entre observations ≤ {max_gap} jours)\n\n"
                f"Solutions possibles:\n"
                f"- Vérifier qu'il n'y a pas de trous > 7 jours dans les données\n"
                f"- Uploader des données avec meilleure continuité temporelle\n"
                f"- Les données peuvent être courtes (30 obs OK) mais doivent être continues"
            )
        
        # Étape 3: Métriques
        st.session_state['analysis_step'] = 3
        progress.progress(40, text="⏳ Calcul des métriques de marché...")
        # Les métriques sont calculées dans apply_dynamic_filter
        
        # Étape 4: Filtrage dynamique
        st.session_state['analysis_step'] = 4
        progress.progress(50, text="⏳ Filtrage dynamique de l'univers investissable...")
        investable, filter_report = pipeline.apply_dynamic_filter(unified_clean, comp_df)
        n_investable = len(investable['Company'].unique()) if len(investable) > 0 else 0
        progress.progress(60, text=f"✓ Filtrage dynamique terminé ({n_investable} titres investissables)")
        
        # Diagnostic: Vérifier si l'univers investissable est vide
        if len(investable) == 0:
            raise ValueError(
                f"❌ Aucun titre n'a passé le filtrage dynamique.\n\n"
                f"Raisons possibles:\n"
                f"- Free Float < 20% pour tous les titres\n"
                f"- Aucun titre dans les indices de référence (MASI recommandé)\n"
                f"- Données de marché insuffisantes (MIN_CONSECUTIVE={quality_report.get('min_consecutive', 14)})\n\n"
                f"Sociétés après qualité: {n_after_quality}\n"
                f"Vérifiez les fichiers Excel importés."
            )
        
        # Étape 5: Indicateurs techniques
        st.session_state['analysis_step'] = 5
        progress.progress(65, text="⏳ Calcul des indicateurs techniques (7 familles)...")
        indicators, _ = pipeline.compute_indicators(investable)
        progress.progress(75, text="✓ Indicateurs techniques calculés")
        
        # Étape 6: Signaux et Scores
        st.session_state['analysis_step'] = 6
        progress.progress(80, text="⏳ Génération des signaux et scoring...")
        signals, _ = pipeline.compute_signals_and_scores(indicators)
        progress.progress(90, text="✓ Signaux et scores calculés")
        
        # Étape 7: Décisions finales
        st.session_state['analysis_step'] = 7
        progress.progress(95, text="⏳ Génération des décisions finales...")
        decisions, summary, _ = pipeline.make_decisions(signals)
        progress.progress(100, text="✅ Analyse terminée")
        
        # Stockage des résultats
        st.session_state['decisions_summary'] = summary
        st.session_state['pipeline_results'] = {
            'decisions': decisions,
            'signals': signals,
            'indicators': indicators
        }
        st.session_state['pipeline_complete'] = True
        st.session_state['analysis_in_progress'] = False
        
        # Sauvegarde
        save_session_state()
        
        # Stats finales
        buy = (summary['Decision'] == 'BUY').sum()
        hold = (summary['Decision'] == 'HOLD').sum()
        sell = (summary['Decision'] == 'SELL').sum()
        
        st.success(f"✅ **Analyse terminée** : {len(summary)} titres analysés - {buy} BUY, {hold} HOLD, {sell} SELL")
        st.balloons()
        st.rerun()
        
    except Exception as e:
        # Logger l'erreur technique pour les développeurs
        incident_id = str(uuid.uuid4())[:8]
        logger.error(f"[{incident_id}] Erreur lors de l'analyse: {str(e)}", exc_info=True)
        
        # Message simple pour le gestionnaire
        st.error("❌ **Erreur lors de l'analyse du portefeuille**")
        st.warning("⚠️ Les données importées ne permettent pas de générer des recommandations. Veuillez vérifier :")
        st.markdown("""
        - Les **données marché** sont complètes (Date, CODE_ISIN, Cours, Volume)
        - La **composition d'indice** correspond aux titres du marché
        - La période couverte est suffisante (minimum 50 observations consécutives requises)
        """)
        st.info(f"🆔 Référence incident : `{incident_id}`")
        
        st.session_state['analysis_in_progress'] = False
        st.session_state['analysis_step'] = None


def render_footer():
    """Footer professionnel CMR."""
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; color: #6C757D; font-size: 0.9rem; padding: 1rem 0;'>
            <p style='margin: 0.5rem 0;'>
                <strong>DSS Gestion Portefeuille</strong> - Version 2.1
            </p>
            <p style='margin: 0.5rem 0;'>
                © 2026 Caisse Marocaine des Retraites - Pôle Gestion de Portefeuille
            </p>
            <p style='margin: 0.5rem 0; font-size: 0.85rem;'>
                Système d'aide à la décision pour l'analyse technique et fondamentale
            </p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Point d'entrée principal de l'application."""
    # Charger CSS
    load_css()
    
    # Initialiser
    init_app()
    
    # Rendu des sections
    render_header()
    render_import_section()
    render_analysis_section()
    render_recommendations_section()
    render_footer()


if __name__ == "__main__":
    main()
