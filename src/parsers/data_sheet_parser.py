import pandas as pd
from typing import List


def parse_data_sheet(path: str, sheet_name: str) -> pd.DataFrame:
    """Parse Family B data sheets where rows are variables and columns are companies.

    Returns a long DataFrame with columns: `Date` (optional), `CODE_ISIN`, `Company`, `Variable`, `Value`.
    """
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)

    # Locate CODE ISIN row if present (commonly near top)
    code_row = None
    lib_row = None
    for i in range(min(8, len(raw))):
        row_values = raw.iloc[i].astype(str).str.upper()
        if row_values.str.contains('CODE ISIN').any():
            code_row = i
        if row_values.str.contains('LIBELLE').any():
            lib_row = i
    if code_row is None:
        # attempt to detect by pattern: cells that look like ISIN (MA...)
        for i in range(8):
            if raw.shape[1] > 1 and raw.iloc[i, 1].astype(str).str.startswith('MA').any():
                code_row = i
                break

    # company columns start at 1 (col 0 typically is variable name)
    company_cols = list(range(1, raw.shape[1]))

    # extract code_isin and company names
    codes: List[str] = []
    names: List[str] = []
    for col in company_cols:
        code = raw.iat[code_row, col] if code_row is not None else None
        name = raw.iat[lib_row, col] if lib_row is not None else None
        codes.append(str(code).strip() if pd.notna(code) else '')
        names.append(str(name).strip() if pd.notna(name) else '')

    records = []
    # variable rows typically start after the top metadata block; detect where first column contains variable names
    for i in range(len(raw)):
        var = raw.iat[i, 0]
        if pd.isna(var):
            continue
        var_str = str(var).strip()
        # skip metadata label rows
        if var_str.upper() in ('CODE ISIN', 'LIBELLE', 'CODE AMC'):
            continue
        # treat this as a variable row
        for j, col in enumerate(company_cols):
            val = raw.iat[i, col]
            records.append({
                'Date': pd.NaT,
                'CODE_ISIN': codes[j],
                'Company': names[j] or codes[j],
                'Variable': var_str,
                'Value': val,
            })

    return pd.DataFrame.from_records(records)
