"""Market metrics computation module for unified dataset."""

from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np


class MetricsWarning:
    """Container for metric computation warnings."""
    
    def __init__(self, metric_name: str, message: str):
        self.metric_name = metric_name
        self.message = message
    
    def __repr__(self):
        return f"⚠ {self.metric_name}: {self.message}"


def compute_average_volume(df: pd.DataFrame) -> Tuple[Optional[pd.Series], Optional[MetricsWarning]]:
    """
    Compute average trading volume (Volume MC) for each company.
    
    Args:
        df: Unified dataset with Date and CODE_ISIN columns
    
    Returns:
        (Series indexed by CODE_ISIN with avg volumes, warning if applicable)
    """
    if 'Volume MC' not in df.columns:
        warning = MetricsWarning('Average Volume', 'Volume MC column not available')
        return None, warning
    
    # Group by company and compute mean volume
    avg_volume = df.groupby('CODE_ISIN')['Volume MC'].mean()
    
    # Check data quality
    all_na = avg_volume.isna().sum()
    if all_na > 0:
        warning = MetricsWarning(
            'Average Volume',
            f'{all_na}/{len(avg_volume)} companies have no volume data'
        )
        return avg_volume, warning
    
    return avg_volume, None


def compute_liquidity_proxy(df: pd.DataFrame) -> Tuple[Optional[pd.Series], Optional[MetricsWarning]]:
    """
    Compute liquidity proxy as (Average Volume × Average Price).
    
    This is a proxy measure for liquidity. Actual liquidity would require
    market value of shares traded, which is not available in the raw data.
    
    Higher values indicate more liquid securities.
    
    Args:
        df: Unified dataset with Volume MC and Cours columns
    
    Returns:
        (Series indexed by CODE_ISIN with liquidity proxies, warning if applicable)
    """
    if 'Volume MC' not in df.columns or 'Cours' not in df.columns:
        warning = MetricsWarning(
            'Liquidity Proxy',
            'Volume MC or Cours column not available'
        )
        return None, warning
    
    # Group by company
    grouped = df.groupby('CODE_ISIN')
    avg_volume = grouped['Volume MC'].mean()
    avg_price = grouped['Cours'].mean()
    
    # Compute liquidity proxy
    liquidity = avg_volume * avg_price
    
    # Check data quality
    incomplete = liquidity.isna().sum()
    if incomplete > 0:
        warning = MetricsWarning(
            'Liquidity Proxy',
            f'{incomplete}/{len(liquidity)} companies have incomplete data'
        )
        return liquidity, warning
    
    return liquidity, None


def compute_bid_ask_spreads(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[MetricsWarning]]:
    """
    Compute Bid-Ask spread statistics for each company.
    
    Tighter spreads indicate more liquid securities.
    
    Args:
        df: Unified dataset with Bid and Ask columns
    
    Returns:
        (DataFrame with spread stats, warning if applicable)
    """
    if 'Bid' not in df.columns or 'Ask' not in df.columns:
        warning = MetricsWarning('Bid-Ask Spreads', 'Bid or Ask column not available')
        return None, warning
    
    # Filter rows with both Bid and Ask
    df_valid = df[(df['Bid'].notna()) & (df['Ask'].notna())].copy()
    
    if len(df_valid) == 0:
        warning = MetricsWarning('Bid-Ask Spreads', 'No rows with both Bid and Ask prices')
        return None, warning
    
    # Compute spreads
    df_valid['Spread'] = df_valid['Ask'] - df_valid['Bid']
    df_valid['Spread_Pct'] = (df_valid['Spread'] / df_valid['Bid']) * 100
    
    # Group by company
    spread_stats = df_valid.groupby('CODE_ISIN').agg({
        'Spread': ['mean', 'min', 'max', 'std'],
        'Spread_Pct': ['mean', 'std']
    }).round(4)
    
    # Flatten column names
    spread_stats.columns = [
        'Avg_Spread',
        'Min_Spread', 
        'Max_Spread',
        'Std_Spread',
        'Avg_Spread_Pct',
        'Std_Spread_Pct'
    ]
    
    return spread_stats, None


def compute_trading_coverage(df: pd.DataFrame) -> Tuple[Optional[pd.Series], Optional[MetricsWarning]]:
    """
    Compute what percentage of trading sessions have volume data for each company.
    
    High coverage indicates actively traded/liquid securities.
    
    Args:
        df: Unified dataset with Volume MC column
    
    Returns:
        (Series indexed by CODE_ISIN with coverage %, warning if applicable)
    """
    if 'Volume MC' not in df.columns:
        warning = MetricsWarning('Trading Coverage', 'Volume MC column not available')
        return None, warning
    
    # Count trading days with volume for each company
    def coverage_pct(group):
        total = len(group)
        trading_days = group['Volume MC'].notna().sum()
        return (trading_days / total * 100) if total > 0 else 0
    
    coverage = df.groupby('CODE_ISIN').apply(coverage_pct)
    
    return coverage, None


def compute_volatility_proxy(df: pd.DataFrame) -> Tuple[Optional[pd.Series], Optional[MetricsWarning]]:
    """
    Compute price volatility as coefficient of variation (std / mean) of close prices.
    
    This is a simple volatility measure. More sophisticated measures (historical vol)
    will be computed in technical indicators phase.
    
    Args:
        df: Unified dataset with Cours column
    
    Returns:
        (Series indexed by CODE_ISIN with volatility proxies, warning if applicable)
    """
    if 'Cours' not in df.columns:
        warning = MetricsWarning('Volatility Proxy', 'Cours column not available')
        return None, warning
    
    def coeff_variation(group):
        prices = group['Cours'].dropna()
        if len(prices) < 2:
            return np.nan
        mean_price = prices.mean()
        if mean_price == 0:
            return np.nan
        return (prices.std() / mean_price) * 100
    
    volatility = df.groupby('CODE_ISIN').apply(coeff_variation)
    
    # Check data quality
    all_na = volatility.isna().sum()
    if all_na > 0:
        warning = MetricsWarning(
            'Volatility Proxy',
            f'{all_na}/{len(volatility)} companies have insufficient price data'
        )
        return volatility, warning
    
    return volatility, None


def compute_all_metrics(df: pd.DataFrame, verbose: bool = True) -> Tuple[pd.DataFrame, Dict]:
    """
    Compute all available market metrics and merge into unified dataset.
    
    This function computes metrics that can be derived from market data alone.
    Metrics requiring index composition data (capitalization, free float) are
    deferred to the filtering stage.
    
    Args:
        df: Unified dataset
        verbose: Print progress messages
    
    Returns:
        (Enhanced dataset with metrics columns, report dict with warnings)
    """
    report = {
        'metrics_computed': [],
        'metrics_skipped': [],
        'warnings': []
    }
    
    # Start with enhanced copy
    df_enhanced = df.copy()
    
    if verbose:
        print('Computing market metrics...\n')
    
    # 1. Average Volume
    if verbose:
        print('1. Average Volume (Volume MC)')
    avg_vol, warning = compute_average_volume(df)
    if avg_vol is not None:
        df_enhanced['Avg_Volume_MC'] = df['CODE_ISIN'].map(avg_vol)
        report['metrics_computed'].append('Avg_Volume_MC')
        if verbose:
            print(f'   ✓ {len(avg_vol)} companies')
    else:
        report['metrics_skipped'].append('Avg_Volume_MC')
        if verbose:
            print(f'   ✗ Skipped')
    if warning:
        report['warnings'].append(warning)
        if verbose:
            print(f'   {warning}')
    
    # 2. Liquidity Proxy
    if verbose:
        print('\n2. Liquidity Proxy (Volume × Price)')
    liquidity, warning = compute_liquidity_proxy(df)
    if liquidity is not None:
        df_enhanced['Liquidity_Proxy'] = df['CODE_ISIN'].map(liquidity)
        report['metrics_computed'].append('Liquidity_Proxy')
        if verbose:
            print(f'   ✓ {len(liquidity)} companies')
    else:
        report['metrics_skipped'].append('Liquidity_Proxy')
        if verbose:
            print(f'   ✗ Skipped')
    if warning:
        report['warnings'].append(warning)
        if verbose:
            print(f'   {warning}')
    
    # 3. Bid-Ask Spreads
    if verbose:
        print('\n3. Bid-Ask Spread Statistics')
    spreads, warning = compute_bid_ask_spreads(df)
    if spreads is not None:
        # Merge spread stats
        for col in spreads.columns:
            df_enhanced[col] = df['CODE_ISIN'].map(spreads[col])
        report['metrics_computed'].extend(list(spreads.columns))
        if verbose:
            print(f'   ✓ {len(spreads)} companies')
    else:
        report['metrics_skipped'].append('Bid-Ask_Spreads')
        if verbose:
            print(f'   ✗ Skipped')
    if warning:
        report['warnings'].append(warning)
        if verbose:
            print(f'   {warning}')
    
    # 4. Trading Coverage
    if verbose:
        print('\n4. Trading Coverage (%)')
    coverage, warning = compute_trading_coverage(df)
    if coverage is not None:
        df_enhanced['Trading_Coverage_Pct'] = df['CODE_ISIN'].map(coverage)
        report['metrics_computed'].append('Trading_Coverage_Pct')
        if verbose:
            print(f'   ✓ Coverage computed')
    else:
        report['metrics_skipped'].append('Trading_Coverage_Pct')
        if verbose:
            print(f'   ✗ Skipped')
    if warning:
        report['warnings'].append(warning)
        if verbose:
            print(f'   {warning}')
    
    # 5. Volatility Proxy
    if verbose:
        print('\n5. Volatility Proxy (Coefficient of Variation)')
    volatility, warning = compute_volatility_proxy(df)
    if volatility is not None:
        df_enhanced['Volatility_Proxy_Pct'] = df['CODE_ISIN'].map(volatility)
        report['metrics_computed'].append('Volatility_Proxy_Pct')
        if verbose:
            print(f'   ✓ Volatility proxy computed')
    else:
        report['metrics_skipped'].append('Volatility_Proxy_Pct')
        if verbose:
            print(f'   ✗ Skipped')
    if warning:
        report['warnings'].append(warning)
        if verbose:
            print(f'   {warning}')
    
    if verbose:
        print(f'\n✓ Metrics computation complete')
        print(f'  Computed: {len(report["metrics_computed"])} metrics')
        print(f'  Skipped: {len(report["metrics_skipped"])} metrics')
        if report['warnings']:
            print(f'  Warnings: {len(report["warnings"])}')
    
    return df_enhanced, report


def get_metrics_summary(df_enhanced: pd.DataFrame) -> pd.DataFrame:
    """
    Get summary statistics for each company's metrics.
    
    Args:
        df_enhanced: Dataset with metrics columns
    
    Returns:
        DataFrame with company names and metric values (one row per company)
    """
    # Identify metric columns
    metric_cols = [
        c for c in df_enhanced.columns 
        if c in [
            'Avg_Volume_MC', 'Liquidity_Proxy', 'Trading_Coverage_Pct',
            'Volatility_Proxy_Pct', 'Avg_Spread', 'Avg_Spread_Pct'
        ]
    ]
    
    if not metric_cols:
        return pd.DataFrame()
    
    # Get unique company-CODE_ISIN mapping
    company_map = df_enhanced[['CODE_ISIN', 'Company']].drop_duplicates().set_index('CODE_ISIN')
    
    # Get metrics (one per company)
    metrics_summary = df_enhanced[['CODE_ISIN'] + metric_cols].drop_duplicates(subset=['CODE_ISIN'])
    metrics_summary = metrics_summary.set_index('CODE_ISIN')
    
    # Add company names
    metrics_summary = metrics_summary.join(company_map)
    
    # Reorder: Company first
    cols = ['Company'] + [c for c in metrics_summary.columns if c != 'Company']
    metrics_summary = metrics_summary[[c for c in cols if c in metrics_summary.columns]]
    
    return metrics_summary
