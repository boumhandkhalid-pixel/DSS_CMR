"""
Investment decision generation (BUY/HOLD/SELL).

Migrated from Notebook 11.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, Tuple


def make_decision(
    row: pd.Series,
    thresholds: Dict,
    min_coverage: float
) -> Tuple[str, float]:
    """
    Make investment decision for one row.
    
    Args:
        row: DataFrame row with Overall_Score and Confidence
        thresholds: DECISION_THRESHOLDS from config
        min_coverage: MIN_COVERAGE_FOR_DECISION from config
    
    Returns:
        (decision, coverage) tuple
    """
    REQUIRED_IND = ['SMA_20', 'SMA_50', 'EMA_20', 'RSI_14', 'MACD', 'RVOL', 'VWAP']
    
    score = row.get('Overall_Score', np.nan)
    conf = row.get('Confidence', np.nan)
    
    # Calculate data coverage
    valid_count = sum(
        1 for ind in REQUIRED_IND
        if row.get(f'Valid_{ind}', 'INSUFFICIENT_DATA') == 'VALID'
    )
    coverage = valid_count / len(REQUIRED_IND)
    
    # Gate 1: Minimum coverage
    if coverage < min_coverage:
        return 'INSUFFICIENT_DATA', coverage
    
    # Gate 2: Score and confidence must be computable
    if pd.isna(score) or pd.isna(conf):
        return 'INSUFFICIENT_DATA', coverage
    
    # Decision rules
    buy_t = thresholds['buy']
    sell_t = thresholds['sell']
    
    if score >= buy_t['min_score'] and conf >= buy_t['min_confidence']:
        return 'BUY', coverage
    
    if score <= sell_t['max_score'] and conf >= sell_t['min_confidence']:
        return 'SELL', coverage
    
    return 'HOLD', coverage


def make_investment_decisions(
    df: pd.DataFrame,
    thresholds: Dict,
    min_coverage: float
) -> pd.DataFrame:
    """
    Generate investment decisions for all rows.
    
    Args:
        df: DataFrame with signals and scores
        thresholds: DECISION_THRESHOLDS from config
        min_coverage: MIN_COVERAGE_FOR_DECISION from config
    
    Returns:
        DataFrame with Decision and Data_Coverage columns
    """
    results = df.apply(
        lambda r: pd.Series(
            make_decision(r, thresholds, min_coverage),
            index=['Decision', 'Data_Coverage']
        ),
        axis=1
    )
    
    df['Decision'] = results['Decision']
    df['Data_Coverage'] = results['Data_Coverage']
    
    return df


def generate_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate per-company decision summary (latest decision per company).
    
    Args:
        df: DataFrame with decisions
    
    Returns:
        Summary DataFrame with one row per company
    """
    rows_out = []
    
    for isin, grp in df.groupby('CODE_ISIN'):
        grp_s = grp.sort_values('Date')
        
        # Prefer rows with valid decisions
        valid = grp_s[grp_s['Decision'] != 'INSUFFICIENT_DATA']
        latest = valid.tail(1) if len(valid) > 0 else grp_s.tail(1)
        
        if len(latest) == 0:
            continue
        
        r = latest.iloc[0]
        
        # Build signal summary
        sig_parts = []
        for sig_col, label in [
            ('Sig_EMA_20', 'EMA_20'),
            ('Sig_RSI_14', 'RSI_14'),
            ('Sig_RVOL', 'RVOL'),
            ('Sig_VWAP', 'VWAP')
        ]:
            v = r.get(sig_col, np.nan)
            if pd.notna(v):
                arrow = '↑' if v > 0 else '↓' if v < 0 else '='
                sig_parts.append(f'{label}{arrow}')
        
        rows_out.append({
            'CODE_ISIN': isin,
            'Company': r['Company'],
            'Date': r['Date'].date() if pd.notna(r['Date']) else 'N/A',
            'Cours': round(r['Cours'], 2) if pd.notna(r['Cours']) else np.nan,
            'Overall_Score': round(r['Overall_Score'], 1) if pd.notna(r['Overall_Score']) else np.nan,
            'Confidence': r['Confidence'],
            'Decision': r['Decision'],
            'Data_Coverage': f"{r['Data_Coverage'] * 100:.0f}%",
            'Signals': ' | '.join(sig_parts) if sig_parts else 'no valid signals',
        })
    
    return pd.DataFrame(rows_out)
