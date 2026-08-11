# Parser Usage Guide

Quick reference for using the robust BVC market data parser.

---

## Basic Usage

```python
from src.ingestion import ingest_workbook

# Simple ingestion (permissive mode)
unified_df, report = ingest_workbook('path/to/workbook.xlsx')

# With allowlist (recommended for production)
required_vars = {'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
unified_df, report = ingest_workbook('path/to/workbook.xlsx', 
                                     required_variables=required_vars)
```

---

## What Sheet Names Are Accepted?

The parser recognizes these patterns (case-insensitive):

### Closing Price (→ "Cours")
- cours, COURS, Cours
- close, Close, CLOSE
- closing, Closing
- cloture, clôture, Clôture

### Bid (→ "Bid")
- bid, BID, Bid
- achat, Achat, ACHAT
- demande, Demande

### Ask (→ "Ask")
- ask, ASK, Ask
- vente, Vente, VENTE
- offre, Offre, OFFRE

### Volume (→ "Volume MC")
- volume, VOLUME, Volume
- volume mc, Volume MC, VOLUME_MC
- volume marche, Volume Marché

### Quantity (→ "Quantité MC")
- quantité, Quantité, QUANTITE
- quantité mc, Quantité MC, QUANTITE_MC
- quantité marche, Quantité Marché

---

## Ingestion Report Structure

```python
report = {
    'total_sheets': 7,
    'sheets_included': [
        {
            'name': 'cours',              # Original name
            'canonical_variable': 'Cours', # Normalized name
            'kind': 'family_a',
            'confidence': 'medium',
            'records': 98,
            'included': True,
            'reason': 'Family A sheet with medium confidence'
        }
    ],
    'sheets_excluded': [...],
    'warnings': [],
    'unified_records': 182,
    'unified_companies': 7,
    'unified_sessions': 28,
    'unified_variables': ['Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC']
}
```

---

## Example: Checking Report

```python
unified_df, report = ingest_workbook('market_data.xlsx')

# Check what was included
print(f"Included {len(report['sheets_included'])} sheets:")
for sheet in report['sheets_included']:
    print(f"  ✓ {sheet['name']} -> {sheet['canonical_variable']}")

# Check what was excluded
print(f"\nExcluded {len(report['sheets_excluded'])} sheets:")
for sheet in report['sheets_excluded']:
    print(f"  ⊗ {sheet['name']}: {sheet['reason']}")

# Check for warnings
if report['warnings']:
    print(f"\n⚠ Warnings:")
    for w in report['warnings']:
        print(f"  - {w}")
```

---

## Unified Dataset Structure

```python
# Output DataFrame columns:
# - Date: datetime64
# - CODE_ISIN: str (MA...)
# - Company: str
# - Cours: float (if Cours sheet present)
# - Bid: float (if Bid sheet present)
# - Ask: float (if Ask sheet present)
# - Volume MC: float (if Volume sheet present)
# - Quantité MC: float (if Quantité sheet present)

# Grain: Date × CODE_ISIN (one row per company per trading session)
```

---

## Common Scenarios

### Scenario 1: All sheets have correct names
```python
# Sheets: Cours, Bid, Ask, Volume MC, Quantité MC
unified_df, report = ingest_workbook('workbook.xlsx')
# Result: All 5 sheets included ✓
```

### Scenario 2: Lowercase sheet names
```python
# Sheets: cours, bid, ask, volume mc, quantité mc
unified_df, report = ingest_workbook('workbook.xlsx')
# Result: All normalized and included ✓
```

### Scenario 3: Mixed languages
```python
# Sheets: cours, offre, demande, volume, quantité mc
unified_df, report = ingest_workbook('workbook.xlsx')
# Result: 
# - cours -> Cours ✓
# - offre -> Ask ✓
# - demande -> Bid ✓
# - volume -> Volume MC ✓
# - quantité mc -> Quantité MC ✓
```

### Scenario 4: Unknown sheet names
```python
# Sheets: Sheet1, Feuil1, Unknown
unified_df, report = ingest_workbook('workbook.xlsx')
# Result: 
# - If Family A structure: Included with medium confidence
# - If Family B structure: Excluded
# - Check report['sheets_included'] for details
```

### Scenario 5: Data sheet present (Family B)
```python
# Sheets: Cours, Bid, Ask, Data, Indicateurs
unified_df, report = ingest_workbook('workbook.xlsx')
# Result:
# - Cours, Bid, Ask included ✓
# - Data, Indicateurs excluded (Family B) ✓
```

---

## Allowlist Recommendations

### Development/Testing
```python
# No allowlist - include all Family A sheets
unified_df, report = ingest_workbook('workbook.xlsx')
```

### Production (Recommended)
```python
# Strict allowlist - only expected variables
required = {'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
unified_df, report = ingest_workbook('workbook.xlsx', 
                                     required_variables=required)
```

### Custom Requirements
```python
# Only price data
required = {'Cours', 'Bid', 'Ask'}
unified_df, report = ingest_workbook('workbook.xlsx', 
                                     required_variables=required)
```

---

## Troubleshooting

### Problem: Sheet not included

**Check:**
1. Is it Family A structure? (has CODE ISIN and LIBELLE rows)
2. Does sheet name match any pattern? Check report['sheets_excluded']
3. Is it in allowlist? (if using required_variables)

**Solution:**
- Add pattern to `_MARKET_VARIABLE_PATTERNS` in `parser_factory.py`
- Or use sheet without allowlist if structure is correct

### Problem: Wrong variable name

**Example:** Sheet "price" becomes "Price" instead of "Cours"

**Solution:**
- Add to pattern: `r'price|prix': 'Cours'`
- Or rename sheet before import

### Problem: Duplicate variables

**Example:** Both "Cours" and "cours" sheets present

**Result:** Last one wins in pivot (both become "Cours" variable)

**Solution:**
- Remove duplicate sheet before import
- Or keep only one with correct data

---

## Adding New Patterns

Edit `src/parsers/parser_factory.py`:

```python
_MARKET_VARIABLE_PATTERNS = {
    # ... existing patterns ...
    
    # Add new pattern
    r'your_pattern|alternative': 'Canonical Name',
}
```

**Pattern syntax:**
- Use `|` for alternatives: `cours|close`
- Use `.*` for wildcards: `volume.*mc`
- Use `^` for start: `^price`
- Use `$` for end: `volume$`
- Use `[eé]` for character variants: `quantit[eé]`

---

## Performance Notes

- **First read:** 20 rows per sheet (detection only)
- **Full parse:** Complete sheet if Family A
- **Memory:** ~10 MB for typical BVC workbook (7 sheets, 100 companies, 250 sessions)
- **Time:** ~2-5 seconds for complete ingestion on modern hardware

---

## Next Steps After Ingestion

1. **Validate data quality** (notebook 06)
   - Check for missing CODE ISIN
   - Check for duplicate Date × CODE_ISIN
   - Check for invalid dates
   - Check null percentage

2. **Compute market metrics** (notebook 07)
   - Market capitalization
   - Liquidity
   - Average volume

3. **Apply dynamic filters** (notebook 08)
   - Use index composition dataset
   - Filter investable universe

4. **Compute technical indicators** (notebook 09)
   - RSI, MACD, SMA, EMA, etc.

---

## API Reference

### `ingest_workbook(path, required_variables=None)`

**Parameters:**
- `path` (str): Path to Excel workbook
- `required_variables` (set[str], optional): Allowlist of canonical variable names

**Returns:**
- `unified_df` (pd.DataFrame): Unified market dataset
- `report` (dict): Detailed ingestion report

**Raises:**
- `FileNotFoundError`: If workbook doesn't exist
- `ValueError`: If workbook is corrupted or unreadable

---

## Support

For issues or questions:
1. Check report['warnings'] for error messages
2. Review report['sheets_excluded'] for exclusion reasons
3. Verify sheet structure matches Family A pattern (CODE ISIN + LIBELLE rows)
4. Check pattern definitions in parser_factory.py
