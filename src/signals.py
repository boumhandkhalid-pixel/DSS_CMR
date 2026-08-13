"""
Signal generation, family scoring, overall score, and confidence calculation.

Migrated from Notebook 10.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict


def individual_signals(row: pd.Series, signal_rules: Dict) -> Dict:
    """
    Compute individual signals for one row.
    
    Args:
        row: DataFrame row with indicators
        signal_rules: SIGNAL_RULES from config
    
    Returns:
        dict mapping indicator name to signal value (+1/0/-1/NaN)
    """
    s = {}
    c = row['Cours']
    
    # Trend signals (price vs indicator)
    for ind in ['SMA_20', 'SMA_50', 'EMA_20']:
        v = row[ind]
        if pd.notna(v) and pd.notna(c):
            s[ind] = 1 if c > v else -1 if c < v else 0
        else:
            s[ind] = np.nan
    
    # RSI signal (oversold/overbought)
    rsi = row['RSI_14']
    if pd.notna(rsi):
        if rsi < signal_rules['RSI_14']['bullish_if_below']:
            s['RSI_14'] = 1
        elif rsi > signal_rules['RSI_14']['bearish_if_above']:
            s['RSI_14'] = -1
        else:
            s['RSI_14'] = 0
    else:
        s['RSI_14'] = np.nan
    
    # MACD signal (crossover)
    macd, macd_sig = row['MACD'], row['MACD_Signal']
    if pd.notna(macd) and pd.notna(macd_sig):
        s['MACD'] = 1 if macd > macd_sig else -1
    else:
        s['MACD'] = np.nan
    
    # RVOL signal (confirmation)
    rvol = row['RVOL']
    if pd.notna(rvol):
        if rvol >= signal_rules['RVOL']['confirm_threshold']:
            s['RVOL'] = 1
        elif rvol <= signal_rules['RVOL']['weak_threshold']:
            s['RVOL'] = -1
        else:
            s['RVOL'] = 0
    else:
        s['RVOL'] = np.nan
    
    # VWAP signal (price vs VWAP)
    vwap = row['VWAP']
    if pd.notna(vwap) and pd.notna(c):
        s['VWAP'] = 1 if c > vwap else -1
    else:
        s['VWAP'] = np.nan
    
    # HV_20 not a directional signal
    s['HV_20'] = np.nan
    
    return s


def family_score(row: pd.Series, members: list) -> float:
    """
    Compute family score from individual signals.
    
    Args:
        row: DataFrame row with signal columns
        members: List of signal column names
    
    Returns:
        Family score (0-100) or NaN
    """
    vals = [row[m] for m in members if pd.notna(row.get(m, np.nan))]
    if not vals:
        return np.nan
    # Convert [-1, +1] to [0, 100]
    return (np.mean(vals) + 1) / 2 * 100


def overall_score(row: pd.Series, weights: Dict) -> float:
    """
    Compute weighted overall score from family scores.
    
    Args:
        row: DataFrame row with family score columns
        weights: SCORE_WEIGHTS from config
    
    Returns:
        Overall score (0-100) or NaN
    """
    total_w, ws = 0.0, 0.0
    
    for fam, w in weights.items():
        if fam == 'Risk':
            continue
        v = row.get(f'Score_{fam}', np.nan)
        if pd.notna(v):
            ws += v * w
            total_w += w
    
    return ws / total_w if total_w > 0 else np.nan


def confidence_score_v2(row: pd.Series, df_all: pd.DataFrame, confidence_weights: Dict) -> float:
    """
    Compute confidence score (INDEPENDENT of Overall_Score).
    
    Confidence measures data quality, not signal direction:
    - A. Data Coverage (40%): fraction of indicators with VALID status
    - B. Family Agreement (40%): do families agree on direction?
    - C. Risk Penalty (20%): high HV reduces confidence
    
    Args:
        row: DataFrame row
        df_all: Full DataFrame (for HV quantiles)
        confidence_weights: CONFIDENCE_WEIGHTS from config
    
    Returns:
        Confidence score (0-100%)
    """
    REQUIRED_IND = ['SMA_20', 'SMA_50', 'EMA_20', 'RSI_14', 'MACD', 'RVOL', 'VWAP']
    CW = confidence_weights
    
    # A. Data coverage from validity status
    valid_count = sum(
        1 for ind in REQUIRED_IND
        if row.get(f'Valid_{ind}', 'INSUFFICIENT_DATA') == 'VALID'
    )
    coverage = valid_count / len(REQUIRED_IND)
    
    # B. Family agreement (consensus, not direction)
    fam_scores = [
        row.get(f'Score_{f}', np.nan)
        for f in ['Trend', 'Momentum', 'Volume']
    ]
    valid_fams = [s for s in fam_scores if pd.notna(s)]
    
    if len(valid_fams) >= 2:
        bullish = sum(1 for s in valid_fams if s > 50)
        bearish = sum(1 for s in valid_fams if s < 50)
        agreement = max(bullish, bearish) / len(valid_fams)
    elif len(valid_fams) == 1:
        agreement = 0.5
    else:
        agreement = 0.0
    
    # C. Risk penalty
    hv = row.get('HV_20', np.nan)
    if pd.notna(hv) and len(df_all['HV_20'].dropna()) > 0:
        hv_p75 = df_all['HV_20'].quantile(0.75)
        risk_penalty = min(0.3, max(0.0, (hv - hv_p75) / hv_p75)) if hv_p75 > 0 else 0.0
    else:
        risk_penalty = 0.0
    
    raw = (
        coverage * CW['data_coverage'] +
        agreement * CW['family_agreement'] +
        (1 - risk_penalty) * CW['risk_penalty']
    )
    
    return round(raw * 100, 1)


def compute_family_coverage(row: pd.Series) -> Dict:
    """
    NEW: Compute coverage per family, not just global.
    
    Returns dict with:
        - Trend_Coverage (0.0 to 1.0)
        - Momentum_Coverage (0.0 to 1.0)
        - Volume_Coverage (0.0 to 1.0)
    
    Example:
        If SMA-50 is INSUFFICIENT but SMA-20 and EMA-20 are VALID:
        Trend_Coverage = 2/3 = 0.67
    """
    FAMILIES = {
        'Trend':    ['SMA_20', 'SMA_50', 'EMA_20'],
        'Momentum': ['RSI_14', 'MACD'],
        'Volume':   ['RVOL', 'VWAP'],
    }
    
    coverage = {}
    
    for fam, members in FAMILIES.items():
        valid_count = sum(
            1 for ind in members
            if row.get(f'Valid_{ind}', 'INSUFFICIENT_DATA') == 'VALID'
        )
        coverage[f'{fam}_Coverage'] = valid_count / len(members) if len(members) > 0 else 0.0
    
    return coverage


def compute_signals_and_confidence(
    df: pd.DataFrame,
    signal_rules: Dict,
    score_weights: Dict,
    confidence_weights: Dict
) -> pd.DataFrame:
    """
    Compute signals, family scores, overall score, confidence, and coverage.
    
    Args:
        df: DataFrame with indicators
        signal_rules: SIGNAL_RULES from config
        score_weights: SCORE_WEIGHTS from config
        confidence_weights: CONFIDENCE_WEIGHTS from config
    
    Returns:
        DataFrame with signal, score, confidence, and coverage columns
    """
    # Individual signals
    signals_df = df.apply(lambda r: pd.Series(individual_signals(r, signal_rules)), axis=1)
    sig_cols = ['SMA_20', 'SMA_50', 'EMA_20', 'RSI_14', 'MACD', 'RVOL', 'VWAP', 'HV_20']
    for c in sig_cols:
        df[f'Sig_{c}'] = signals_df[c]
    
    # Family scores
    FAMILIES = {
        'Trend': ['Sig_SMA_20', 'Sig_SMA_50', 'Sig_EMA_20'],
        'Momentum': ['Sig_RSI_14', 'Sig_MACD'],
        'Volume': ['Sig_RVOL', 'Sig_VWAP'],
    }
    
    for fam, members in FAMILIES.items():
        df[f'Score_{fam}'] = df.apply(lambda r: family_score(r, members), axis=1)
    
    # Overall score
    df['Overall_Score'] = df.apply(lambda r: overall_score(r, score_weights), axis=1)
    
    # Confidence
    df['Confidence'] = df.apply(lambda r: confidence_score_v2(r, df, confidence_weights), axis=1)
    
    # NEW: Coverage per family
    coverage_df = df.apply(lambda r: pd.Series(compute_family_coverage(r)), axis=1)
    for col in coverage_df.columns:
        df[col] = coverage_df[col]
    
    return df
