import pandas as pd
from typing import List


def merge_long_tables(tables: List[pd.DataFrame]) -> pd.DataFrame:
    """Merge multiple long-format tables (Date, CODE_ISIN, Company, Variable, Value)
    into a single wide DataFrame indexed by Date and CODE_ISIN with variables as columns.
    """
    if not tables:
        return pd.DataFrame()

    # concat all and pivot
    concat = pd.concat(tables, ignore_index=True)
    # ensure Date is datetime
    if 'Date' in concat.columns:
        concat['Date'] = pd.to_datetime(concat['Date'], errors='coerce')

    pivot = (
        concat
        .dropna(subset=['CODE_ISIN'])
        .pivot_table(index=['Date', 'CODE_ISIN', 'Company'], columns='Variable', values='Value', aggfunc='first')
        .reset_index()
    )
    # flatten columns
    pivot.columns.name = None
    return pivot
