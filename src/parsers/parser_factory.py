from enum import Enum
from typing import Callable, Optional, Tuple
import pandas as pd
import re

from .simple_sheet_parser import parse_simple_sheet


class SheetKind(str, Enum):
    MARKET_FAMILY_A = 'family_a'
    MARKET_FAMILY_B = 'family_b'
    INDEX_COMPOSITION = 'index_composition'
    UNKNOWN = 'unknown'


# Semantic mapping for known market variable patterns
# Maps sheet name patterns to canonical variable names
_MARKET_VARIABLE_PATTERNS = {
    # Closing price patterns
    r'cours|close|closing|cloture|clôture': 'Cours',
    # Bid patterns
    r'bid|achat|demande': 'Bid',
    # Ask patterns  
    r'ask|vente|offre': 'Ask',
    # Volume patterns
    r'volume.*mc|volume.*marche|volume.*marché|volume.*market|^volume$': 'Volume MC',
    # Quantity patterns
    r'quantit[eé].*mc|quantit[eé].*marche|quantit[eé].*marché|quantity.*market|^quantit[eé]$': 'Quantité MC',
    # Price patterns (fallback)
    r'^price|^prix': 'Price',
}


def normalize_sheet_name(sheet_name: str) -> str:
    """Normalize sheet name to canonical variable name using semantic patterns.
    
    This handles cases where sheets may be named inconsistently:
    - "Cours" or "cours" or "COURS" -> "Cours"
    - "volume mc" or "Volume MC" or "VOLUME_MC" -> "Volume MC"
    - Unknown patterns -> return original name (titlecased)
    """
    if not sheet_name:
        return "Unknown"
    
    # Normalize to lowercase for pattern matching
    name_lower = sheet_name.lower().strip()
    
    # Try to match against known patterns
    for pattern, canonical_name in _MARKET_VARIABLE_PATTERNS.items():
        if re.search(pattern, name_lower):
            return canonical_name
    
    # If no match, return titlecased original
    return sheet_name.strip().title()


def infer_variable_semantics(df: pd.DataFrame, sheet_name: str) -> Tuple[str, str]:
    """Infer what market variable this sheet represents.
    
    Returns:
        (canonical_variable_name, confidence_level)
        confidence_level: 'high' | 'medium' | 'low'
    """
    # First try sheet name matching
    canonical = normalize_sheet_name(sheet_name)
    
    # If we got a known canonical name (not just titlecased original), confidence is high
    if canonical != sheet_name.strip().title():
        return canonical, 'high'
    
    # Try to infer from data patterns (future enhancement)
    # For now, use the normalized name with medium confidence
    return canonical, 'medium'


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

    # Strategy: check metadata rows (rows 3-6) for repetitive patterns
    # Family A: one row will have same value repeated across companies (e.g., "VAL", "VAL", "VAL")
    # Family B: attribute row will have many different values (ALTHIGHMID, ALTLOWMID, BASK, etc.)
    
    min_distinct = float('inf')
    
    for i in range(3, min(7, len(df))):
        tokens = _row_tokens(df, i)
        # Exclude metadata column labels
        non_metadata_tokens = [t for t in tokens if t.lower() not in {'code amc', 'code isin', 'libelle'}]
        
        if len(non_metadata_tokens) >= 3:  # Need at least 3 values to assess pattern
            distinct_count = len({token.lower() for token in non_metadata_tokens})
            min_distinct = min(min_distinct, distinct_count)
    
    if min_distinct == float('inf'):
        return SheetKind.UNKNOWN
    
    # Family A: will have at least one metadata row with <=2 distinct values
    # Family B: all metadata rows have many distinct values
    if min_distinct <= 2:
        return SheetKind.MARKET_FAMILY_A
    return SheetKind.MARKET_FAMILY_B


def should_include_in_market_dataset(
    sheet_kind: SheetKind,
    canonical_variable: str,
    confidence: str,
    required_variables: set[str] = None
) -> Tuple[bool, str]:
    """Decide whether a sheet should be included in the unified market dataset.
    
    Args:
        sheet_kind: Detected sheet type
        canonical_variable: Inferred variable name
        confidence: Confidence level of inference
        required_variables: Set of required variable names (optional allowlist)
    
    Returns:
        (should_include, reason)
    """
    # Never include non-Family-A sheets
    if sheet_kind != SheetKind.MARKET_FAMILY_A:
        return False, f"Sheet type is {sheet_kind.value}, not market Family A"
    
    # If allowlist provided, only include if variable is in it
    if required_variables:
        if canonical_variable in required_variables:
            return True, f"Variable '{canonical_variable}' is in allowlist"
        else:
            return False, f"Variable '{canonical_variable}' not in required set {required_variables}"
    
    # If no allowlist, include all high/medium confidence Family A sheets
    if confidence in ('high', 'medium'):
        return True, f"Family A sheet with {confidence} confidence variable identification"
    
    # Low confidence sheets require manual review
    return False, f"Low confidence variable identification for '{canonical_variable}'"


def get_parser_for_sheet(df: pd.DataFrame) -> Optional[Callable[[str, str], pd.DataFrame]]:
    family = detect_sheet_family(df)
    if family == SheetKind.MARKET_FAMILY_A:
        return parse_simple_sheet
    return None
