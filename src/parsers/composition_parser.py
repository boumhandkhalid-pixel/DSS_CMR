"""
Parser robuste pour les fichiers de composition d'indice BVC.

Contrairement aux données marché (non plates, multi-formats), les fichiers
de composition sont déjà tabulaires (1 ligne = 1 titre).

Problèmes résolus :
-------------------
1. Fichiers multi-feuilles (chaque feuille = un indice)
2. Inconsistances dans les noms de colonnes :
   - 'Facteur flottant' vs 'Facteur Flottant' vs 'Facteur 1'
3. Espaces parasites dans les noms d'indices
4. Validation structure manquante

Stratégie :
-----------
- Lire TOUTES les feuilles du fichier
- Détecter automatiquement le mapping des colonnes (fuzzy matching)
- Consolider dans un seul DataFrame
- Normaliser les noms d'indices
- Valider la structure
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from src.parsers.isin_utils import normalize_isin


def normalize_index_name(name: str) -> str:
    """
    Normalise les noms d'indices pour comparaison robuste.
    
    Exemples :
    ---------
    'MASI 20' → 'MASI20'
    'masi 20 ' → 'MASI20'
    'MASI-20' → 'MASI20'
    'MASI_20' → 'MASI20'
    """
    return str(name).strip().upper().replace(' ', '').replace('-', '').replace('_', '')


def detect_column_mapping(df_columns: List[str]) -> Dict[str, str]:
    """
    Détecte automatiquement le mapping des colonnes malgré les variations de nommage.
    
    Args:
        df_columns: Liste des noms de colonnes du DataFrame brut
    
    Returns:
        dict: {canonical_name: actual_column_name_in_file}
    
    Exemple:
    --------
    >>> columns = ['Indice', 'Code ISIN', 'Facteur Flottant', 'Capitalisation flottante']
    >>> detect_column_mapping(columns)
    {'Indice': 'Indice', 'CODE_ISIN': 'Code ISIN', 'FF': 'Facteur Flottant', ...}
    """
    mapping = {}

    # Normaliser les colonnes pour comparaison (fuzzy matching)
    def normalize(s):
        return str(s).strip().lower().replace(' ', '').replace('_', '').replace('-', '')

    # Conserver l'ordre des colonnes du fichier
    norm_by_col = [(col, normalize(col)) for col in df_columns]

    # Patterns pour chaque colonne critique (ordre = priorité)
    patterns = {
        'Indice': ['indice'],
        'CODE_ISIN': ['codeisin', 'isin'],
        'Company': ['instrument', 'valeur', 'libelle', 'societe', 'emetteur'],
        'FF': ['facteurflottant', 'facteur1', 'freefloat', 'ff', 'flottant'],
        'FF_MarketCap': ['capitalisationflottante', 'capflottante', 'marketcap', 'capitalisation'],
        'Weight': ['poids', 'weight', 'ponderation'],
        'Capping_Factor': ['facteurplafonnement', 'facteur2', 'cappingfactor', 'plafonnement'],
        'Nb_Titres': ['nombredetitres', 'nbtitres', 'titres', 'nombre'],
        'Date': ['seance', 'date'],
        'Cours': ['cours', 'price', 'close', 'dernier'],
    }

    used_sources = set()  # évite qu'une même colonne source alimente 2 canoniques

    # Passe 1 — correspondance EXACTE (normalisée) : la plus fiable.
    # Empêche p.ex. 'Code Indice' (codeindice) de capturer le canonique 'Indice'.
    for canonical, pattern_list in patterns.items():
        for col, norm in norm_by_col:
            if col in used_sources:
                continue
            if norm in pattern_list:
                mapping[canonical] = col
                used_sources.add(col)
                break

    # Passe 2 — correspondance par inclusion (contains), pour les canoniques restants,
    # sans réutiliser une colonne déjà affectée.
    for canonical, pattern_list in patterns.items():
        if canonical in mapping:
            continue
        for col, norm in norm_by_col:
            if col in used_sources:
                continue
            if any(pattern in norm for pattern in pattern_list):
                mapping[canonical] = col
                used_sources.add(col)
                break

    return mapping


def validate_composition_structure(df: pd.DataFrame, sheet_name: str) -> Tuple[bool, List[str]]:
    """
    Valide qu'un DataFrame a la structure attendue pour une composition d'indice.
    
    Args:
        df: DataFrame à valider
        sheet_name: Nom de la feuille (pour messages d'erreur)
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Colonnes critiques absolument requises
    required = ['Indice', 'CODE_ISIN', 'FF', 'FF_MarketCap', 'Weight']
    
    # Détecter le mapping
    mapping = detect_column_mapping(df.columns.tolist())
    
    # Vérifier colonnes manquantes
    missing = [col for col in required if col not in mapping]
    
    if missing:
        errors.append(
            f"Feuille '{sheet_name}' : colonnes critiques manquantes {missing}.\n"
            f"Colonnes présentes : {df.columns.tolist()}"
        )
    
    # Vérifier DataFrame vide
    if df.empty:
        errors.append(f"Feuille '{sheet_name}' : aucune ligne de données")
    
    # Vérifier types de données (après renommage)
    if not missing:
        df_renamed = df.rename(columns={v: k for k, v in mapping.items()})
        
        # FF doit être numérique entre 0 et 1
        if 'FF' in df_renamed.columns:
            if not pd.api.types.is_numeric_dtype(df_renamed['FF']):
                errors.append(f"Feuille '{sheet_name}' : colonne FF n'est pas numérique")
            elif (df_renamed['FF'] < 0).any() or (df_renamed['FF'] > 1).any():
                n_invalid = ((df_renamed['FF'] < 0) | (df_renamed['FF'] > 1)).sum()
                errors.append(f"Feuille '{sheet_name}' : {n_invalid} valeurs FF hors [0, 1]")
        
        # FF_MarketCap doit être positif
        if 'FF_MarketCap' in df_renamed.columns:
            if not pd.api.types.is_numeric_dtype(df_renamed['FF_MarketCap']):
                errors.append(f"Feuille '{sheet_name}' : colonne FF_MarketCap n'est pas numérique")
            elif (df_renamed['FF_MarketCap'] <= 0).any():
                n_invalid = (df_renamed['FF_MarketCap'] <= 0).sum()
                errors.append(f"Feuille '{sheet_name}' : {n_invalid} valeurs FF_MarketCap ≤ 0")
        
        # Weight doit être entre 0 et 1
        if 'Weight' in df_renamed.columns:
            if not pd.api.types.is_numeric_dtype(df_renamed['Weight']):
                errors.append(f"Feuille '{sheet_name}' : colonne Weight n'est pas numérique")
            elif (df_renamed['Weight'] < 0).any() or (df_renamed['Weight'] > 1).any():
                n_invalid = ((df_renamed['Weight'] < 0) | (df_renamed['Weight'] > 1)).sum()
                errors.append(f"Feuille '{sheet_name}' : {n_invalid} valeurs Weight hors [0, 1]")
    
    return len(errors) == 0, errors


def parse_composition_file(
    excel_path: str,
    index_name: Optional[str] = None,
    validate: bool = True
) -> Tuple[pd.DataFrame, Dict]:
    """
    Parse robuste d'un fichier de composition multi-feuilles.
    
    Processus :
    -----------
    1. Lit TOUTES les feuilles du fichier Excel
    2. Détecte automatiquement le mapping des colonnes (fuzzy matching)
    3. Valide la structure de chaque feuille
    4. Consolide dans un seul DataFrame
    5. Normalise les noms d'indices
    6. Filtre sur l'indice cible si spécifié
    
    Args:
        excel_path: Chemin vers le fichier Excel
        index_name: Nom de l'indice à filtrer (optionnel). Si None, retourne tous les indices.
        validate: Si True, valide la structure (recommandé en production)
    
    Returns:
        (composition_df, parse_report)
    
    Raises:
        ValueError: Si validation échoue ou indice introuvable
    
    Exemple:
    --------
    >>> df, report = parse_composition_file('composition.xlsx', index_name='MASI 20')
    >>> print(f"Titres dans MASI 20 : {len(df)}")
    """
    from openpyxl import load_workbook
    
    excel_path = Path(excel_path)
    
    if not excel_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {excel_path}")
    
    # Rapport de parsing
    report = {
        'file_path': str(excel_path),
        'sheets_processed': [],
        'sheets_skipped': [],
        'total_rows_raw': 0,
        'total_rows_filtered': 0,
        'indices_found': [],
        'validation_errors': [],
        'target_index': index_name,
    }
    
    # Lire toutes les feuilles
    xls = pd.ExcelFile(excel_path)
    all_dfs = []
    
    print(f"[INFO] Lecture du fichier : {excel_path.name}")
    print(f"[INFO] Feuilles trouvées : {xls.sheet_names}\n")
    
    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # Validation structure
            if validate:
                is_valid, errors = validate_composition_structure(df, sheet_name)
                if not is_valid:
                    report['validation_errors'].extend(errors)
                    report['sheets_skipped'].append({
                        'sheet': sheet_name,
                        'reason': 'Validation échouée',
                        'errors': errors
                    })
                    print(f"[WARN] Feuille '{sheet_name}' ignorée : validation échouée")
                    for error in errors:
                        print(f"       {error}")
                    continue
            
            # Détecter le mapping des colonnes
            mapping = detect_column_mapping(df.columns.tolist())
            
            # Renommer avec les noms canoniques
            reverse_mapping = {v: k for k, v in mapping.items()}
            df_renamed = df.rename(columns=reverse_mapping)
            
            # Garder seulement les colonnes canoniques
            canonical_cols = ['Indice', 'CODE_ISIN', 'Company', 'FF', 'FF_MarketCap',
                            'Weight', 'Capping_Factor', 'Nb_Titres', 'Date', 'Cours']
            available_cols = [col for col in canonical_cols if col in df_renamed.columns]
            df_clean = df_renamed[available_cols].copy()
            
            # Normaliser les noms d'indices (strip espaces parasites)
            if 'Indice' in df_clean.columns:
                df_clean['Indice'] = df_clean['Indice'].str.strip()
            
            # Normaliser CODE_ISIN (isole le code propre pour une jointure fiable)
            if 'CODE_ISIN' in df_clean.columns:
                df_clean['CODE_ISIN'] = df_clean['CODE_ISIN'].map(normalize_isin)
            
            all_dfs.append(df_clean)
            
            report['sheets_processed'].append({
                'sheet': sheet_name,
                'rows': len(df_clean),
                'columns_detected': list(mapping.keys())
            })
            
            report['total_rows_raw'] += len(df_clean)
            
            # Logger les indices trouvés
            if 'Indice' in df_clean.columns:
                indices_in_sheet = df_clean['Indice'].unique().tolist()
                report['indices_found'].extend(indices_in_sheet)
                print(f"[INFO] ✓ {sheet_name:30s} : {len(df_clean):3d} lignes, indices={indices_in_sheet}")
            else:
                print(f"[INFO] ✓ {sheet_name:30s} : {len(df_clean):3d} lignes")
        
        except Exception as e:
            report['sheets_skipped'].append({
                'sheet': sheet_name,
                'reason': 'Erreur lecture',
                'error': str(e)
            })
            print(f"[ERROR] Erreur lecture feuille '{sheet_name}' : {e}")
    
    # Vérifier qu'au moins une feuille a été chargée
    if not all_dfs:
        raise ValueError(
            f"❌ Aucune feuille valide trouvée dans le fichier.\n"
            f"Feuilles ignorées : {[s['sheet'] for s in report['sheets_skipped']]}\n"
            f"Erreurs : {report['validation_errors']}"
        )
    
    # Consolider toutes les feuilles
    consolidated = pd.concat(all_dfs, ignore_index=True)
    
    # Dédupliquer les indices trouvés
    report['indices_found'] = list(set(report['indices_found']))
    
    print(f"\n[INFO] ✓ Consolidation : {len(consolidated)} lignes, {consolidated['Indice'].nunique()} indices")
    print(f"[INFO] ✓ Indices disponibles : {report['indices_found']}")
    
    # Filtrage par indice si spécifié
    if index_name:
        print(f"\n[INFO] Filtrage sur l'indice : '{index_name}'")
        
        filtered = consolidated[
            consolidated['Indice'].apply(normalize_index_name) == normalize_index_name(index_name)
        ].copy()
        
        if filtered.empty:
            # Générer message d'erreur détaillé
            available_normalized = [
                f"  • '{idx}' (normalisé: {normalize_index_name(idx)})"
                for idx in report['indices_found']
            ]
            
            raise ValueError(
                f"❌ Aucun titre trouvé pour l'indice '{index_name}'.\n\n"
                f"Indice recherché (normalisé) : {normalize_index_name(index_name)}\n\n"
                f"Indices disponibles dans le fichier :\n" +
                "\n".join(available_normalized) +
                f"\n\nVérifiez que le nom de l'indice dans config/methodology.py "
                f"correspond bien à une valeur présente dans le fichier."
            )
        
        report['total_rows_filtered'] = len(filtered)
        print(f"[INFO] ✓ Après filtrage : {len(filtered)} lignes pour '{index_name}'")
        
        return filtered, report
    else:
        report['total_rows_filtered'] = len(consolidated)
        return consolidated, report


if __name__ == '__main__':
    """Test du parser avec le fichier sample."""
    import sys
    from pathlib import Path
    
    # Chemin vers le fichier sample
    ROOT = Path(__file__).resolve().parents[2]
    sample_file = ROOT / 'samples' / 'Compo_All_Indices_20260731_copy.xlsx'
    
    if not sample_file.exists():
        print(f"❌ Fichier sample introuvable : {sample_file}")
        sys.exit(1)
    
    print("="*80)
    print("TEST DU PARSER COMPOSITION")
    print("="*80 + "\n")
    
    # Test 1 : Sans filtrage (tous les indices)
    print("Test 1 : Lecture de tous les indices")
    print("-" * 80)
    df_all, report_all = parse_composition_file(sample_file)
    print(f"\n✅ Succès : {len(df_all)} lignes, {df_all['Indice'].nunique()} indices")
    print(f"   Indices : {df_all['Indice'].unique().tolist()}\n")
    
    # Test 2 : Filtrage sur MASI 20
    print("\nTest 2 : Filtrage sur 'MASI 20'")
    print("-" * 80)
    df_masi20, report_masi20 = parse_composition_file(sample_file, index_name='MASI 20')
    print(f"\n✅ Succès : {len(df_masi20)} titres dans MASI 20\n")
    
    # Test 3 : Filtrage avec normalisation robuste
    test_cases = ['MASI20', 'masi 20', 'MASI-20']
    print("\nTest 3 : Normalisation robuste")
    print("-" * 80)
    for idx_name in test_cases:
        try:
            df_test, _ = parse_composition_file(sample_file, index_name=idx_name)
            print(f"✅ '{idx_name}' → {len(df_test)} titres trouvés")
        except ValueError as e:
            print(f"❌ '{idx_name}' → Erreur : {e}")
    
    print("\n" + "="*80)
    print("✅ Tests terminés avec succès")
    print("="*80)
