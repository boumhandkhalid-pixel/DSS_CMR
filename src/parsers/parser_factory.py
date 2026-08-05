from typing import Callable
import pandas as pd

from .simple_sheet_parser import parse_simple_sheet
from .data_sheet_parser import parse_data_sheet


def detect_sheet_family(df: pd.DataFrame) -> str:
    """Detect sheet family based on content heuristics.

    Returns 'A' for single-value cross-tab sheets and 'B' for multi-attribute sheets.
    """
    head = df.iloc[:8, :].astype(str).fillna("")

    # Heuristic A: presence of CODE ISIN in first rows -> Family A
    if head.apply(lambda col: col.str.contains('CODE ISIN', case=False).any()).any():
        return 'A'

    # Heuristic B: first column contains many uppercase variable names (e.g. VWAP, HVOLA)
    first_col = head.iloc[:, 0].str.strip()
    uppercase_hits = first_col.str.match(r'^[A-Z0-9\- _/]+$').sum()
    if uppercase_hits >= 3:
        return 'B'

    # Default to A
    return 'A'


def get_parser_for_sheet(df: pd.DataFrame) -> Callable[[str, str], pd.DataFrame]:
    family = detect_sheet_family(df)
    if family == 'A':
        return parse_simple_sheet
    return parse_data_sheet
