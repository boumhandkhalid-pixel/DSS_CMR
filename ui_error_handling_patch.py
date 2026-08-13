"""
Patch pour gestion d'erreurs professionnelle - À intégrer dans ui/app.py
"""

import logging
import uuid
from datetime import datetime

# Configuration logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dss_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def generate_error_reference() -> str:
    """Génère un ID d'incident unique."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"DSS-{timestamp}-{unique_id}"


def show_user_error(message: str, error_ref: str = None):
    """Affiche une erreur métier (sans détails techniques)."""
    st.error(f"❌ {message}")
    if error_ref:
        st.caption(f"Référence incident : `{error_ref}`")
        st.caption("Si le problème persiste, contactez l'équipe support avec cette référence.")


# Exemple d'utilisation dans import_market_data
def import_market_data_CORRECTED(uploaded_file):
    """Import avec gestion d'erreurs professionnelle."""
    error_ref = None
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
        
        # Stockage
        st.session_state['unified_data'] = unified
        st.session_state['market_imported'] = True
        st.session_state['market_file_name'] = uploaded_file.name
        
        # Sauv egarde
        save_session_state()
        
        # Nettoyage
        Path(temp_path).unlink(missing_ok=True)
        
        # Succès
        n_companies = unified['Company'].nunique()
        n_records = len(unified)
        st.success(f"✅ Données marché importées : **{n_companies} sociétés**, **{n_records:,} observations**")
        st.rerun()
        
    except Exception as e:
        # LOG pour développeur
        error_ref = generate_error_reference()
        logger.error(
            f"Market data import failed [{error_ref}]",
            exc_info=True,
            extra={'filename': uploaded_file.name}
        )
        
        # MESSAGE pour utilisateur
        show_user_error(
            "Le fichier des données marché ne peut pas être traité. "
            "Veuillez vérifier le format du fichier ou contactez l'équipe support.",
            error_ref
        )
    
    finally:
        # Nettoyage fichier temporaire
        if 'temp_path' in locals():
            Path(temp_path).unlink(missing_ok=True)


# Exemple pour import_composition_data
def import_composition_data_CORRECTED(uploaded_file):
    """Import composition avec détection dynamique indices."""
    error_ref = None
    try:
        # Fichier temporaire
        suffix = '.xlsx' if uploaded_file.name.endswith('.xlsx') else '.xls'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='wb') as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name
        
        # Pipeline
        pipeline = st.session_state['pipeline']
        comp_df, report = pipeline.ingest_index_composition(temp_path)
        
        # DÉTECTION DYNAMIQUE DES INDICES
        if 'Index' in comp_df.columns:
            # Extraire les indices disponibles
            indices = sorted(comp_df['Index'].dropna().unique().tolist())
            st.session_state['available_indices'] = indices
            
            # MASI par défaut si existe, sinon le premier
            default_index = "MASI" if "MASI" in indices else (indices[0] if indices else None)
            st.session_state['selected_index'] = default_index
        else:
            raise ValueError("Colonne 'Index' manquante dans le fichier de composition")
        
        # Stockage
        st.session_state['composition_data'] = comp_df
        st.session_state['index_imported'] = True
        st.session_state['index_file_name'] = uploaded_file.name
        
        # Sauvegarde
        save_session_state()
        
        # Nettoyage
        Path(temp_path).unlink(missing_ok=True)
        
        # Succès
        n_securities = len(comp_df)
        n_indices = len(indices)
        st.success(f"✅ Composition importée : **{n_securities} titres**, **{n_indices} indices détectés**")
        st.info(f"Indices disponibles : {', '.join(indices)}")
        st.rerun()
        
    except Exception as e:
        # LOG pour développeur
        error_ref = generate_error_reference()
        logger.error(
            f"Composition import failed [{error_ref}]",
            exc_info=True,
            extra={'filename': uploaded_file.name}
        )
        
        # MESSAGE pour utilisateur
        show_user_error(
            "Le fichier de composition des indices est incompatible. "
            "Vérifiez qu'il contient les colonnes requises (Index, CODE ISIN, Company).",
            error_ref
        )
    
    finally:
        # Nettoyage fichier temporaire
        if 'temp_path' in locals():
            Path(temp_path).unlink(missing_ok=True)


# Exemple pour run_analysis
def run_analysis_CORRECTED():
    """Analyse avec gestion d'erreurs et indice dynamique."""
    st.session_state['analysis_in_progress'] = True
    error_ref = None
    
    try:
        pipeline = st.session_state['pipeline']
        market_df = st.session_state['unified_data']
        comp_df = st.session_state['composition_data']
        selected_index = st.session_state.get('selected_index', 'MASI')
        
        # Progress bar
        progress = st.progress(0, text="Initialisation...")
        
        # Étapes pipeline...
        # (identiques mais avec meilleure gestion erreurs)
        
        # Filtrage dynamique AVEC INDICE SÉLECTIONNÉ
        st.session_state['analysis_step'] = 4
        progress.progress(50, text=f"⏳ Filtrage dynamique ({selected_index})...")
        
        investable, filter_report = pipeline.apply_dynamic_filter(
            unified_clean,
            comp_df,
            selected_index=selected_index  # ← NOUVEAU : indice dynamique
        )
        
        n_investable = len(investable['Company'].unique()) if len(investable) > 0 else 0
        progress.progress(60, text=f"✓ {n_investable} titres investissables ({selected_index})")
        
        # Vérification univers vide
        if len(investable) == 0:
            raise ValueError(
                f"Aucun titre ne correspond aux critères de filtrage pour l'indice {selected_index}. "
                f"Vérifiez les fichiers importés."
            )
        
        # ... suite du pipeline ...
        
        # Succès
        st.success(f"✅ Analyse terminée ({selected_index})")
        st.rerun()
        
    except Exception as e:
        # LOG pour développeur
        error_ref = generate_error_reference()
        logger.error(
            f"Analysis failed [{error_ref}]",
            exc_info=True,
            extra={
                'selected_index': st.session_state.get('selected_index'),
                'market_file': st.session_state.get('market_file_name'),
                'comp_file': st.session_state.get('index_file_name')
            }
        )
        
        # MESSAGE pour utilisateur
        show_user_error(
            "Une erreur est survenue lors de l'analyse. "
            "Veuillez vérifier les fichiers importés ou contactez l'équipe support.",
            error_ref
        )
        
    finally:
        st.session_state['analysis_in_progress'] = False


print("✓ Patch de gestion d'erreurs prêt")
print("Intégrer ces fonctions dans ui/app.py")
