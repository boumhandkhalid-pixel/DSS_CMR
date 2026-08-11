from typing import Optional
import pandas as pd


def _find_row_with_value(df: pd.DataFrame, value_substr: str) -> Optional[int]:
    value_substr = value_substr.lower()
    for i in range(min(8, len(df))):
        row = df.iloc[i].astype(str).str.lower()
        if row.str.contains(value_substr).any():
            return i
    return None


def parse_simple_sheet(path: str, sheet_name: str) -> pd.DataFrame:
    """Parse Family A sheets (one value per company × date).

    Returns a long DataFrame with columns: `Date`, `CODE_ISIN`, `Company`, `Variable`, `Value`.
    """
    from src.parsers.parser_factory import normalize_sheet_name
    
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)

    # detect CODE ISIN row
    code_row = _find_row_with_value(raw, 'CODE ISIN')
    lib_row = _find_row_with_value(raw, 'LIBELLE')

    # fallback: use next row
    if code_row is None:
        raise ValueError(f'CODE ISIN row not found in sheet {sheet_name}')

    if lib_row is None:
        lib_row = code_row + 1 if code_row + 1 < len(raw) else code_row

    # detect data start by finding first row where first column is a date
    data_start = None
    for i in range(code_row + 1, len(raw)):
        first = raw.iat[i, 0]
        try:
            if pd.notna(first) and pd.to_datetime(first, errors='coerce') is not pd.NaT:
                data_start = i
                break
        except Exception:
            continue

    if data_start is None:
        # as fallback, assume data starts at lib_row + 1
        data_start = lib_row + 1

    # Build mapping for company columns
    companies = []  # list of tuples (col_idx, code_isin, company_name)
    for col in range(1, raw.shape[1]):
        code = raw.iat[code_row, col]
        name = raw.iat[lib_row, col]
        if pd.isna(code) and pd.isna(name):
            continue
        companies.append((col, str(code).strip() if pd.notna(code) else '', str(name).strip() if pd.notna(name) else ''))

    # Normalize variable name using semantic patterns
    canonical_variable = normalize_sheet_name(sheet_name)

    records = []
    for row_idx in range(data_start, len(raw)):
        date = raw.iat[row_idx, 0]
        for col, code, name in companies:
            val = raw.iat[row_idx, col]
            records.append({
                'Date': pd.to_datetime(date, errors='coerce') if pd.notna(date) else pd.NaT,
                'CODE_ISIN': code,
                'Company': name or code,
                'Variable': canonical_variable,  # Use normalized name
                'Value': val,
            })

    return pd.DataFrame.from_records(records)
