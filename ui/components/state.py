from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import streamlit as st
from ui.components.persistence import get_state_manager

STATE_DEFAULTS: dict[str, Any] = {
    "market_file_name": None,
    "market_imported": False,
    "index_file_name": None,
    "index_imported": False,
    "pipeline_complete": False,
    "analysis_in_progress": False,
    "analysis_step": None,
    "market_upload_temp_path": None,
    "market_upload_name": None,
    "market_preview_page": 0,
    "comp_upload_temp_path": None,
    "comp_upload_name": None,
    "comp_preview_page": 0,
    "reset_counter": 0,  # Compteur pour forcer le reset des uploaders
    # Pas de résumé détaillé, juste l'essentiel
    # Pas de paramètres complexes
    # Pas de métriques détaillées
}


def init_session_state() -> None:
    """Initialise l'état de session minimaliste."""
    
    # Charger l'état sauvegardé si disponible
    state_manager = get_state_manager()
    
    # Restaurer depuis sauvegarde si disponible
    if 'initialized' not in st.session_state:
        saved_session = state_manager.load_session()
        
        if saved_session['has_saved_state']:
            # Restaurer l'essentiel seulement
            if saved_session['unified_data'] is not None:
                st.session_state['unified_data'] = saved_session['unified_data']
                st.session_state['market_imported'] = True
            
            if saved_session['composition_data'] is not None:
                st.session_state['composition_data'] = saved_session['composition_data']
                st.session_state['index_imported'] = True
            
            if saved_session.get('composition_data_full') is not None:
                st.session_state['composition_data_full'] = saved_session['composition_data_full']
            
            if saved_session['decisions_summary'] is not None:
                st.session_state['decisions_summary'] = saved_session['decisions_summary']
                st.session_state['pipeline_complete'] = True

            # Restaurer les essentiels de traçabilité depuis les métadonnées
            md = saved_session.get('metadata', {}) or {}
            if md.get('selected_index'):
                st.session_state['selected_index'] = md['selected_index']
            if md.get('filter_report'):
                st.session_state['filter_report'] = md['filter_report']
            if md.get('intersection_stats'):
                st.session_state['intersection_stats'] = md['intersection_stats']
            if md.get('market_isins_raw'):
                st.session_state['market_isins_raw'] = set(md['market_isins_raw'])
            if md.get('market_isins_quality'):
                st.session_state['market_isins_quality'] = set(md['market_isins_quality'])

            # Restaurer la trace d'analyse (Parquet) si présente
            try:
                import pandas as pd
                trace_path = state_manager.state_dir / 'analysis_trace.parquet'
                if trace_path.exists():
                    st.session_state['analysis_trace'] = pd.read_parquet(trace_path)
            except Exception:
                pass
        
        st.session_state['initialized'] = True
    
    # Initialiser les valeurs par défaut minimales
    for key, value in STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, dict) else value


def reset_session_state() -> None:
    """Efface complètement la session (état + fichiers)."""
    state_manager = get_state_manager()
    state_manager.clear_session()
    
    # Incrémenter le compteur de reset pour forcer le re-render des uploaders
    current_counter = st.session_state.get('reset_counter', 0)
    
    for key in list(st.session_state.keys()):
        st.session_state.pop(key, None)
    
    init_session_state()
    
    # Incrémenter le compteur pour changer les keys des widgets
    st.session_state['reset_counter'] = current_counter + 1


def save_session_state() -> None:
    """Sauvegarde l'état actuel de la session sur disque."""
    state_manager = get_state_manager()
    
    # Métadonnées minimales + essentiels de traçabilité (pour survivre au rechargement)
    _mr = st.session_state.get('market_isins_raw') or set()
    _mq = st.session_state.get('market_isins_quality') or set()
    metadata = {
        'market_file_name': st.session_state.get('market_file_name', ''),
        'index_file_name': st.session_state.get('index_file_name', ''),
        'market_imported': st.session_state.get('market_imported', False),
        'index_imported': st.session_state.get('index_imported', False),
        'pipeline_complete': st.session_state.get('pipeline_complete', False),
        # Traçabilité (index sélectionné, rapport de filtrage, intersection)
        'selected_index': st.session_state.get('selected_index'),
        'filter_report': st.session_state.get('filter_report'),
        'intersection_stats': st.session_state.get('intersection_stats'),
        'market_isins_raw': sorted(_mr),
        'market_isins_quality': sorted(_mq),
    }
    
    # Sauvegarder uniquement l'essentiel
    state_manager.save_session(
        unified_data=st.session_state.get('unified_data'),
        composition_data=st.session_state.get('composition_data'),
        decisions_summary=st.session_state.get('decisions_summary'),
        metadata=metadata,
        composition_data_full=st.session_state.get('composition_data_full')
    )


def mark_market_uploaded(file_name: str) -> None:
    st.session_state.market_file_name = file_name
    st.session_state.market_imported = True
    save_session_state()


def mark_index_uploaded(file_name: str) -> None:
    st.session_state.index_file_name = file_name
    st.session_state.index_imported = True
    save_session_state()


def mark_analysis_completed() -> None:
    st.session_state.pipeline_complete = True
    save_session_state()
