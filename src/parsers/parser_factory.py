from enum import Enum
from typing import Callable, Optional
import pandas as pd

from .simple_sheet_parser import parse_simple_sheet


class SheetKind(str, Enum):
    MARKET_FAMILY_A = 'family_a'
    MARKET_FAMILY_B = 'family_b'
    INDEX_COMPOSITION = 'index_composition'
    UNKNOWN = 'unknown'


_INDEX_HEADER_TOKENS = {
    'séance',
    'seance',
    'indice',
    'code indice',
    'code isin',
    'instrument',
    'cours',
    'nombre de titres',
    'facteur flottant',
    'facteur de plafonnement',
    'capitalisation flottante',
    'poids',
}


def _row_tokens(df: pd.DataFrame, row_index: int) -> list[str]:
    if row_index >= len(df):
        return []
    return [str(value).strip() for value in df.iloc[row_index].tolist() if pd.notna(value) and str(value).strip()]


def _row_token_set(df: pd.DataFrame, row_index: int) -> set[str]:
    return {token.lower() for token in _row_tokens(df, row_index)}


def is_index_composition_sheet(df: pd.DataFrame) -> bool:
    """Detect normalized index-composition sheets such as MASI or Sector Indices."""
    if df.empty:
        return False

    tokens = _row_token_set(df, 0)
    hits = sum(1 for token in _INDEX_HEADER_TOKENS if token in tokens)
    return hits >= 5


def detect_sheet_family(df: pd.DataFrame) -> SheetKind:
    """Detect whether a worksheet is Family A, Family B, index composition, or unknown.

    Family A sheets are raw market sheets with one value per company per date.
    Family B sheets are block-based, multi-attribute sheets such as Data.
    Index-composition sheets are already normalized and must stay outside the market normalization path.
    """
    if df.empty:
        return SheetKind.UNKNOWN

    if is_index_composition_sheet(df):
        return SheetKind.INDEX_COMPOSITION

    head = df.iloc[:8, :].astype(str).fillna('')
    flattened = ' '.join(head.iloc[:3].astype(str).fillna('').to_numpy().flatten()).lower()
    has_code_isin = 'code isin' in flattened
    has_libelle = 'libelle' in flattened

    if not (has_code_isin and has_libelle):
        return SheetKind.UNKNOWN

    metadata_row_index = 5 if len(df) > 5 else len(df) - 1
    row_values = [value for value in _row_tokens(df, metadata_row_index) if value.lower() not in {'code amc', 'code isin', 'libelle'}]
    distinct_count = len({value.lower() for value in row_values})

    if distinct_count <= 2:
        return SheetKind.MARKET_FAMILY_A
    return SheetKind.MARKET_FAMILY_B


def get_parser_for_sheet(df: pd.DataFrame) -> Optional[Callable[[str, str], pd.DataFrame]]:
    family = detect_sheet_family(df)
    if family == SheetKind.MARKET_FAMILY_A:
        return parse_simple_sheet
    return None
