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
                indices = comp_data['Indice'].nunique() if 'Indice' in comp_data.columns else 'N/A'
                st.success(f"✓ {filename}")
                st.caption(f"📋 {n_securities} titres · {indices} indices")
    
    # Statut global + Sélection critères si composition importée
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
    
    # Section de sélection des critères (si composition importée)
    if comp_ok:
        render_filter_criteria_section()




def render_filter_criteria_section():
    """
    Section 1.5: Sélection des Critères de Filtrage Dynamique
    Le gestionnaire choisit l'indice cible et les seuils sans toucher au code.
    """
    st.divider()
    st.subheader("⚙️ Configurer les Critères de Filtrage")
    
    # Récupérer les données de composition pour extraire les indices disponibles
    comp_data = st.session_state.get('composition_data_full')  # On garde TOUTES les données
    
    if comp_data is None or comp_data.empty:
        st.info("📋 Importez d'abord un fichier de composition pour configurer les critères.")
        return
    
    # Indices supportés (décision encadrant : uniquement MASI et MASI 20)
    from config.methodology import FILTER_CONFIG
    from src.parsers.composition_parser import normalize_index_name

    supported = FILTER_CONFIG.get('supported_indices', ['MASI', 'MASI 20'])
    top_n_masi = int(FILTER_CONFIG.get('masi_top_n_by_weight', 40))
    norm_supported = {normalize_index_name(s): s for s in supported}

    if 'Indice' not in comp_data.columns:
        st.error("❌ Colonne 'Indice' introuvable dans les données de composition.")
        return

    # Ne conserver que les indices supportés réellement présents dans le fichier
    present = []
    for idx in comp_data['Indice'].unique():
        if normalize_index_name(idx) in norm_supported and idx not in present:
            present.append(idx)
    available_indices = sorted(present)

    if not available_indices:
        st.warning("⚠️ Le fichier importé ne contient ni **MASI** ni **MASI 20**. "
                   "Ces deux indices sont les seuls pris en charge.")
        return

    st.markdown(
        "Choisissez l'**indice de référence**. La règle de sélection de l'univers "
        "investissable est appliquée automatiquement :"
    )
    st.markdown(
        f"- **MASI** → les **{top_n_masi} premières** sociétés par **poids flottant**\n"
        f"- **MASI 20** → **tous** les titres de l'indice"
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        default_index = st.session_state.get('selected_index', 'MASI 20')
        if default_index not in available_indices:
            default_index = available_indices[0]

        selected_index = st.selectbox(
            "🎯 Indice de référence",
            options=available_indices,
            index=available_indices.index(default_index),
            key="filter_index_select",
            help="Seuls MASI et MASI 20 sont pris en charge."
        )

    # Déterminer la règle et l'aperçu du nombre de titres retenus
    idx_rows = comp_data[comp_data['Indice'].apply(normalize_index_name) == normalize_index_name(selected_index)].copy()
    n_in_index = len(idx_rows)

    if normalize_index_name(selected_index) == normalize_index_name('MASI'):
        n_selected = min(top_n_masi, n_in_index)
        rule_txt = f"MASI → **{n_selected}** premières sociétés par poids flottant (sur {n_in_index})"
    else:
        n_selected = n_in_index
        rule_txt = f"MASI 20 → **tous** les titres ({n_in_index})"

    with col2:
        st.markdown("**📋 Règle appliquée**")
        st.caption(rule_txt)
        st.caption(f"→ {n_selected} titres sélectionnés dans l'indice (avant jointure marché)")

    st.divider()

    # Bouton d'application
    b1, b2, b3 = st.columns([2, 1, 2])
    with b2:
        if st.button("✅ Appliquer", use_container_width=True, type="primary"):
            st.session_state['selected_index'] = selected_index
            st.session_state['criteria_applied'] = True
            # Composition filtrée sur l'indice choisi (la sélection top-N se fait au pipeline)
            st.session_state['composition_data'] = idx_rows
            st.success(f"✅ Indice appliqué : {selected_index} — {rule_txt}")
            st.rerun()

    # Critères actifs
    if st.session_state.get('criteria_applied', False):
        active_index = st.session_state.get('selected_index', 'N/A')
        if normalize_index_name(active_index) == normalize_index_name('MASI'):
            active_rule = f"{top_n_masi} premières par poids flottant"
        else:
            active_rule = "tous les titres de l'indice"
        st.info(f"**📋 Critère actif :** Indice **{active_index}** — {active_rule}.")


def render_traceability_section():
    """
    Page Traçabilité — restitution concise et business-oriented :
      • Market Data : sociétés, observations, période.
      • Composition : indice sélectionné, règle appliquée, table paginée (poids flottant).
      • Jointure : retenus / rejetés + raison principale.
    Aucune logique métier : lecture des sorties du pipeline (filter_report, trace, session).
    """
    from src.parsers.composition_parser import normalize_index_name

    st.markdown("### 🔎 Traçabilité de l'analyse")

    unified = st.session_state.get('unified_data')
    comp_data = st.session_state.get('composition_data')
    filter_report = st.session_state.get('filter_report', {}) or {}
    stats = st.session_state.get('intersection_stats', {}) or {}
    trace_df = st.session_state.get('analysis_trace')
    summary = st.session_state.get('decisions_summary')

    # ── Dérivations ROBUSTES (survivent à un rechargement de session) ──
    # Indice : filter_report → session → déduit de la composition
    selected_index = st.session_state.get('selected_index') or filter_report.get('index')
    if (not selected_index or str(selected_index) in ('N/A', 'None')) and comp_data is not None and 'Indice' in comp_data.columns:
        uq = [str(x) for x in comp_data['Indice'].dropna().unique()]
        selected_index = uq[0] if len(uq) == 1 else (", ".join(uq) if uq else 'N/A')
    selected_index = selected_index or 'N/A'

    # Sociétés retenues : decisions_summary (restauré) fait foi, sinon rapports
    if summary is not None and len(summary):
        retained_count = summary['CODE_ISIN'].nunique() if 'CODE_ISIN' in summary.columns else len(summary)
    else:
        retained_count = stats.get('after_gates', filter_report.get('output_companies', 0)) or 0

    n_dispo = len(comp_data) if comp_data is not None else 0
    selected_n = filter_report.get('selected_companies')  # peut être None après reload

    # ── Cartes de synthèse ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**📥 Données marché**")
        if unified is not None and len(unified):
            st.metric("Sociétés détectées", unified['CODE_ISIN'].nunique())
            st.caption(f"{len(unified):,} observations")
            if 'Date' in unified.columns and unified['Date'].notna().any():
                st.caption(f"Période : {unified['Date'].min().date()} → {unified['Date'].max().date()}")
        else:
            st.caption("—")
    with c2:
        st.markdown("**🎯 Composition / Indice**")
        st.metric(f"Indice : {selected_index}", n_dispo)
        st.caption("Sociétés disponibles dans l'indice")
        rule = filter_report.get('selection_rule')
        if rule:
            st.caption(f"Règle : {rule}")
    with c3:
        st.markdown("**🔗 Jointure marché × indice**")
        st.metric("Sociétés retenues", retained_count)
        if selected_n:
            st.caption(f"Sélectionnées dans l'indice : {selected_n}")
        st.caption("Rejet possible : titre de l'indice sans données marché, ou hors sélection.")

    # Ensembles pour motifs exacts (fallback sur decisions_summary si trace absente après reload)
    if trace_df is not None and len(trace_df):
        retained_isins = set(trace_df['CODE_ISIN'])
    elif summary is not None and 'CODE_ISIN' in summary.columns:
        retained_isins = set(summary['CODE_ISIN'])
    else:
        retained_isins = set()
    market_raw = st.session_state.get('market_isins_raw', set())
    market_quality = st.session_state.get('market_isins_quality', set())

    def _reason(isin: str) -> str:
        """Motif exact pour une société sélectionnée mais non retenue."""
        if isin in retained_isins:
            return ""
        if market_raw and isin not in market_raw:
            return "Absente du fichier marché (aucun historique de prix pour cet ISIN)"
        if market_quality and isin not in market_quality:
            return "Écartée au contrôle qualité (aucun cours valide)"
        return "Écartée au filtrage / données insuffisantes"

    # ── Table Composition : sociétés de l'indice triées par poids flottant ──
    if comp_data is not None and 'Weight' in comp_data.columns and len(comp_data):
        st.markdown("##### 🏦 Composition de l'indice (triée par poids flottant)")
        selected_n = int(filter_report.get('selected_companies', len(comp_data)) or len(comp_data))

        comp_sorted = comp_data.sort_values('Weight', ascending=False).reset_index(drop=True)
        rows = []
        for i, r in comp_sorted.iterrows():
            selected = i < selected_n  # top-N (MASI) ou tous (MASI 20)
            isin = r.get('CODE_ISIN', '')
            if not selected:
                statut = "⊗ Hors sélection (poids flottant)"
            elif isin in retained_isins:
                statut = "✅ Retenue (analysée)"
            else:
                statut = "⚠️ " + _reason(isin)
            rows.append({
                "Rang": i + 1,
                "Société": r.get('Company', ''),
                "Code ISIN": isin,
                "Poids flottant": f"{float(r['Weight']) * 100:.2f}%" if pd.notna(r.get('Weight')) else "—",
                "Statut": statut,
            })
        comp_table = pd.DataFrame(rows)
        render_paginated_dataframe(comp_table, lambda d: d, page_size=10, key='trace_comp')

    # ── Table des rejets (sélectionnées mais non analysées) avec motif exact ──
    if comp_data is not None and 'Weight' in comp_data.columns:
        selected_n = int(filter_report.get('selected_companies', len(comp_data)) or len(comp_data))
        comp_sorted = comp_data.sort_values('Weight', ascending=False).reset_index(drop=True)
        selected_part = comp_sorted.head(selected_n)
        rejected_rows = [
            {
                "Société": r.get('Company', ''),
                "Code ISIN": r.get('CODE_ISIN', ''),
                "Poids flottant": f"{float(r['Weight']) * 100:.2f}%" if pd.notna(r.get('Weight')) else "—",
                "Raison": _reason(r.get('CODE_ISIN', '')),
            }
            for _, r in selected_part.iterrows()
            if r.get('CODE_ISIN', '') not in retained_isins
        ]
        if rejected_rows:
            with st.expander(f"⚠️ Sociétés rejetées ({len(rejected_rows)}) — sélectionnées mais non analysables"):
                render_paginated_dataframe(pd.DataFrame(rejected_rows), lambda d: d, page_size=10, key='trace_rej')


def render_intersection_breakdown():
    """
    (Conservé) Bilan détaillé de la jointure marché ∩ indice par ISIN.
    """
    stats = st.session_state.get('intersection_stats')
    if not stats:
        return

    with st.expander("🔎 Traçabilité du filtrage (marché ∩ indice)", expanded=True):
        st.markdown(
            f"Jointure par **code ISIN** entre les données marché et la composition de "
            f"l'indice **{stats['index_name']}**. Elle montre précisément d'où viennent "
            f"les titres analysés."
        )

        # Étape 1 : les deux ensembles de départ
        st.markdown("##### 1️⃣ Ensembles de départ")
        c1, c2 = st.columns(2)
        c1.metric("Sociétés marché exploitables", stats['market'],
                  help="Sociétés dont la série de cours est continue (contrôle qualité : aucun trou > 7 jours)")
        c2.metric(f"Titres de l'indice {stats['index_name']}", stats['index'],
                  help="Titres composant l'indice sélectionné dans le fichier de composition")

        # Étape 2 : résultat de la jointure
        st.markdown("##### 2️⃣ Résultat de la jointure par ISIN")
        c3, c4, c5 = st.columns(3)
        c3.metric("✅ Communs (analysables)", stats['kept'],
                  help="Présents dans le marché ET dans l'indice → seuls ceux-ci peuvent être analysés")
        c4.metric("⊗ Titres indice sans données marché", stats['index_absent_from_market'],
                  help="Dans l'indice mais absents du fichier marché → aucun cours/volume → non analysables")
        c5.metric("⊗ Sociétés marché hors indice", stats['market_outside_index'],
                  help="Ont des données marché mais n'appartiennent pas à l'indice choisi → écartées (Gate 1)")

        # Étape 3 : après les filtres d'investabilité
        st.markdown("##### 3️⃣ Après filtres d'investabilité")
        st.metric("Titres retenus (univers final)", stats['after_gates'],
                  help="Après Gate 2 (poids flottant) et Gate 3 (capitalisation flottante)")

        # Légende explicative
        st.divider()
        st.markdown("""
        **Comment lire ce bilan :**
        - **Sociétés marché exploitables** : issues du fichier marché, après *contrôle qualité*
          (on ne garde que les séries de cours continues, sans trou > 7 jours, car un indicateur
          calculé sur une série discontinue n'a pas de sens).
        - **Titres indice sans données marché** : présents dans l'indice choisi mais **absents du
          fichier marché** (aucun ISIN correspondant) → impossible de les analyser faute de cours.
        - **Communs (analysables)** = intersection des deux : c'est la base réellement analysable,
          ensuite affinée par les filtres poids flottant et capitalisation.
        """)

        if stats['kept'] == 0:
            st.warning(
                "⚠️ Aucun titre commun entre le marché et l'indice sélectionné. "
                "Vérifie que les codes ISIN correspondent et que l'indice choisi est cohérent "
                "avec les sociétés présentes dans le fichier marché."
            )


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
        st.warning("⏳ Analyse en cours, veuillez patienter...")
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
        
        # Bilan de transparence : d'où viennent les titres analysés
        render_traceability_section()
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


def _class_legend() -> str:
    """Légende dynamique symbole → intitulé (depuis la config, jamais codée en dur)."""
    from config.methodology import FLASH_MOMENTUM_CONFIG as C
    sym = dict(C.get('class_symbol_scale', []))            # {80:'+++', 60:'++', ...}
    bounds = sorted([b for b, _ in C.get('classification', [])], reverse=True)  # [80,60,40,0]
    labels = dict(C.get('classification', []))             # {80:'Très Fort', ...}
    parts = [f"{sym.get(b, '')} : {labels.get(b, '')}" for b in bounds]
    return "  ·  ".join(parts)


def _class_name_for_symbol(symbol: str) -> str:
    """Intitulé de classe correspondant à un symbole (pour info-bulle)."""
    from config.methodology import FLASH_MOMENTUM_CONFIG as C
    sym = dict(C.get('class_symbol_scale', []))
    labels = dict(C.get('classification', []))
    for b, s in sym.items():
        if s == symbol:
            return labels.get(b, '')
    return ''


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
    
    # Tableau (paginé si plus de 10 titres)
    if len(filtered_decisions) > 0:
        display_df = prepare_display_table(filtered_decisions)
        legend = _class_legend()
        col_cfg = {
            "Classe": st.column_config.TextColumn(
                "Classe",
                help="Symbole de la classe du score technique.\n\n" + legend,
            )
        }
        render_paginated_dataframe(display_df, style_decisions_table, page_size=10, key='rec',
                                   column_config=col_cfg)
        st.markdown(
            f"<div style='color:#4B5563; font-size:0.9rem; padding:0.3rem 0;'>"
            f"<strong>Légende — Classe :</strong>&nbsp; {legend}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Aucun titre ne correspond aux filtres sélectionnés.")
    
    st.divider()
    
    # Actions
    selected_company = ""
    col1, col2 = st.columns([2, 1])

    with col1:
        # Sélection d'une société pour détails
        if len(filtered_decisions) > 0:
            companies_sorted = sorted(
                filtered_decisions['Company'].dropna().unique().tolist(),
                key=lambda s: str(s).casefold()
            )
            selected_company = st.selectbox(
                "Voir les détails d'une société",
                options=[""] + companies_sorted,
                key="company_select"
            )

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

    # Détails de la société sélectionnée — affichage centré, pleine largeur
    if selected_company:
        st.divider()
        render_company_details(selected_company, decisions)


def render_paginated_dataframe(display_df: pd.DataFrame, styler_fn, page_size: int = 10, key: str = 'page', column_config=None):
    """
    Affiche un DataFrame avec pagination (page_size lignes par page).

    - Si le nombre de lignes ≤ page_size : affichage direct sans contrôles.
    - Sinon : navigation Précédent/Suivant + indicateur « Page x/y ».
    - Le styler_fn est appliqué uniquement à la tranche affichée (performance).

    Args:
        display_df: tableau déjà préparé pour l'affichage
        styler_fn: fonction retournant un Styler à partir d'un DataFrame
        page_size: nombre de lignes par page (défaut 10)
        key: préfixe unique pour l'état de pagination
    """
    total = len(display_df)

    # Pas de pagination nécessaire
    if total <= page_size:
        st.dataframe(styler_fn(display_df), use_container_width=True, hide_index=True,
                     column_config=column_config)
        return

    n_pages = (total + page_size - 1) // page_size
    page_key = f'{key}_page'

    # Initialiser / borner l'index de page (clamp si les filtres réduisent le total)
    current = st.session_state.get(page_key, 0)
    current = max(0, min(current, n_pages - 1))
    st.session_state[page_key] = current

    # Contrôles de navigation
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("◀ Précédent", key=f'{key}_prev', disabled=(current == 0), use_container_width=True):
            st.session_state[page_key] = current - 1
            st.rerun()
    with c3:
        if st.button("Suivant ▶", key=f'{key}_next', disabled=(current >= n_pages - 1), use_container_width=True):
            st.session_state[page_key] = current + 1
            st.rerun()
    with c2:
        start_disp = current * page_size + 1
        end_disp = min((current + 1) * page_size, total)
        st.markdown(
            f"<div style='text-align:center; padding-top:0.4rem; color:#4B5563;'>"
            f"Page <strong>{current + 1}</strong> / {n_pages} &nbsp;·&nbsp; "
            f"titres {start_disp}–{end_disp} sur {total}</div>",
            unsafe_allow_html=True
        )

    # Tranche courante
    start = current * page_size
    page_df = display_df.iloc[start:start + page_size]
    st.dataframe(styler_fn(page_df), use_container_width=True, hide_index=True,
                 column_config=column_config)


def prepare_display_table(decisions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare le tableau d'affichage aligné sur le moteur de décision.

    Colonne pilote = Score Technique (Flash Momentum, 0–100), qui pilote la décision.
    Overall_Score/Confidence restent disponibles dans le détail (vue analytique).
    """
    display = decisions_df.copy()

    # Simplifier INSUFFICIENT_DATA pour l'affichage
    display['Decision'] = display['Decision'].replace('INSUFFICIENT_DATA', 'INSUFFICIENT')

    # Garantir la présence des colonnes attendues (robustesse)
    for col in ['Technical_Score', 'Score_Class', 'Score_Symbol', 'Data_Coverage']:
        if col not in display.columns:
            display[col] = pd.NA

    # Classe = symbole seul (+++ / ++ / + / − / −−)
    def _classe_sym(row):
        sym = row.get('Score_Symbol', '')
        return sym if isinstance(sym, str) and sym else "—"
    display['_Classe'] = display.apply(_classe_sym, axis=1)

    cols = ['Company', 'Technical_Score', '_Classe', 'Data_Coverage', 'Decision']
    display = display[cols].copy()
    display.columns = ['Société', 'Score Technique', 'Classe', 'Couverture', 'Décision']

    # Formatage sûr (aucun cast int sur NaN)
    display['Score Technique'] = pd.to_numeric(display['Score Technique'], errors='coerce').round(1)

    # Tri par Score Technique décroissant (NaN en dernier)
    display = display.sort_values('Score Technique', ascending=False, na_position='last')

    return display


def style_decisions_table(df: pd.DataFrame):
    """Applique les couleurs institutionnelles au tableau (seuils alignés méthodologie)."""
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
        """Gradient aligné sur la classification : ≥60 vert, 40–59 ambre, <40 rouge."""
        if pd.isna(val):
            return 'color: #9CA3AF;'
        if val >= 60:
            return 'background-color: #D1FAE5; color: #065F46;'
        elif val >= 40:
            return 'background-color: #FEF3C7; color: #92400E;'
        else:
            return 'background-color: #FEE2E2; color: #991B1B;'

    styled = df.style.map(color_decision, subset=['Décision'])
    if 'Score Technique' in df.columns:
        styled = styled.map(color_score, subset=['Score Technique'])

    # Formatage du score sans casser les NaN
    styled = styled.format({'Score Technique': lambda v: '—' if pd.isna(v) else f'{v:.1f}'})

    return styled


def render_company_details(company: str, decisions_df: pd.DataFrame):
    """Affiche les détails d'une société sélectionnée (centré, orienté Flash Momentum)."""
    row = decisions_df[decisions_df['Company'] == company].iloc[0]

    decision = row['Decision']
    if decision == 'INSUFFICIENT_DATA':
        decision = 'INSUFFICIENT'

    def _fmt(value, suffix="", decimals=1):
        """Formatage sûr (évite l'affichage de 'nan')."""
        if value is None or pd.isna(value):
            return "N/A"
        return f"{value:.{decimals}f}{suffix}"

    # Affichage CENTRÉ : colonne centrale plus large, marges latérales
    _left, center, _right = st.columns([1, 4, 1])

    with center:
        st.markdown(
            f"<h3 style='text-align:center;'>📊 Détails : {company}</h3>",
            unsafe_allow_html=True
        )

        # ── Métriques principales (Flash Momentum) ──
        col1, col2, col3 = st.columns(3)
        with col1:
            decision_color = {'BUY': '🟢', 'HOLD': '🟡', 'SELL': '🔴', 'INSUFFICIENT': '⚪'}.get(decision, '')
            st.metric("Décision", f"{decision_color} {decision}")
        with col2:
            st.metric("Score Technique", f"{_fmt(row.get('Technical_Score', pd.NA))} / 100")
        with col3:
            _sym = row.get('Score_Symbol', '')
            _cls = row.get('Score_Class', '') or _class_name_for_symbol(_sym)
            st.metric(
                "Classe",
                _sym if isinstance(_sym, str) and _sym else "—",
                help=f"{_sym} = {_cls}" if _sym and _cls else None,
            )

        coverage = row.get('Data_Coverage', None)
        if coverage is not None and pd.notna(coverage):
            st.caption(f"📶 Couverture des données : **{coverage}**")

        st.divider()

        # ── Signaux Techniques = détail des points par pilier Flash Momentum ──
        st.markdown("##### 📋 Signaux Techniques — points par pilier (Flash Momentum)")

        pillars = [
            ("Volume (RVOL + OBV)", row.get('Flash_Vol_Score', pd.NA), 20),
            ("RSI (momentum)",      row.get('Flash_RSI_Score', pd.NA), 25),
            ("Moyennes mobiles",    row.get('Flash_MM_Score', pd.NA),  35),
            ("MACD",                row.get('Flash_MACD_Score', pd.NA), 20),
        ]
        pillar_df = pd.DataFrame([
            {
                "Pilier": name,
                "Points": "—" if pd.isna(val) else f"{int(round(val))} / {maxp}",
            }
            for name, val, maxp in pillars
        ])
        st.dataframe(pillar_df, use_container_width=True, hide_index=True)

        total = row.get('Technical_Score', pd.NA)
        st.markdown(f"**Score technique total : {_fmt(total)} / 100** — *{row.get('Score_Class', 'N/A')}*")
        if pd.notna(total):
            st.progress(min(1.0, max(0.0, float(total) / 100.0)))

        # Traçabilité OBV / Golden Cross (contexte des piliers)
        obv = row.get('OBV_Trend', None)
        gc = row.get('Golden_Cross_Recent', False)
        traces = []
        if obv in ('rising', 'neutral', 'falling'):
            traces.append({'rising': 'OBV en hausse', 'neutral': 'OBV neutre', 'falling': 'OBV en baisse'}[obv])
        if bool(gc):
            traces.append("Golden Cross récent (MM50 > MM200)")
        if traces:
            st.caption("🔎 " + " · ".join(traces))

        st.divider()

        # ── Couverture des indicateurs + détail indicateur-par-indicateur (via la trace) ──
        trace_df = st.session_state.get('analysis_trace')
        trow = None
        if trace_df is not None and len(trace_df):
            match = trace_df[trace_df['Company'] == company]
            if len(match):
                trow = match.iloc[0]

        if trow is not None:
            from src.traceability import company_indicator_table, indicator_coverage
            from config.methodology import FLASH_MOMENTUM_CONFIG

            n_ok, n_tot, missing = indicator_coverage(trow, FLASH_MOMENTUM_CONFIG)
            pct = (n_ok / n_tot * 100) if n_tot else 0.0

            st.markdown("##### 🧪 Couverture des indicateurs")
            cova, covb = st.columns([1, 2])
            with cova:
                st.metric("Indicateurs calculés", f"{n_ok} / {n_tot}")
                st.caption(f"Couverture : {pct:.0f} %")
            with covb:
                if missing:
                    st.warning("Indisponibles : " + ", ".join(missing))
                else:
                    st.success("Tous les indicateurs attendus sont calculés.")

            st.markdown("##### 🧾 Détail des indicateurs")
            ind_table = pd.DataFrame(company_indicator_table(trow))
            st.dataframe(ind_table, use_container_width=True, hide_index=True)

        st.divider()

        # ── Informations complémentaires ──
        st.markdown("##### ℹ️ Informations complémentaires")
        info1, info2 = st.columns(2)
        with info1:
            n_ok = row.get('Indicators_Computed', None)
            n_tot = row.get('Indicators_Total', None)
            if n_ok is not None and n_tot:
                st.write(f"**Indicateurs calculés :** {int(n_ok)} / {int(n_tot)}")
                st.caption("Indicateurs du score Flash Momentum : RVOL, OBV, RSI-14, "
                           "SMA-20/50/200, MACD, MACD-Signal.")
            if 'Cours' in row.index and pd.notna(row['Cours']):
                st.write(f"**Dernier cours :** {row['Cours']:.2f} MAD")
        with info2:
            first_d = row.get('First_Price_Date', None)
            last_d = row.get('Last_Price_Date', None)
            n_sess = row.get('N_Sessions', None)
            if first_d not in (None, 'N/A'):
                st.write(f"**1ère séance analysée :** {first_d}")
            if last_d not in (None, 'N/A'):
                st.write(f"**Dernière séance :** {last_d}")
            if n_sess is not None:
                st.write(f"**Nombre de séances :** {int(n_sess)}")


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


def _valider_extension_excel(uploaded_file) -> bool:
    """Vérifie que le fichier a une extension Excel valide (.xlsx / .xls)."""
    name = (uploaded_file.name or '').lower()
    if not name.endswith(('.xlsx', '.xls')):
        st.error("❌ **Format de fichier non supporté**")
        st.warning("⚠️ Seuls les fichiers Excel (**.xlsx** ou **.xls**) sont acceptés. "
                   f"Fichier reçu : `{uploaded_file.name}`")
        return False
    return True


def import_market_data(uploaded_file):
    """Import et validation des données marché."""
    # Validation de l'extension avant tout traitement
    if not _valider_extension_excel(uploaded_file):
        return
    _big = len(uploaded_file.getvalue()) > 1_000_000  # > ~1 Mo → gros fichier
    _spin = ("⏳ Importation en cours… Le fichier contient beaucoup de données et son "
             "traitement peut prendre quelques instants. Veuillez patienter."
             if _big else "⏳ Import des données marché en cours...")
    with st.spinner(_spin):
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
            
            # ── Métadonnées d'import (transparence pour le gestionnaire) ──
            n_companies = unified['CODE_ISIN'].nunique()
            n_records = len(unified)
            n_dates = unified['Date'].nunique() if 'Date' in unified.columns else 0
            date_min = unified['Date'].min() if 'Date' in unified.columns else 'N/A'
            date_max = unified['Date'].max() if 'Date' in unified.columns else 'N/A'
            included = [s['canonical_variable'] or s['name'] for s in report.get('sheets_included', [])]
            excluded = [(s['name'], s.get('reason', '')) for s in report.get('sheets_excluded', [])]
            
            st.success(
                f"✅ **Données marché importées** — "
                f"{n_companies} sociétés · {n_records:,} observations · {n_dates} séances"
            )
            
            # Cartes de métadonnées
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Sociétés", n_companies)
            m2.metric("Observations", f"{n_records:,}")
            m3.metric("Séances", n_dates)
            m4.metric("Feuilles retenues", len(included))
            
            with st.expander("📊 Détails de l'import marché"):
                # Période couverte
                st.markdown("##### 📅 Période couverte")
                dmin = date_min.date() if hasattr(date_min, 'date') else date_min
                dmax = date_max.date() if hasattr(date_max, 'date') else date_max
                st.caption(f"Du **{dmin}** au **{dmax}** · {n_dates} séances")

                # Feuilles (retenues + écartées) sous forme de tableau
                st.markdown("##### 🗂️ Feuilles du classeur")
                sheet_rows = [{'Feuille': v, 'Statut': '✅ Retenue', 'Détail': 'Variable marché'} for v in included]
                sheet_rows += [{'Feuille': name, 'Statut': '⊗ Écartée', 'Détail': reason} for name, reason in excluded]
                st.dataframe(
                    pd.DataFrame(sheet_rows),
                    use_container_width=True, hide_index=True
                )

                # Colonnes
                st.markdown("##### 🧾 Colonnes disponibles")
                st.caption(', '.join(unified.columns.tolist()))

                # Aperçu des données
                st.markdown("##### 🔍 Aperçu des données (10 lignes)")
                st.dataframe(unified.head(10), use_container_width=True, hide_index=True)
            
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
    """Import de la composition des indices (version full - sans filtrage préalable)."""
    # Validation de l'extension avant tout traitement
    if not _valider_extension_excel(uploaded_file):
        return
    _big = len(uploaded_file.getvalue()) > 1_000_000  # > ~1 Mo → gros fichier
    _spin = ("⏳ Importation en cours… Le fichier contient beaucoup de données et son "
             "traitement peut prendre quelques instants. Veuillez patienter."
             if _big else "⏳ Import de la composition des indices en cours...")
    with st.spinner(_spin):
        try:
            # Fichier temporaire
            suffix = '.xlsx' if uploaded_file.name.endswith('.xlsx') else '.xls'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='wb') as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name
            
            # Pipeline - charger TOUS les indices (pas de filtrage)
            pipeline = st.session_state['pipeline']
            from src.parsers.composition_parser import parse_composition_file
            
            comp_df_full, report = parse_composition_file(
                temp_path,
                index_name=None,  # Charger TOUS les indices
                validate=True
            )
            
            # Stockage - garder TOUTES les données
            st.session_state['composition_data_full'] = comp_df_full  # NOUVEAU : toutes les données
            st.session_state['composition_report'] = report
            st.session_state['index_imported'] = True
            st.session_state['index_file_name'] = uploaded_file.name
            
            # Par défaut, sélectionner MASI 20 si disponible
            available_indices = comp_df_full['Indice'].unique().tolist() if 'Indice' in comp_df_full.columns else []
            default_index = 'MASI 20' if 'MASI 20' in available_indices else (available_indices[0] if available_indices else None)
            
            if default_index:
                from src.parsers.composition_parser import normalize_index_name
                comp_df_filtered = comp_df_full[
                    comp_df_full['Indice'].apply(normalize_index_name) == normalize_index_name(default_index)
                ].copy()
                st.session_state['composition_data'] = comp_df_filtered
                st.session_state['selected_index'] = default_index
            
            # Sauvegarde
            save_session_state()
            
            # Nettoyage
            Path(temp_path).unlink(missing_ok=True)
            
            # ── Métadonnées d'import (transparence pour le gestionnaire) ──
            n_indices = len(available_indices)
            n_observations = len(comp_df_full)
            n_societes = comp_df_full['CODE_ISIN'].nunique() if 'CODE_ISIN' in comp_df_full.columns else n_observations
            n_feuilles = len(report.get('sheets_processed', []))
            
            st.success(
                f"✅ **Composition importée** — "
                f"{n_observations} observations · {n_societes} sociétés · {n_indices} indices"
            )
            
            # Cartes de métadonnées
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Observations", f"{n_observations:,}")
            c2.metric("Sociétés (ISIN)", n_societes)
            c3.metric("Indices", n_indices)
            c4.metric("Feuilles lues", n_feuilles)
            
            with st.expander("📊 Détails de l'import composition"):
                # Répartition par indice sous forme de tableau
                st.markdown("##### 🎯 Répartition par indice")
                rep_df = pd.DataFrame([
                    {'Indice': idx, 'Titres': int((comp_df_full['Indice'] == idx).sum())}
                    for idx in available_indices
                ]).sort_values('Titres', ascending=False)
                st.dataframe(rep_df, use_container_width=True, hide_index=True)

                # Feuilles ignorées (le cas échéant)
                skipped = report.get('sheets_skipped', [])
                if skipped:
                    st.markdown("##### ⚠️ Feuilles ignorées")
                    st.dataframe(
                        pd.DataFrame([
                            {'Feuille': s['sheet'], 'Raison': s.get('reason', '')}
                            for s in skipped
                        ]),
                        use_container_width=True, hide_index=True
                    )

                # Colonnes
                st.markdown("##### 🧾 Colonnes disponibles")
                st.caption(', '.join(comp_df_full.columns.tolist()))

                # Aperçu des données
                st.markdown("##### 🔍 Aperçu des données (10 lignes)")
                st.dataframe(comp_df_full.head(10), use_container_width=True, hide_index=True)
            
            st.info(f"💡 **Prochaine étape** : Configurez les critères de filtrage ci-dessous avant de lancer l'analyse.")
            
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
    """Exécution du pipeline d'analyse complet avec critères dynamiques de l'UI."""
    st.session_state['analysis_in_progress'] = True
    st.session_state['analysis_step'] = 0
    
    try:
        pipeline = st.session_state['pipeline']
        market_df = st.session_state['unified_data']
        comp_df = st.session_state['composition_data']  # Déjà filtré sur l'indice sélectionné
        
        # Indice de référence sélectionné dans l'UI (MASI ou MASI 20)
        selected_index = st.session_state.get('selected_index', 'MASI 20')
        
        # Progress bar
        progress = st.progress(0, text="Initialisation...")
        
        # Afficher l'indice utilisé
        progress.progress(5, text=f"📋 Indice de référence : {selected_index}")
        
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
        
        # Étape 4: Filtrage dynamique (règle selon l'indice choisi)
        st.session_state['analysis_step'] = 4
        progress.progress(50, text=f"⏳ Filtrage dynamique ({selected_index})...")
        
        # Règle de sélection : MASI → top-N par poids flottant ; MASI 20 → tous les titres
        investable, filter_report = pipeline.apply_dynamic_filter(
            unified_clean, 
            comp_df,
            index_name=selected_index
        )
        
        n_investable = len(investable['Company'].unique()) if len(investable) > 0 else 0
        progress.progress(60, text=f"✓ Filtrage dynamique terminé ({n_investable} titres investissables)")
        
        # ── Bilan de transparence : intersection marché ∩ indice (jointure par ISIN) ──
        # Ensembles pour des MOTIFS de rejet exacts en Traçabilité
        st.session_state['market_isins_raw'] = set(market_df['CODE_ISIN'].dropna().unique())
        st.session_state['market_isins_quality'] = set(unified_clean['CODE_ISIN'].dropna().unique())

        market_isins = set(unified_clean['CODE_ISIN'].dropna().unique())
        index_isins = set(comp_df['CODE_ISIN'].dropna().unique())
        kept_isins = market_isins & index_isins
        st.session_state['intersection_stats'] = {
            'index_name': selected_index,
            'market': len(market_isins),
            'index': len(index_isins),
            'kept': len(kept_isins),
            'index_absent_from_market': len(index_isins - market_isins),
            'market_outside_index': len(market_isins - index_isins),
            'after_gates': int(investable['CODE_ISIN'].nunique()) if len(investable) > 0 else 0,
        }
        
        # Diagnostic: Vérifier si l'univers investissable est vide
        if len(investable) == 0:
            raise ValueError(
                f"❌ Aucun titre n'a passé le filtrage dynamique.\n\n"
                f"Indice sélectionné : {selected_index}\n\n"
                f"Raison probable : aucun titre commun (par code ISIN) entre les données "
                f"marché et l'indice choisi.\n\n"
                f"Vérifiez que le fichier marché contient bien l'historique des titres de l'indice."
            )
        
        # Étape 5: Indicateurs techniques
        st.session_state['analysis_step'] = 5
        progress.progress(65, text="⏳ Calcul des indicateurs techniques...")
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
        
        # Métadonnées de traçabilité TEMPORAIRES (session-scoped, écrasées à chaque analyse)
        # Restitution pure des colonnes déjà calculées — aucune logique métier dupliquée.
        from src.traceability import build_company_traces
        from config.methodology import FLASH_MOMENTUM_CONFIG
        trace_df = build_company_traces(decisions, FLASH_MOMENTUM_CONFIG)
        st.session_state['analysis_trace'] = trace_df
        try:
            trace_path = ROOT / 'data' / '.app_state' / 'analysis_trace.parquet'
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            trace_df.to_parquet(trace_path, compression='snappy', index=False)
        except Exception:
            pass  # la trace session reste disponible même si l'écriture Parquet échoue

        # Stockage des résultats + critères + rapport de filtrage (pour la Traçabilité)
        st.session_state['decisions_summary'] = summary
        st.session_state['pipeline_results'] = {
            'decisions': decisions,
            'signals': signals,
            'indicators': indicators
        }
        st.session_state['filter_report'] = filter_report
        st.session_state['analysis_criteria'] = {
            'index': selected_index,
            'selection_rule': filter_report.get('selection_rule', ''),
        }
        st.session_state['pipeline_complete'] = True
        st.session_state['analysis_in_progress'] = False
        
        # Sauvegarde
        save_session_state()
        
        # Stats finales
        buy = (summary['Decision'] == 'BUY').sum()
        hold = (summary['Decision'] == 'HOLD').sum()
        sell = (summary['Decision'] == 'SELL').sum()
        
        st.success(f"✅ **Analyse terminée** ({selected_index}) : {len(summary)} titres - {buy} BUY, {hold} HOLD, {sell} SELL")
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
        - Les **critères de filtrage** ne sont pas trop restrictifs
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
