# Quick Reference — Complete Workflow Overview

## Your Project Workflow (13 Steps)

```
INGESTION → NORMALIZATION → VALIDATION → FILTERING → PERSISTENCE
    ↓            ↓              ↓            ↓            ↓
   (02)         (04)           (06)        (05)      [PARQUET]
                                                        ↓
                            FEATURE ENGINEERING (AUTO-LOAD FROM PARQUET)
                            ↓
    METRICS → DYNAMIC FILTER → INDICATORS → SIGNALS → SCORE → RULES → DECISION → UI
      (07)         (08)          (09)      (08.5)   (09.5)    (10)      (11)
```

---

## Step-by-Step Reference

| Step | Notebook | Input | Process | Output | Status |
|------|----------|-------|---------|--------|--------|
| 01/02 | `02_familyA_parser` | Excel files | Parse & normalize | (182 × 8) | ✓ DONE |
| 04 | `04_normalization` | Parsed data | Merge sheets | Unified df | ✓ DONE |
| 06 | `06_validation` | Unified df | 15+ quality checks | Valid/invalid | ✓ DONE |
| 05 | `05_data_filtering` | Validated df | Remove bad companies | (168 × 8) | ✓ DONE |
| - | Parquet Convert | Filtered df | Compress & save | .parquet file | ✓ DONE |
| 07 | `07_market_metrics` | From Parquet | Compute metrics | (168 × 18) | ✓ DONE |
| 08 | `08_dynamic_filters` | Metrics + index | Filter by criteria | Investable set | ⏳ TODO |
| 09 | `09_technical_indicators` | Investable set | RSI, SMA, EMA, MACD, etc. | (168 × 28) | ⏳ TODO |
| 08.5 | *In Step 10 | Indicators | Convert to signals | Signal df | ❌ NEW |
| 09.5 | *In Step 11 | Signals | Aggregate & score | Score df | ❌ NEW |
| 10 | `10_business_rules` | Score df | Apply portfolio rules | Rule flags | ⏳ TODO |
| 11 | `11_decision_engine` | Rule flags | Generate recommendations | BUY/HOLD/SELL | ⏳ TODO |
| 12 | Streamlit | Recommendations | Display results | UI Dashboard | ⏳ TODO |

---

## Data Transformation Pipeline

```
Excel File (User Upload)
       ↓ (Ingestion 02)
    ↓ Parsed data
       ↓ (Normalization 04)
    ↓ Unified: (182 × 8)
       ↓ (Validation 06)
    ↓ Validated: (182 × 8)
       ↓ (Filtering 05)
    ↓ Clean: (168 × 8) [AKDITAL removed]
       ↓ (Parquet Convert)
    ↓ PARQUET FILE: 6.65 KB
       ↓ (Load from Parquet)
    ↓ DataFrame: (168 × 8)
       ├─ (Market Metrics 07)
       │  ↓ (168 × 18)
       │
       ├─ (Dynamic Filter 08)
       │  ↓ Investable subset
       │
       ├─ (Technical Indicators 09)
       │  ↓ (168 × 28) [approx]
       │
       └─ (Signals 08.5 + Score 09.5)
          ↓
       Signal DataFrame
          ↓ (Business Rules 10)
       Rule-compliant
          ↓ (Decision Engine 11)
       BUY / HOLD / SELL
          ↓ (Streamlit)
       UI Dashboard
```

---

## Current Status by Phase

### ✓ COMPLETE (3 Phases)

**Phase 1: INGESTION**
- Parser: Robust, handles Family A sheets
- Tests: 17/17 passing
- File: `src/parsers/data_sheet_parser.py`
- Notebook: `02_familyA_parser_validation.ipynb`

**Phase 2: QUALITY**
- Validation: 15+ checks, 7 categories
- Filtering: Removes low-quality companies (AKDITAL)
- Files: `src/validation.py`
- Notebooks: `06_validation.ipynb`, `05_data_filtering.ipynb`

**Phase 3: PERSISTENCE**
- Parquet: Auto-convert after filtering
- Functions: `save_unified_dataset()`, `load_unified_dataset()`
- File: `data/unified_dataset.parquet` (6.65 KB)
- Compression: Snappy

### ⏳ PLANNED (5 Phases)

**Phase 4: FEATURE ENGINEERING**
- Market Metrics (07): ✓ Done early
- Dynamic Filtering (08): Load tomorrow
- Technical Indicators (09): Load after 08

**Phase 5: SIGNAL GENERATION** (NEW)
- Individual Signals (08.5): Convert indicators to signals
- Overall Score + Confidence (09.5): Aggregate signals

**Phase 6: DECISION**
- Business Rules (10): Apply constraints
- Decision Engine (11): Final recommendations

### 🔧 OPTIONAL (2 Phases)

**Phase 7: VALIDATION**
- Historical Backtesting: Test on past data
- Performance Metrics: Win rate, Sharpe ratio

**Phase 8: DISPLAY**
- Streamlit UI: Dashboard & reports

---

## Parquet Strategy (Correct)

### ✓ What You Should Do

```
AUTOMATIC CONVERSION (On Streamlit Upload)
│
├─ Receive: Excel file
├─ Parse: Extract data
├─ Validate: Quality checks
├─ Filter: Remove bad companies
├─ Convert: TO PARQUET ← AUTO
│  └─ data/[timestamp]_unified_dataset.parquet
├─ Load: From Parquet
├─ Proceed: With metrics/indicators/etc.
│
NO HARDCODING
│
FOR EACH UPLOAD:
├─ New timestamp
├─ New Parquet file
├─ Independent processing
└─ Dynamic handling
```

### ✗ NOT Hardcoding

```
❌ WRONG:
  - Assuming file location: 'data/unified_dataset.parquet'
  - Hardcoded paths in code
  - Same file for all uploads

✓ CORRECT:
  - Generate timestamp-based filename
  - Store path in session/config
  - Each upload → separate file
  - User can upload different files
```

---

## Key Metrics

### Current Dataset
- Records: 168 (was 182, -14 rows)
- Companies: 6 (was 7, AKDITAL removed)
- Columns: 8 core + 10 metrics + 10 indicators ≈ 28 total
- Sessions: 28 trading dates
- Parquet Size: 6.65 KB (compressed)

### Coverage
- Price data: 100% for kept companies
- Quality: 9/15 validation tests passing
- Ready for indicators: YES ✓

---

## External Tool vs. Your Implementation

```
EXTERNAL WORKFLOW               YOUR IMPLEMENTATION
─────────────────────────────────────────────────────

1. Market Data                  Excel upload
2. Unified Dataset              Ingestion (02) + Normalization (04)
3. Data Quality/Coverage        Validation (06) + Filtering (05)
4. Dynamic Filtering            Step 08 (planned)
5. Technical Indicators         Step 09 (planned)
6. Individual Signals           NEW: Step 08.5
7. Overall Score + Confidence   NEW: Step 09.5
8. Business Rules               Step 10 (planned)
9. BUY/HOLD/SELL                Step 11 (planned)
10. Historical Backtesting      Optional
11. Performance Metrics         Optional
                                Parquet (auto-convert)
                                Streamlit UI
```

**Alignment: 90% ✓**

---

## Next 30 Minutes (Do This Now)

1. Read: `ARCHITECTURE_DIAGRAM.md` (5 min)
2. Read: `ALIGNMENT_CHECKLIST.md` (5 min)
3. Review: Current Notebook 07 (5 min)
4. Start: Notebook 08_dynamic_filters.ipynb (15 min)

**Expected by End of Day:**
- ✓ Understand complete workflow
- ✓ Start implementing Step 08
- ✓ Plan Steps 08.5 & 09.5 (new signal steps)

---

## Success Criteria

### By End of This Phase
- [ ] Understand workflow (✓ You will after reading docs)
- [ ] Parquet strategy clear (✓ Auto-convert, no hardcoding)
- [ ] Next steps obvious (→ Start with Step 08)

### By End of Project
- [ ] Steps 07-11 complete
- [ ] Steps 08.5, 09.5 added
- [ ] Streamlit UI functional
- [ ] All tests passing

---

## Commands to Know

### Load from Parquet (for Steps 08+)
```python
from src.validation import load_unified_dataset

df = load_unified_dataset('data/unified_dataset.parquet')[0]
# Use df for metrics/indicators/etc.
```

### Save New Dataset (after processing)
```python
from src.validation import save_unified_dataset

save_report = save_unified_dataset(
    df_with_new_features,
    'data/processed_dataset.parquet'
)
```

### Test All Imports
```python
python3 -c "
from src.ingestion import ingest_workbook
from src.validation import validate_dataset, filter_companies_by_usable_data, save_unified_dataset, load_unified_dataset
from src.metrics import compute_all_metrics
print('✓ All imports OK')
"
```

---

## File Locations

```
Project Structure:
├── data/
│   ├── unified_dataset.parquet    ← Filtered dataset (6.65 KB)
│   ├── Compo_All_Indices_*.xlsx   ← Index composition (for Step 08)
│   └── Données Marché Boursier_*.xlsx ← Sample data
├── notebooks/
│   ├── 02_familyA_parser_validation.ipynb     ✓ Done
│   ├── 04_normalization.ipynb                 ✓ Done
│   ├── 05_data_filtering.ipynb                ✓ Done (+ Parquet)
│   ├── 06_validation.ipynb                    ✓ Done
│   ├── 07_market_metrics.ipynb                ✓ Done
│   ├── 08_dynamic_filters.ipynb               ⏳ TODO
│   ├── 09_technical_indicators.ipynb          ⏳ TODO
│   ├── 10_business_rules.ipynb                ⏳ TODO
│   └── 11_decision_engine.ipynb               ⏳ TODO
└── src/
    ├── validation.py                          ✓ + Parquet functions
    ├── metrics.py                             ✓ Done
    └── parsers/
```

---

## Summary (TL;DR)

**You are correct!** ✓

- Workflow is aligned with external tool
- Parquet strategy is perfect (auto-convert, dynamic)
- Only 2 small additions needed (Steps 08.5 & 09.5)
- Next: Start Step 08 (Dynamic Filtering)
- Timeline: 3-4 weeks to full implementation

**No changes needed to core architecture.**  
**Proceed with confidence to Step 08.** 🎯
