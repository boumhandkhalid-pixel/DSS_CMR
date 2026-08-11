"""Data quality validation functions for unified market dataset."""

from typing import Dict, List, Tuple
import pandas as pd


class ValidationResult:
    """Container for validation test results."""
    
    def __init__(self, name: str, passed: bool, severity: str, message: str = None, details: dict = None):
        self.name = name
        self.passed = passed
        self.severity = severity  # 'critical', 'warning', 'info'
        self.message = message or ''
        self.details = details or {}
    
    def __repr__(self):
        status = '✓' if self.passed else ('⚠' if self.severity == 'warning' else '✗')
        return f"{status} [{self.severity:8s}] {self.name}: {self.message}"


def validate_schema(df: pd.DataFrame) -> List[ValidationResult]:
    """Validate dataset schema and structure."""
    results = []
    
    # Check for required columns
    required_cols = {'Date', 'CODE_ISIN', 'Company', 'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
    actual_cols = set(df.columns)
    missing = required_cols - actual_cols
    
    if missing:
        results.append(ValidationResult(
            name='Schema - Missing Columns',
            passed=False,
            severity='critical',
            message=f"Missing columns: {missing}",
            details={'missing': list(missing)}
        ))
    else:
        results.append(ValidationResult(
            name='Schema - All Columns',
            passed=True,
            severity='info',
            message='All required columns present'
        ))
    
    # Check data types
    expected_types = {
        'Date': 'datetime64[ns]',
        'CODE_ISIN': 'object',
        'Company': 'object',
    }
    
    type_errors = []
    for col, expected in expected_types.items():
        if col in df.columns and str(df[col].dtype) != expected:
            type_errors.append(f"{col}: got {df[col].dtype}, expected {expected}")
    
    if type_errors:
        results.append(ValidationResult(
            name='Schema - Data Types',
            passed=False,
            severity='warning',
            message='; '.join(type_errors)
        ))
    else:
        results.append(ValidationResult(
            name='Schema - Data Types',
            passed=True,
            severity='info',
            message='All data types correct'
        ))
    
    return results


def validate_grain(df: pd.DataFrame) -> List[ValidationResult]:
    """Validate that grain is (Date, CODE_ISIN)."""
    results = []
    
    grain = ['Date', 'CODE_ISIN']
    duplicates = df[grain].duplicated().sum()
    
    if duplicates > 0:
        results.append(ValidationResult(
            name='Grain - Uniqueness',
            passed=False,
            severity='critical',
            message=f"{duplicates} duplicate (Date, CODE_ISIN) combinations found",
            details={'duplicate_count': duplicates}
        ))
    else:
        results.append(ValidationResult(
            name='Grain - Uniqueness',
            passed=True,
            severity='info',
            message='Each (Date, CODE_ISIN) combination is unique'
        ))
    
    return results


def validate_identifiers(df: pd.DataFrame) -> List[ValidationResult]:
    """Validate identifier columns (CODE_ISIN, Company)."""
    results = []
    
    # CODE_ISIN validation
    null_isins = df['CODE_ISIN'].isna().sum()
    empty_isins = (df['CODE_ISIN'] == '').sum()
    
    if null_isins > 0 or empty_isins > 0:
        results.append(ValidationResult(
            name='Identifiers - CODE_ISIN Null/Empty',
            passed=False,
            severity='critical',
            message=f"{null_isins} null, {empty_isins} empty CODE_ISIN values",
            details={'null_count': null_isins, 'empty_count': empty_isins}
        ))
    else:
        results.append(ValidationResult(
            name='Identifiers - CODE_ISIN Null/Empty',
            passed=True,
            severity='info',
            message='No null or empty CODE_ISIN values'
        ))
    
    # ISIN format validation
    valid_isins = df['CODE_ISIN'].str.startswith('MA', na=False).sum()
    total_isins = df['CODE_ISIN'].notna().sum()
    invalid_count = total_isins - valid_isins
    
    if invalid_count > 0:
        results.append(ValidationResult(
            name='Identifiers - ISIN Format',
            passed=False,
            severity='warning',
            message=f"{invalid_count}/{total_isins} ISINs don't start with 'MA'",
            details={'invalid_count': invalid_count, 'total': total_isins}
        ))
    else:
        results.append(ValidationResult(
            name='Identifiers - ISIN Format',
            passed=True,
            severity='info',
            message='All ISINs start with MA (valid format)'
        ))
    
    # Company name consistency
    isin_to_companies = df.groupby('CODE_ISIN')['Company'].nunique()
    inconsistent = (isin_to_companies > 1).sum()
    
    if inconsistent > 0:
        results.append(ValidationResult(
            name='Identifiers - Company Consistency',
            passed=False,
            severity='warning',
            message=f"{inconsistent} ISINs have multiple company names",
            details={'inconsistent_count': inconsistent}
        ))
    else:
        results.append(ValidationResult(
            name='Identifiers - Company Consistency',
            passed=True,
            severity='info',
            message='Each ISIN maps to exactly one company name'
        ))
    
    return results


def validate_dates(df: pd.DataFrame) -> List[ValidationResult]:
    """Validate date column."""
    results = []
    
    null_dates = df['Date'].isna().sum()
    
    if null_dates > 0:
        results.append(ValidationResult(
            name='Dates - Null Values',
            passed=False,
            severity='critical',
            message=f"{null_dates} null dates found",
            details={'null_count': null_dates}
        ))
    else:
        results.append(ValidationResult(
            name='Dates - Null Values',
            passed=True,
            severity='info',
            message='No null dates'
        ))
    
    # Date range
    if df['Date'].notna().sum() > 0:
        date_min = df['Date'].min()
        date_max = df['Date'].max()
        span = (date_max - date_min).days
        
        results.append(ValidationResult(
            name='Dates - Range',
            passed=True,
            severity='info',
            message=f"Date range: {date_min.date()} to {date_max.date()} ({span} days)",
            details={'min_date': str(date_min), 'max_date': str(date_max), 'span_days': span}
        ))
    
    return results


def validate_prices(df: pd.DataFrame) -> List[ValidationResult]:
    """Validate price columns (Cours, Bid, Ask)."""
    results = []
    
    price_cols = ['Cours', 'Bid', 'Ask']
    
    # Check for negative prices
    for col in price_cols:
        negatives = (df[col] < 0).sum()
        if negatives > 0:
            results.append(ValidationResult(
                name=f'Prices - {col} Negative',
                passed=False,
                severity='warning',
                message=f"{negatives} negative {col} values found",
                details={'negative_count': negatives}
            ))
    
    # Check Bid <= Ask relationship
    both_present = df[(df['Bid'].notna()) & (df['Ask'].notna())]
    if len(both_present) > 0:
        inverted = (both_present['Bid'] > both_present['Ask']).sum()
        if inverted > 0:
            results.append(ValidationResult(
                name='Prices - Bid-Ask Spread',
                passed=False,
                severity='warning',
                message=f"{inverted}/{len(both_present)} rows have Bid > Ask",
                details={'inverted_count': inverted, 'total': len(both_present)}
            ))
        else:
            results.append(ValidationResult(
                name='Prices - Bid-Ask Spread',
                passed=True,
                severity='info',
                message=f'All {len(both_present)} rows have Bid <= Ask'
            ))
    
    # Check for zero prices
    zero_prices = ((df['Cours'] == 0) | (df['Bid'] == 0) | (df['Ask'] == 0)).sum()
    if zero_prices > 0:
        results.append(ValidationResult(
            name='Prices - Zero Values',
            passed=False,
            severity='warning',
            message=f"{zero_prices} rows have zero prices",
            details={'zero_count': zero_prices}
        ))
    
    # Null percentage
    for col in price_cols:
        null_pct = df[col].isna().mean() * 100
        if null_pct > 50:
            results.append(ValidationResult(
                name=f'Prices - {col} Coverage',
                passed=False,
                severity='warning',
                message=f"{null_pct:.1f}% null {col} values",
                details={'null_percentage': null_pct}
            ))
        else:
            results.append(ValidationResult(
                name=f'Prices - {col} Coverage',
                passed=True,
                severity='info',
                message=f"{100-null_pct:.1f}% data coverage"
            ))
    
    return results


def validate_volumes(df: pd.DataFrame) -> List[ValidationResult]:
    """Validate volume columns."""
    results = []
    
    volume_cols = ['Volume MC', 'Quantité MC']
    
    for col in volume_cols:
        # Check for negative volumes
        negatives = (df[col] < 0).sum()
        if negatives > 0:
            results.append(ValidationResult(
                name=f'Volumes - {col} Negative',
                passed=False,
                severity='warning',
                message=f"{negatives} negative {col} values",
                details={'negative_count': negatives}
            ))
        
        # Check null percentage
        null_pct = df[col].isna().mean() * 100
        if null_pct > 70:
            results.append(ValidationResult(
                name=f'Volumes - {col} Coverage',
                passed=False,
                severity='info',
                message=f"{null_pct:.1f}% null (common for illiquid securities)",
                details={'null_percentage': null_pct}
            ))
    
    return results


def validate_consistency(df: pd.DataFrame) -> List[ValidationResult]:
    """Validate cross-dataset consistency."""
    results = []
    
    # Check that all dates have complete company coverage
    records_per_date = df.groupby('Date').size()
    companies_per_date = df.groupby('Date')['CODE_ISIN'].nunique()
    
    max_companies = companies_per_date.max()
    min_companies = companies_per_date.min()
    
    if min_companies < max_companies:
        incomplete_dates = (companies_per_date < max_companies).sum()
        results.append(ValidationResult(
            name='Consistency - Date Coverage',
            passed=False,
            severity='warning',
            message=f"{incomplete_dates} dates have < {max_companies} companies",
            details={'incomplete_dates': incomplete_dates, 'max_companies': max_companies}
        ))
    else:
        results.append(ValidationResult(
            name='Consistency - Date Coverage',
            passed=True,
            severity='info',
            message=f"All dates have {max_companies} companies"
        ))
    
    # Check for rows with all nulls
    price_cols = ['Cours', 'Bid', 'Ask']
    all_null_rows = df[price_cols].isna().all(axis=1).sum()
    
    if all_null_rows > 0:
        results.append(ValidationResult(
            name='Consistency - All-Null Rows',
            passed=False,
            severity='warning',
            message=f"{all_null_rows} rows have all price columns null",
            details={'null_row_count': all_null_rows}
        ))
    
    return results


def validate_dataset(df: pd.DataFrame, verbose: bool = False) -> Tuple[bool, Dict]:
    """Run all validation checks on unified dataset.
    
    Args:
        df: Unified market dataset
        verbose: Print results
    
    Returns:
        (all_passed, validation_report)
    """
    validation_checks = [
        ('Schema', validate_schema),
        ('Grain', validate_grain),
        ('Identifiers', validate_identifiers),
        ('Dates', validate_dates),
        ('Prices', validate_prices),
        ('Volumes', validate_volumes),
        ('Consistency', validate_consistency),
    ]
    
    report = {
        'total_tests': 0,
        'passed': 0,
        'warnings': 0,
        'critical': 0,
        'by_category': {},
        'results': []
    }
    
    for category, check_func in validation_checks:
        results = check_func(df)
        report['by_category'][category] = results
        
        for result in results:
            report['total_tests'] += 1
            
            if result.passed:
                report['passed'] += 1
            
            if result.severity == 'warning':
                report['warnings'] += 1
            elif result.severity == 'critical':
                report['critical'] += 1
            
            report['results'].append(result)
    
    all_passed = report['critical'] == 0
    
    if verbose:
        print('\n' + '='*70)
        print('DATA QUALITY VALIDATION REPORT')
        print('='*70)
        
        for category, results in report['by_category'].items():
            print(f'\n{category.upper()}')
            print('-' * 70)
            for result in results:
                print(f'  {result}')
        
        print(f'\n' + '='*70)
        print(f'SUMMARY: {report["passed"]}/{report["total_tests"]} passed | '
              f'{report["warnings"]} warnings | {report["critical"]} critical')
        print('='*70)
    
    return all_passed, report


def filter_companies_by_usable_data(
    df: pd.DataFrame,
    min_consecutive: int = 14,
    key_column: str = 'Cours',
    max_gap_days: int = 7,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Filter out companies that do not have enough CONSECUTIVE observations
    in key_column to compute technical indicators reliably.

    Why consecutive, not just count?
    ---------------------------------
    RSI, SMA, EMA etc. operate on price *differences* across adjacent rows.
    If two price rows are separated by a multi-month gap (e.g. 2019 data then
    2024 data), the delta between them is not a daily return — it is a
    multi-year move compressed into one step.  The indicator still produces
    a number, but that number has no financial meaning.

    Rule: a company is KEPT only if it has at least `min_consecutive`
    non-null key_column values with no gap larger than `max_gap_days`
    between consecutive observations.

    Args:
        df: Unified dataset (must have 'Date', 'CODE_ISIN', key_column)
        min_consecutive: Minimum length of the longest unbroken price run
                         (default 14 — RSI_14 binding constraint)
        key_column: Column to check (default 'Cours')
        max_gap_days: Maximum calendar days between two consecutive
                      non-null observations to be considered part of the
                      same run (default 7, covers weekends + public holidays)

    Returns:
        (filtered_df, removal_report)
    """
    removal_report = {
        'total_rows_before': len(df),
        'total_companies_before': df['CODE_ISIN'].nunique(),
        'removed_companies': [],
        'removed_rows': 0,
        'min_consecutive': min_consecutive,
        'max_gap_days': max_gap_days,
        'key_column': key_column,
    }

    valid_isins = []

    for isin in sorted(df['CODE_ISIN'].unique()):
        company_df = df[df['CODE_ISIN'] == isin].sort_values('Date')
        company_name = company_df['Company'].iloc[0]
        total_rows = len(company_df)

        # Dates where key_column is non-null, sorted ascending
        valid_dates = company_df[company_df[key_column].notna()]['Date'].sort_values()
        n_valid = len(valid_dates)

        if n_valid == 0:
            max_run = 0
        else:
            # Walk through valid dates and find the longest unbroken run
            max_run = current_run = 1
            for i in range(1, n_valid):
                gap = (valid_dates.iloc[i] - valid_dates.iloc[i - 1]).days
                if gap <= max_gap_days:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 1

        if max_run >= min_consecutive:
            valid_isins.append(isin)
        else:
            removal_report['removed_companies'].append({
                'CODE_ISIN': isin,
                'Company': company_name,
                'Total_Rows': total_rows,
                'Valid_Obs': n_valid,
                'Max_Consecutive_Run': max_run,
                'Required': min_consecutive,
                'Reason': (
                    f'Longest consecutive {key_column} run = {max_run} '
                    f'(need >= {min_consecutive})'
                ),
            })
            removal_report['removed_rows'] += total_rows

    filtered_df = (
        df[df['CODE_ISIN'].isin(valid_isins)]
        .copy()
        .reset_index(drop=True)
    )

    removal_report.update({
        'total_rows_after': len(filtered_df),
        'total_companies_after': filtered_df['CODE_ISIN'].nunique(),
        'companies_retained': len(valid_isins),
        'companies_removed': len(removal_report['removed_companies']),
        'rows_retained': len(filtered_df),
        'rows_removed': removal_report['removed_rows'],
    })

    return filtered_df, removal_report


def save_unified_dataset(df: pd.DataFrame, output_path: str, compression: str = 'snappy') -> Dict:
    """
    Save unified dataset to Parquet format.
    
    Parquet advantages:
    - Columnar format (fast queries)
    - Compression (smaller file size)
    - Schema preservation (type safety)
    - Efficient for downstream processing
    
    Args:
        df: Unified dataset to save
        output_path: Path to save parquet file (e.g., 'data/unified_dataset.parquet')
        compression: Compression method ('snappy', 'gzip', 'brotli', 'lz4', 'zstd')
    
    Returns:
        save_report: Dict with save operation details
    """
    from pathlib import Path
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    save_report = {
        'success': False,
        'path': str(output_path),
        'file_size_bytes': 0,
        'rows': len(df),
        'columns': len(df.columns),
        'compression': compression,
        'error': None
    }
    
    try:
        df.to_parquet(output_path, compression=compression, index=False)
        
        file_size = output_path.stat().st_size
        save_report['success'] = True
        save_report['file_size_bytes'] = file_size
        save_report['file_size_mb'] = file_size / 1024 / 1024
        
    except Exception as e:
        save_report['error'] = str(e)
    
    return save_report


def load_unified_dataset(input_path: str) -> Tuple[pd.DataFrame, Dict]:
    """
    Load unified dataset from Parquet format.
    
    Args:
        input_path: Path to parquet file
    
    Returns:
        (df, load_report)
    """
    from pathlib import Path
    
    input_path = Path(input_path)
    
    load_report = {
        'success': False,
        'path': str(input_path),
        'rows': 0,
        'columns': 0,
        'columns_list': [],
        'dtypes': {},
        'error': None
    }
    
    try:
        df = pd.read_parquet(input_path)
        
        load_report['success'] = True
        load_report['rows'] = len(df)
        load_report['columns'] = len(df.columns)
        load_report['columns_list'] = list(df.columns)
        load_report['dtypes'] = {col: str(df[col].dtype) for col in df.columns}
        
    except Exception as e:
        load_report['error'] = str(e)
        df = None
    
    return df, load_report
