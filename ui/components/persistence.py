"""
Gestionnaire de persistance pour l'état de l'application.

Sauvegarde l'état dans des fichiers Parquet pour survivre aux rafraîchissements.
"""

from __future__ import annotations

import pandas as pd
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class AppStateManager:
    """Gestionnaire d'état persistant pour l'application DSS."""
    
    def __init__(self, state_dir: Path = None):
        """
        Initialise le gestionnaire d'état.
        
        Args:
            state_dir: Répertoire pour sauvegarder l'état (défaut: data/.app_state)
        """
        if state_dir is None:
            state_dir = Path(__file__).parent.parent.parent / 'data' / '.app_state'
        
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.state_dir / 'metadata.json'
    
    def save_session(
        self,
        unified_data: Optional[pd.DataFrame] = None,
        composition_data: Optional[pd.DataFrame] = None,
        decisions_summary: Optional[pd.DataFrame] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Sauvegarde l'état de la session.
        
        Args:
            unified_data: Données marché unifiées
            composition_data: Composition de l'indice
            decisions_summary: Résumé des décisions
            metadata: Métadonnées (noms de fichiers, rapports, etc.)
        """
        # Sauvegarder les DataFrames
        if unified_data is not None:
            unified_data.to_parquet(
                self.state_dir / 'unified_data.parquet',
                compression='snappy'
            )
        
        if composition_data is not None:
            composition_data.to_parquet(
                self.state_dir / 'composition_data.parquet',
                compression='snappy'
            )
        
        if decisions_summary is not None:
            decisions_summary.to_parquet(
                self.state_dir / 'decisions_summary.parquet',
                compression='snappy'
            )
        
        # Sauvegarder les métadonnées
        if metadata is None:
            metadata = {}
        
        metadata['last_updated'] = datetime.now().isoformat()
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def load_session(self) -> Dict[str, Any]:
        """
        Charge l'état de la session sauvegardée.
        
        Returns:
            Dict contenant les données et métadonnées
        """
        session = {
            'unified_data': None,
            'composition_data': None,
            'decisions_summary': None,
            'metadata': {},
            'has_saved_state': False
        }
        
        # Charger unified_data
        unified_path = self.state_dir / 'unified_data.parquet'
        if unified_path.exists():
            session['unified_data'] = pd.read_parquet(unified_path)
            session['has_saved_state'] = True
        
        # Charger composition_data
        comp_path = self.state_dir / 'composition_data.parquet'
        if comp_path.exists():
            session['composition_data'] = pd.read_parquet(comp_path)
        
        # Charger decisions_summary
        dec_path = self.state_dir / 'decisions_summary.parquet'
        if dec_path.exists():
            session['decisions_summary'] = pd.read_parquet(dec_path)
        
        # Charger métadonnées
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                session['metadata'] = json.load(f)
        
        return session
    
    def clear_session(self) -> None:
        """Efface l'état sauvegardé."""
        for f in self.state_dir.glob('*.parquet'):
            f.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()
    
    def session_exists(self) -> bool:
        """Vérifie si une session sauvegardée existe."""
        return (
            (self.state_dir / 'unified_data.parquet').exists() or
            (self.state_dir / 'decisions_summary.parquet').exists()
        )
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur la session sauvegardée.
        
        Returns:
            Dict avec les informations (dernière mise à jour, taille, etc.)
        """
        if not self.session_exists():
            return {'exists': False}
        
        info = {'exists': True}
        
        # Charger métadonnées
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                info.update(json.load(f))
        
        # Ajouter taille des fichiers
        total_size = sum(f.stat().st_size for f in self.state_dir.glob('*.parquet'))
        info['total_size_kb'] = total_size / 1024
        
        return info


# Instance globale
_state_manager = None


def get_state_manager() -> AppStateManager:
    """Retourne l'instance globale du gestionnaire d'état."""
    global _state_manager
    if _state_manager is None:
        _state_manager = AppStateManager()
    return _state_manager
