"""
Technical indicators computation with validity tracking.

This module computes all 10 technical indicators and tracks validity status
per indicator per row (VALID vs INSUFFICIENT_DATA).

Migrated from Notebook 09.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict


def _rsi_wilder(prices_clean: pd.Series, period: int) -> pd.Series:
    """
    Compute Wilder RSI on clean (no-NaN) price series.
    
    Args:
        prices_clean: Series of consecutive prices (no gaps)
        period: RSI period (typically 14)
    
    Returns:
        RSI values (first `period` values will be NaN)
    """
    n = len(prices_clean)
    delta = prices_clean.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    
    ag = pd.Series(np.nan, index=prices_clean.index)
    al = pd.Series(np.nan, index=prices_clean.index)
    
    if n >= period:
        ag.iloc[period - 1] = gain.iloc[:period].mean()
        al.iloc[period - 1] = loss.iloc[:period].mean()
        
        for i in range(period, n):
            ag.iloc[i] = (ag.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            al.iloc[i] = (al.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
    
    rs = ag / al.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def compute_indicators_for_company(
    group_df: pd.DataFrame,
    params: Dict,
    min_obs: Dict
) -> pd.DataFrame:
    """
    Compute all indicators for a single company.
    
    Args:
        group_df: DataFrame for one CODE_ISIN
        params: INDICATOR_PARAMS from config
        min_obs: INDICATOR_MIN_OBS from config
    
    Returns:
        DataFrame with indicator columns added
    """
    g = group_df.sort_values('Date').copy()
    
    # Initialize indicator columns
    IND = ['SMA_20', 'SMA_50', 'EMA_20', 'RSI_14', 'MACD', 'MACD_Signal', 
           'MACD_Histogram', 'RVOL', 'VWAP', 'HV_20']
    for c in IND:
        g[c] = np.nan
    
    # Get clean Cours series
    mask = g['Cours'].notna()
    if not mask.any():
        return g
    
    pr = g.loc[mask, 'Cours']
    n = len(pr)
    
    # ─── Trend Indicators ───
    
    # SMA_20 (strict: need full window)
    if n >= min_obs['SMA_20']:
        g.loc[mask, 'SMA_20'] = pr.rolling(
            params['sma_short'],
            min_periods=params['sma_short']
        ).mean().values
    
    # SMA_50 (strict: need full window)
    if n >= min_obs['SMA_50']:
        g.loc[mask, 'SMA_50'] = pr.rolling(
            params['sma_long'],
            min_periods=params['sma_long']
        ).mean().values
    
    # EMA_20 (degrades gracefully from obs 1)
    g.loc[mask, 'EMA_20'] = pr.ewm(
        span=params['ema_short'],
        adjust=False,
        min_periods=1
    ).mean().values
    
    # ─── Momentum Indicators ───
    
    # RSI_14 (Wilder method)
    rsi = _rsi_wilder(pr.reset_index(drop=True), params['rsi_period'])
    g.loc[mask, 'RSI_14'] = rsi.values
    
    # MACD (strict: need slow EMA window)
    ema_f = pr.ewm(span=params['macd_fast'], adjust=False, min_periods=1).mean()
    ema_s = pr.ewm(span=params['macd_slow'], adjust=False, min_periods=1).mean()
    ml = ema_f - ema_s
    sig = ml.ewm(span=params['macd_signal'], adjust=False, min_periods=1).mean()
    
    if n >= min_obs['MACD']:
        g.loc[mask, 'MACD'] = ml.values
        g.loc[mask, 'MACD_Signal'] = sig.values
        g.loc[mask, 'MACD_Histogram'] = (ml - sig).values
    
    # ─── Volume Indicators ───
    
    # RVOL (relative volume)
    vm = g['Volume MC'].notna()
    if vm.any():
        vs = g.loc[vm, 'Volume MC']
        avg_v = vs.rolling(params['rvol_window'], min_periods=1).mean()
        g.loc[vm, 'RVOL'] = (vs / avg_v.replace(0, np.nan)).values
    
    # VWAP (cumulative)
    pv_price = g['Cours'].fillna(
        ((g['Bid'].fillna(0) + g['Ask'].fillna(0)) / 2).replace(0, np.nan)
    )
    both = pv_price.notna() & g['Volume MC'].notna()
    if both.any():
        pv = (pv_price * g['Volume MC']).where(both)
        cum_pv = pv.cumsum()
        cum_vol = g['Volume MC'].where(both, 0).cumsum()
        g['VWAP'] = (cum_pv / cum_vol.replace(0, np.nan)).where(cum_vol > 0)
    
    # ─── Volatility Indicators ───
    
    # HV_20 (annualized historical volatility)
    if n >= params['hv_window'] + 1:
        lr = np.log(pr / pr.shift(1))
        hv = lr.rolling(
            params['hv_window'],
            min_periods=params['hv_window']
        ).std() * np.sqrt(params['hv_annualise'])
        g.loc[mask, 'HV_20'] = hv.values
    
    return g


def add_validity_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add validity status columns for each indicator.
    
    Args:
        df: DataFrame with indicator columns
    
    Returns:
        DataFrame with Valid_{indicator} columns added
    """
    IND_COLS = ['SMA_20', 'SMA_50', 'EMA_20', 'RSI_14', 'MACD', 'MACD_Signal',
                'MACD_Histogram', 'RVOL', 'VWAP', 'HV_20']
    
    for ind in IND_COLS:
        df[f'Valid_{ind}'] = df[ind].notna().map(
            {True: 'VALID', False: 'INSUFFICIENT_DATA'}
        )
    
    return df


def compute_all_indicators(
    df: pd.DataFrame,
    params: Dict,
    min_obs: Dict
) -> pd.DataFrame:
    """
    Compute all indicators for all companies with validity tracking.
    
    Args:
        df: Input DataFrame (investable universe)
        params: INDICATOR_PARAMS from config
        min_obs: INDICATOR_MIN_OBS from config
    
    Returns:
        DataFrame with indicators and validity columns
    """
    parts = []
    
    for isin, grp in df.groupby('CODE_ISIN'):
        grp_with_ind = compute_indicators_for_company(grp, params, min_obs)
        parts.append(grp_with_ind)
    
    result = pd.concat(parts).sort_values(['CODE_ISIN', 'Date']).reset_index(drop=True)
    result = add_validity_status(result)
    
    return result
