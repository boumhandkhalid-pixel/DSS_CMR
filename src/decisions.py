"""
Investment decision generation (BUY/HOLD/SELL).

La décision est pilotée par le SCORE TECHNIQUE « Flash Momentum » (0–100),
source de vérité métier (voir src/scoring_flash.py et FLASH_MOMENTUM_CONFIG).

Principes (méthodologie encadrant) :
    - Technical Score → pilote BUY / HOLD / SELL via une grille configurable.
    - Data Coverage est une dimension INDÉPENDANTE : une couverture insuffisante
      produit INSUFFICIENT_DATA, JAMAIS un SELL automatique.

Mapping par défaut (FLASH_DECISION_THRESHOLDS, configurable) :
    score ≥ buy_min_score (60)  → BUY
    score < sell_max_score (40) → SELL
    sinon (zone Neutre 40–59)   → HOLD
    couverture < min_coverage   → INSUFFICIENT_DATA
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, Tuple


def make_decision(
    row: pd.Series,
    flash_thresholds: Dict,
    min_coverage: float,
) -> Tuple[str, float]:
    """
    Décision d'investissement pour une ligne, pilotée par le Technical Score.

    Args:
        row: ligne avec 'Technical_Score' et 'Flash_Coverage'
        flash_thresholds: FLASH_DECISION_THRESHOLDS (buy_min_score, sell_max_score)
        min_coverage: MIN_COVERAGE_FOR_DECISION (seuil de couverture)

    Returns:
        (decision, coverage)
    """
    score = row.get('Technical_Score', np.nan)
    coverage = row.get('Flash_Coverage', np.nan)

    if pd.isna(coverage):
        coverage = 0.0

    # Gate 1 : couverture insuffisante → INSUFFICIENT_DATA (jamais SELL)
    if coverage < min_coverage:
        return 'INSUFFICIENT_DATA', coverage

    # Gate 2 : score non calculable → INSUFFICIENT_DATA
    if pd.isna(score):
        return 'INSUFFICIENT_DATA', coverage

    # Décision pilotée par le Technical Score
    if score >= flash_thresholds['buy_min_score']:
        return 'BUY', coverage
    if score < flash_thresholds['sell_max_score']:
        return 'SELL', coverage
    return 'HOLD', coverage


def make_investment_decisions(
    df: pd.DataFrame,
    flash_thresholds: Dict,
    min_coverage: float,
) -> pd.DataFrame:
    """
    Génère les décisions BUY/HOLD/SELL pour toutes les lignes.

    Args:
        df: DataFrame avec Technical_Score et Flash_Coverage
        flash_thresholds: FLASH_DECISION_THRESHOLDS
        min_coverage: MIN_COVERAGE_FOR_DECISION

    Returns:
        DataFrame avec colonnes Decision et Data_Coverage
    """
    results = df.apply(
        lambda r: pd.Series(
            make_decision(r, flash_thresholds, min_coverage),
            index=['Decision', 'Data_Coverage']
        ),
        axis=1
    )

    df['Decision'] = results['Decision']
    df['Data_Coverage'] = results['Data_Coverage']

    return df


def generate_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Résumé par société (dernière décision exploitable par société).

    Expose le Technical Score officiel et sa classification, en conservant
    Overall_Score/Confidence pour la vue analytique.

    Args:
        df: DataFrame avec décisions

    Returns:
        Résumé (une ligne par société)
    """
    rows_out = []

    from config.methodology import FLASH_MOMENTUM_CONFIG
    cov_inputs = FLASH_MOMENTUM_CONFIG['coverage_inputs']
    n_total_ind = len(cov_inputs)

    def _r1(v):
        return round(float(v), 1) if pd.notna(v) else np.nan

    for isin, grp in df.groupby('CODE_ISIN'):
        grp_s = grp.sort_values('Date')

        # Préférer les lignes avec décision exploitable
        valid = grp_s[grp_s['Decision'] != 'INSUFFICIENT_DATA']
        latest = valid.tail(1) if len(valid) > 0 else grp_s.tail(1)

        if len(latest) == 0:
            continue

        r = latest.iloc[0]

        # Indicateurs du score Flash Momentum calculés (non-NaN) sur la ligne retenue
        n_computed = sum(1 for c in cov_inputs if c in r.index and pd.notna(r.get(c)))

        # Historique de cours de la société (pour dates de couverture)
        price_rows = grp_s[grp_s['Cours'].notna()] if 'Cours' in grp_s.columns else grp_s.iloc[0:0]
        first_date = price_rows['Date'].min() if len(price_rows) else pd.NaT
        last_date = price_rows['Date'].max() if len(price_rows) else pd.NaT
        n_sessions = int(len(price_rows))

        rows_out.append({
            'CODE_ISIN': isin,
            'Company': r['Company'],
            'Date': r['Date'].date() if pd.notna(r['Date']) else 'N/A',
            'Cours': round(r['Cours'], 2) if pd.notna(r['Cours']) else np.nan,
            # Score technique officiel (Flash Momentum)
            'Technical_Score': _r1(r.get('Technical_Score', np.nan)),
            'Score_Class': r.get('Score_Class', 'N/A'),
            'Score_Symbol': r.get('Score_Symbol', ''),
            # Détail des points par pilier Flash Momentum
            'Flash_Vol_Score': _r1(r.get('Flash_Vol_Score', np.nan)),
            'Flash_RSI_Score': _r1(r.get('Flash_RSI_Score', np.nan)),
            'Flash_MM_Score': _r1(r.get('Flash_MM_Score', np.nan)),
            'Flash_MACD_Score': _r1(r.get('Flash_MACD_Score', np.nan)),
            # Traçabilité OBV / Golden Cross
            'OBV_Trend': r.get('OBV_Trend', None),
            'Golden_Cross_Recent': bool(r.get('Golden_Cross_Recent', False)),
            # Couverture des données
            'Decision': r['Decision'],
            'Data_Coverage': f"{r['Data_Coverage'] * 100:.0f}%",
            'Indicators_Computed': n_computed,
            'Indicators_Total': n_total_ind,
            # Fenêtre historique
            'First_Price_Date': first_date.date() if pd.notna(first_date) else 'N/A',
            'Last_Price_Date': last_date.date() if pd.notna(last_date) else 'N/A',
            'N_Sessions': n_sessions,
        })

    return pd.DataFrame(rows_out)
