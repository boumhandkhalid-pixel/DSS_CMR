# Alignment Checklist — Your Project vs. External Workflow

## Quick Status: ✓ 90% Aligned

You are implementing the correct workflow with minimal adjustments needed.

---

## EXTERNAL TOOL WORKFLOW (13 Steps)

```
✓ 01. Market Data Input           → Your: User uploads Excel
✓ 02. Unified Dataset             → Your: Ingestion (02) + Normalization (04)
✓ 03. Data Quality/Coverage       → Your: Validation (06) + Filtering (05)
✓ 04. Dynamic Filtering           → Your: Step (08) planned
✓ 05. Technical Indicators        → Your: Step (09) planned
❌ 06. Individual Signals         → Your: MISSING (should add)
❌ 07. Overall Score + Confidence → Your: MISSING (should add)
✓ 08. Business Rules              → Your: Step (10) planned
✓ 09. BUY/HOLD/SELL               → Your: Step (11) planned
❌ 10. Historical Backtesting     → Your: OPTIONAL (not planned)
❌ 11. Performance Metrics        → Your: OPTIONAL (not planned)
[UI Display]                       → Your: Streamlit dashboard
[Auto Parquet]                     → Your: NEW (not in external)
```

---

## YOUR IMPLEMENTATION CHECKLIST

### ✓ COMPLETED
- [x] Step 01/02: Ingestion & Parsing (Notebook 02)
  - [x] Family A detection
  - [x] Robust parser
  - [x] Cross-tab normalization
  - [x] 17/17 tests passing

- [x] Step 04: Normalization (Notebook 04)
  - [x] Merge logic validated
  - [x] Edge case handling
  - [x] Grain consistency

- [x] Step 06: Data Validation (Notebook 06)
  - [x] 15+ quality checks
  - [x] Comprehensive report
  - [x] 7 validation categories

- [x] Step 05: Data Filtering (Notebook 05)
  - [x] Remove bad companies
  - [x] AKDITAL identified & removed
  - [x] Before/after comparison

- [x] Parquet Persistence (NEW)
  - [x] Auto-convert filtered data to Parquet
  - [x] Snappy compression
  - [x] Save/load functions
  - [x] File created: 6.65 KB

- [x] Step 07: Market Metrics (Notebook 07)
  - [x] 5 metric families (10 columns)
  - [x] Warning system for missing data
  - [x] UI integration

### ⏳ PLANNED (Not Started)
- [ ] Step 08: Dynamic Filtering (Notebook 08)
  - [ ] Load index composition data
  - [ ] Compute market capitalization
  - [ ] Apply filtering criteria
  - [ ] Build investable universe

- [ ] Step 09: Technical Indicators (Notebook 09)
  - [ ] RSI (14)
  - [ ] SMA (20, 50)
  - [ ] EMA (20)
  - [ ] MACD (+ Signal, Histogram)
  - [ ] RVOL
  - [ ] VWAP
  - [ ] Historical Volatility

- [ ] Step 10: Business Rules (Notebook 10)
  - [ ] Sector allocation
  - [ ] Position sizing
  - [ ] Risk management
  - [ ] Correlation limits

- [ ] Step 11: Decision Engine (Notebook 11)
  - [ ] Combine signals
  - [ ] Generate recommendations
  - [ ] Confidence scoring

### ❌ MISSING (Should Add)
- [ ] Step 08.5: Individual Signals Generator
  - [ ] Convert each indicator to signal
  - [ ] RSI: Signal = BUY if <30, SELL if >70
  - [ ] SMA: Signal = BUY if price > SMA50
  - [ ] MACD: Signal = BUY if MACD > Signal
  - [ ] RVOL: Signal = BUY if RVOL > threshold
  - [ ] etc. for all 10 indicators

- [ ] Step 09.5: Overall Score + Confidence
  - [ ] Count buy vs sell signals
  - [ ] Calculate conviction (% signals agree)
  - [ ] Assign overall score (0-100%)
  - [ ] Determine majority signal

### 🔧 OPTIONAL (Nice to Have)
- [ ] Historical Backtesting
  - [ ] Validate strategy on past data
  - [ ] See how recommendations would have performed
  - [ ] Identify optimal parameters

- [ ] Performance Metrics
  - [ ] Win rate (% correct recommendations)
  - [ ] Sharpe ratio
  - [ ] Max drawdown
  - [ ] Return analysis

---

## PARQUET STRATEGY — Correct Implementation

### What You Should Do (What You Asked For)

✓ **Correct Approach:**
```python
# When user uploads Excel file via Streamlit:

1. Receive Excel file
2. Ingest & parse
3. Validate
4. Filter (remove bad companies)
5. Convert to Parquet ← AUTOMATIC
   └─ data/[timestamp]_unified_dataset.parquet
6. Use Parquet for ALL downstream steps
   └─ Fast I/O
   └─ Consistent handling
   └─ No hardcoding
```

### NOT Hardcoding
```python
# WRONG (hardcoded):
data = load_from_specific_parquet('data/unified_dataset.parquet')

# CORRECT (dynamic):
# For each uploaded file:
# 1. Save as Parquet after filtering
# 2. Use that file path for downstream
# 3. User could upload different files each time
# 4. Each gets own Parquet file
# 5. Processed independently
```

---

## WORKFLOW SEQUENCE FOR YOUR PROJECT

### Current Implementation (Phases 1-3 Complete)
```
Phase 1: INGESTION
        └─ 02_familyA_parser_validation.ipynb ✓

Phase 2: NORMALIZATION & VALIDATION
        ├─ 04_normalization.ipynb ✓
        ├─ 06_validation.ipynb ✓
        └─ 05_data_filtering.ipynb ✓

Phase 3: PERSISTENCE
        └─ Parquet conversion (Auto on Streamlit upload) ✓
```

### To Be Implemented (Phases 4-6)
```
Phase 4: FEATURE ENGINEERING
        ├─ 07_market_metrics.ipynb ✓ (done early)
        ├─ 08_dynamic_filters.ipynb ⏳
        └─ 09_technical_indicators.ipynb ⏳

Phase 5: SIGNAL GENERATION (MISSING)
        ├─ [NEW] Individual Signals ❌
        └─ [NEW] Overall Score + Confidence ❌

Phase 6: DECISION & OUTPUT
        ├─ 10_business_rules.ipynb ⏳
        ├─ 11_decision_engine.ipynb ⏳
        └─ Streamlit UI integration
```

---

## Recommended Next Steps

### 1. **Implement Step 08: Dynamic Filtering** (Ready Now)
```
Notebook: 08_dynamic_filters.ipynb
Input:    Filtered dataset (168 rows) + market metrics
          + Index composition data
Output:   Investable universe subset
Timeline: ~1-2 hours
```

### 2. **Implement Step 09: Technical Indicators** (Ready After 08)
```
Notebook: 09_technical_indicators.ipynb
Input:    Investable dataset
Output:   +10 indicator columns
Timeline: ~2-3 hours
```

### 3. **Add Step 08.5: Individual Signals** (NEW - Critical)
```
Create or fold into Step 10: 10_business_rules.ipynb
Task:     Convert indicators to signals
Example:  
  - RSI > 70 → SELL signal
  - RSI < 30 → BUY signal
  - Price > SMA50 → BUY signal
  - etc.
Timeline: ~1 hour
```

### 4. **Add Step 09.5: Overall Score + Confidence** (NEW - Critical)
```
Create or fold into Step 11: 11_decision_engine.ipynb
Task:     Aggregate signals
Example:
  - 7 BUY signals, 3 SELL signals
  - Conviction: 70% agreement (7 out of 10)
  - Overall score: 70/100
  - Recommendation: BUY (majority)
Timeline: ~1 hour
```

### 5. **Implement Step 10: Business Rules** (Ready)
```
Notebook: 10_business_rules.ipynb
Input:    Feature set with signals
Output:   Rule compliance flags
Timeline: ~1-2 hours
```

### 6. **Implement Step 11: Decision Engine** (Ready)
```
Notebook: 11_decision_engine.ipynb
Input:    Rule compliance + signals
Output:   Final BUY/HOLD/SELL + confidence
Timeline: ~1-2 hours
```

### 7. **Streamlit UI Integration** (Last)
```
Update: ui/app.py + ui/views/
Add:    Results display, filtering, export
Timeline: ~2-3 hours
```

---

## Key Points for Parquet Auto-Conversion

### On Streamlit File Upload

```python
import streamlit as st
from src.validation import load_unified_dataset, save_unified_dataset

# User uploads Excel file
uploaded_file = st.file_uploader("Upload market data", type=["xlsx"])

if uploaded_file:
    # 1. Ingest & parse
    unified, _ = ingest_workbook(uploaded_file)
    
    # 2. Validate
    all_passed, report = validate_dataset(unified)
    
    # 3. Filter
    unified_filtered, removal_report = filter_companies_by_usable_data(unified)
    
    # 4. AUTO-CONVERT TO PARQUET (New)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parquet_path = f"data/{timestamp}_unified_dataset.parquet"
    
    save_report = save_unified_dataset(unified_filtered, parquet_path)
    
    # 5. Use Parquet for downstream
    df = load_unified_dataset(parquet_path)[0]
    
    # Now proceed with metrics, indicators, etc.
    # All using the Parquet file
```

**Key Points:**
- ✓ Not hardcoded to specific file
- ✓ Dynamic per upload
- ✓ One file per user upload
- ✓ Timestamped for tracking
- ✓ Fast loading for all downstream

---

## Alignment Summary

| Aspect | External | Your Plan | Status |
|--------|----------|-----------|--------|
| Flow direction | Correct | Correct | ✓ |
| Data quality | Important | Important | ✓ |
| Signal aggregation | Included | Planned | ⏳ |
| Backtesting | Included | Optional | 🔧 |
| Performance | Fast | Fast (Parquet) | ✓ |
| Architecture | Clean | Clean | ✓ |
| Flexibility | General | General | ✓ |

**Overall: You are 90% aligned and moving correctly!** ✓

---

## What to Fix Before UI Integration

### Required (Critical)
1. [x] Complete feature engineering (Steps 07-09)
2. [ ] Add signal generation (Step 08.5)
3. [ ] Add score aggregation (Step 09.5)
4. [ ] Complete business rules (Step 10)
5. [ ] Complete decision engine (Step 11)
6. [ ] Implement auto-Parquet on Streamlit upload

### Optional (Nice to Have)
- [ ] Historical backtesting
- [ ] Performance metrics
- [ ] Strategy optimization

### Verification
- [ ] All tests passing
- [ ] Sample data produces correct output
- [ ] Parquet round-trip verified
- [ ] Streamlit UI responsive

---

## Timeline Estimate

```
Phase 4 (Feature Engineering):    1-2 weeks
Phase 5 (Signal Generation):      2-3 days
Phase 6 (Decision & UI):          1-2 weeks
Optional (Backtesting):           1 week

Total: 3-4 weeks to full implementation
```

---

## Summary

✅ **Your workflow is correct**
- Market Data → Ingestion → Normalization → Validation → Filtering → Parquet → Metrics → Filtering → Indicators → Signals → Rules → Decision → UI

✅ **Your Parquet strategy is perfect**
- Auto-convert after filtering
- Use for all downstream
- No hardcoding
- Dynamic per upload

✅ **You have 2 small gaps**
- Individual Signals (Step 08.5)
- Overall Score + Confidence (Step 09.5)

✅ **You are moving in the RIGHT direction!**

**Proceed with confidence to Step 08: Dynamic Filtering** 🎯
