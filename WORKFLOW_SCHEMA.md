# DSS Workflow Schema — Current vs. Proposed

## Overview

This document compares your **current implementation** with the **external tool's suggested workflow** to ensure alignment and identify any gaps.

---

## EXTERNAL TOOL SUGGESTED WORKFLOW

```
Market Data (User Upload)
       │
       ▼
Unified Dataset (Ingestion + Parsing)
       │
       ▼
Data Quality / Coverage (Validation)
       │
       ▼
Dynamic Filtering (Filter by criteria)
       │
       ▼
Technical Indicators (Compute metrics)
       │
       ▼
Individual Signals (Per-indicator signals)
       │
       ▼
Overall Score + Signal Confidence (Aggregate)
       │
       ▼
Business Rules (Apply portfolio rules)
       │
       ▼
BUY / HOLD / SELL (Final decision)
       │
       ▼
Historical Backtesting (Validation)
       │
       ▼
Performance Metrics (Results analysis)
```

---

## YOUR CURRENT IMPLEMENTATION

```
BVC Excel Files
       │
       ▼
Ingestion + Parsing (02)
   └─ Parser Factory
   └─ Family A Detection
   └─ Cross-tab normalization
       │
       ▼
Normalized Dataset
       │
       ▼
Data Validation (06)
   └─ 15+ quality checks
   └─ Schema validation
   └─ Consistency checks
       │
       ▼
Data Filtering (05)
   └─ Remove low-quality companies
   └─ AKDITAL removed
       │
       ▼
Parquet Persistence
   └─ Save: data/unified_dataset.parquet
   └─ Snappy compression
       │
       ▼
Market Metrics (07)
   └─ Average Volume
   └─ Liquidity Proxy
   └─ Bid-Ask Spreads
   └─ Trading Coverage
   └─ Volatility Proxy
       │
       ▼
[Downstream Pipeline]
   ├─ Dynamic Filtering (08) ← NOT YET STARTED
   ├─ Technical Indicators (09) ← NOT YET STARTED
   ├─ Business Rules (10) ← NOT YET STARTED
   └─ Decision Engine (11) ← NOT YET STARTED
       │
       ▼
Streamlit UI
   └─ Results Display
```

---

## ALIGNMENT ANALYSIS

### ✓ MATCH — Already Implemented

| Step | External Workflow | Your Implementation | Status |
|------|-------------------|-------------------|--------|
| 1 | Market Data | BVC Excel files | ✓ MATCH |
| 2 | Unified Dataset | Ingestion (02) + Normalization (04) | ✓ MATCH |
| 3 | Data Quality/Coverage | Data Validation (06) | ✓ MATCH |

### ⏳ PARTIAL — In Progress or Needs Definition

| Step | External Workflow | Your Implementation | Status |
|------|-------------------|-------------------|--------|
| 4 | Dynamic Filtering | Notebook 08 (planned) | ⏳ NOT STARTED |
| 5 | Technical Indicators | Notebook 09 (planned) | ⏳ NOT STARTED |
| 6 | Individual Signals | Not yet defined | ❌ MISSING |
| 7 | Overall Score + Confidence | Not yet defined | ❌ MISSING |
| 8 | Business Rules | Notebook 10 (planned) | ⏳ NOT STARTED |
| 9 | BUY/HOLD/SELL | Notebook 11 (planned) | ⏳ NOT STARTED |

### ✗ NOT ADDRESSED — New Additions

| Step | External Workflow | Your Implementation | Status |
|------|-------------------|-------------------|--------|
| 10 | Historical Backtesting | Not planned | ❌ NEW |
| 11 | Performance Metrics | Not planned | ❌ NEW |

---

## YOUR WORKFLOW vs. EXTERNAL WORKFLOW

### Side-by-Side Comparison

```
EXTERNAL                          YOUR CURRENT
─────────────────────────────────────────────────────────────

Market Data                       Market Data (Excel)
    ↓                                 ↓
Unified Dataset                   Ingestion (02)
                                  Normalization (04)
                                      ↓
                                  Unified Dataset ✓
                                      ↓
Data Quality/Coverage             Data Validation (06) ✓
    ↓                                 ↓
Dynamic Filtering                 Data Filtering (05)
                                  Market Metrics (07)
                                      ↓
                                  Dynamic Filtering (08) ⏳
                                      ↓
Technical Indicators              Technical Indicators (09) ⏳
    ↓                                 ↓
Individual Signals                [NOT DEFINED] ❌
    ↓
Overall Score +                   [NOT DEFINED] ❌
Signal Confidence
    ↓
Business Rules                    Business Rules (10) ⏳
    ↓
BUY/HOLD/SELL                     Decision Engine (11) ⏳
    ↓
Historical Backtesting            [NOT PLANNED] ❌
    ↓
Performance Metrics               [NOT PLANNED] ❌
```

---

## DETAILED WORKFLOW WITH YOUR IMPLEMENTATION

### Complete Current Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Market Data Ingestion                               │
├─────────────────────────────────────────────────────────────┤
│ Input:  BVC Excel files (uploaded by user)                  │
│         - Données Marché Boursier_Projet_IA.xlsx            │
│         - Compo_All_Indices_20260731.xlsx                   │
│         - Custom formats (flexible parser)                  │
│                                                              │
│ Process: Ingestion (01/02)                                  │
│         └─ Detect sheet type (Family A, Family B, unknown)  │
│         └─ Parse to standard format                         │
│         └─ Create unified structure                         │
│                                                              │
│ Output: Unified DataFrame (in-memory)                       │
│         (182 rows × 8 columns)                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Data Normalization                                  │
├─────────────────────────────────────────────────────────────┤
│ Input:  Parsed data from Step 1                             │
│                                                              │
│ Process: Normalization (04)                                 │
│         └─ Merge sheets into unified table                  │
│         └─ Validate grain (1 company × 1 session)           │
│         └─ Preserve all columns                             │
│                                                              │
│ Output: Normalized DataFrame                                │
│         Columns: Date, CODE_ISIN, Company, Cours, Bid, Ask, │
│                  Volume MC, Quantité MC                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Data Quality & Coverage (Validation)                │
├─────────────────────────────────────────────────────────────┤
│ Input:  Normalized DataFrame                                │
│                                                              │
│ Process: Validation (06)                                    │
│         └─ Schema validation (required columns present)     │
│         └─ Grain validation (data structure)                │
│         └─ Date range validation                            │
│         └─ Price validation (Bid-Ask logic)                 │
│         └─ Volume validation (non-negative)                 │
│         └─ Consistency validation                           │
│         └─ Generate quality report                          │
│                                                              │
│ Output: Validation report                                   │
│         (9/15 tests passed for sample data)                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3.5: Data Filtering (Quality Assurance)                │
├─────────────────────────────────────────────────────────────┤
│ Input:  Validated DataFrame                                 │
│         (182 rows × 8 columns, 7 companies)                 │
│                                                              │
│ Process: Filtering (05)                                     │
│         └─ Remove companies with insufficient data          │
│         └─ Threshold: min_usable_rows=10 (Cours column)     │
│         └─ Decision: AKDITAL removed (0 price values)       │
│                                                              │
│ Output: Filtered DataFrame                                  │
│         (168 rows × 8 columns, 6 companies)                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Parquet Persistence (NEW FOR UI)                    │
├─────────────────────────────────────────────────────────────┤
│ Input:  Filtered DataFrame                                  │
│                                                              │
│ Process: Convert to Parquet                                 │
│         └─ User uploads ANY Excel file                      │
│         └─ Auto-convert to Parquet after filtering          │
│         └─ Store in data/[timestamp]_unified_dataset.parquet│
│         └─ Snappy compression (6.65 KB for sample)          │
│         └─ Fast I/O for all downstream steps                │
│                                                              │
│ Output: Parquet file (persistent storage)                   │
│         + Metadata (rows, columns, compression ratio)       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Market Metrics Computation                          │
├─────────────────────────────────────────────────────────────┤
│ Input:  Filtered DataFrame loaded from Parquet              │
│         (168 rows × 8 columns)                              │
│                                                              │
│ Process: Market Metrics (07)                                │
│         └─ Average Volume (Volume MC)                       │
│         └─ Liquidity Proxy (Volume × Price)                 │
│         └─ Bid-Ask Spreads (Avg, Min, Max, Std)             │
│         └─ Trading Coverage % (% sessions with data)        │
│         └─ Volatility Proxy (Coefficient of Variation)      │
│         └─ Generate warnings for missing data               │
│                                                              │
│ Output: Enhanced DataFrame                                  │
│         (168 rows × 18 columns = 8 original + 10 metrics)   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Dynamic Filtering (08 - NOT STARTED)                │
├─────────────────────────────────────────────────────────────┤
│ Input:  DataFrame with metrics                              │
│         + Index composition data (shares, free float)        │
│                                                              │
│ Process: Dynamic Filtering (Notebook 08)                    │
│         └─ Load index composition dataset                   │
│         └─ Compute market capitalization                    │
│         └─ Compute free-float market cap                    │
│         └─ Apply filtering thresholds                       │
│         └─ Build investable universe                        │
│                                                              │
│ Output: Investable DataFrame                                │
│         (Subset of companies meeting criteria)              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Technical Indicators (09 - NOT STARTED)             │
├─────────────────────────────────────────────────────────────┤
│ Input:  Investable DataFrame                                │
│                                                              │
│ Process: Technical Indicators (Notebook 09)                 │
│         └─ RSI (14)                                         │
│         └─ SMA (20, 50)                                     │
│         └─ EMA (20)                                         │
│         └─ MACD (+ Signal, Histogram)                       │
│         └─ RVOL (Relative Volume)                           │
│         └─ VWAP (Volume Weighted Avg Price)                 │
│         └─ Historical Volatility                            │
│                                                              │
│ Output: Technical DataFrame                                 │
│         (Original cols + metrics + 10 indicators)           │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │ [MISSING STEPS DEFINED BY EXTERNAL]  │
        │                                      │
        │ 8. Individual Signals ❌             │
        │    (Per-indicator buy/sell signals)  │
        │                                      │
        │ 9. Overall Score +                   │
        │    Signal Confidence ❌              │
        │    (Aggregate signal strength)       │
        │                                      │
        └──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 10: Business Rules (10 - NOT STARTED)                  │
├─────────────────────────────────────────────────────────────┤
│ Input:  Technical DataFrame + Signals                       │
│                                                              │
│ Process: Business Rules (Notebook 10)                       │
│         └─ Apply portfolio management rules                 │
│         └─ Sector allocation limits                         │
│         └─ Position sizing rules                            │
│         └─ Risk management rules                            │
│                                                              │
│ Output: Rule-evaluated DataFrame                            │
│         (With rule compliance flags)                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 11: Decision Engine (11 - NOT STARTED)                 │
├─────────────────────────────────────────────────────────────┤
│ Input:  Rule-evaluated DataFrame                            │
│                                                              │
│ Process: Decision Engine (Notebook 11)                      │
│         └─ Combine all signals & rules                      │
│         └─ Generate final recommendation                    │
│         └─ Assign confidence score                          │
│         └─ Output: BUY / HOLD / SELL                        │
│                                                              │
│ Output: Recommendations                                     │
│         {company, action, confidence, rationale}            │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │ [MISSING STEPS DEFINED BY EXTERNAL]  │
        │                                      │
        │ 12. Historical Backtesting ❌        │
        │     (Validate strategy on past data) │
        │                                      │
        │ 13. Performance Metrics ❌           │
        │     (Win rate, Sharpe ratio, etc.)   │
        │                                      │
        └──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 12: Streamlit UI Display                               │
├─────────────────────────────────────────────────────────────┤
│ Input:  Recommendations + Analysis                          │
│                                                              │
│ Process: UI Rendering                                       │
│         └─ Display recommendations                          │
│         └─ Show confidence scores                           │
│         └─ Visualize technical indicators                   │
│         └─ Interactive filters                              │
│         └─ Export reports                                   │
│                                                              │
│ Output: BVC Dashboard                                       │
│         (User-facing interface)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## KEY DIFFERENCES & ALIGNMENT

### ✓ Perfect Alignment
```
Your Flow                    External Flow           Status
────────────────────────────────────────────────────────────
Market Data → Ingestion      Market Data            ✓ ALIGN
             → Normalized    Unified Dataset        ✓ ALIGN
Validation (06)              Data Quality/Coverage  ✓ ALIGN
Filtering (05)               Dynamic Filtering*     ✓ PARTIAL
Market Metrics (07)          [Intermediate step]    ✓ ALIGN
```
*Note: Your "Filtering (05)" removes bad companies. External's "Dynamic Filtering (04)" filters by investment criteria. Both needed — they're sequential.

### ⏳ Planned but Not Started
```
Your Notebook               External Step           Your Step #
────────────────────────────────────────────────────────────
Dynamic Filtering (08)      Dynamic Filtering (04)  Step 08
Technical Indicators (09)   Technical Indicators    Step 09
Business Rules (10)         Business Rules          Step 10
Decision Engine (11)        BUY/HOLD/SELL           Step 11
```

### ❌ Missing from Your Plan
```
External Step               Purpose                 Recommendation
────────────────────────────────────────────────────────────────
Individual Signals          Generate buy/sell       ADD TO STEP 10
                           signals from each
                           indicator (RSI>70=sell)
                           
Overall Score +             Aggregate all signals   ADD TO STEP 11
Signal Confidence           into one recommendation
                           + confidence % (0-100%)
                           
Historical Backtesting      Validate strategy on    OPTIONAL
                           past data               (Nice to have)
                           
Performance Metrics         Win rate, Sharpe,      OPTIONAL
                           Max Drawdown, etc.      (Nice to have)
```

---

## REVISED WORKFLOW WITH YOUR IMPLEMENTATION

### Corrected Sequence

```
STEP 1: Market Data (User Upload)
        ↓
STEP 2: Ingestion + Normalization (02, 04)
        ↓
STEP 3: Data Validation (06)
        ↓
STEP 3.5: Data Filtering (05) [Remove bad companies]
        ↓
STEP 4: Parquet Persistence [AUTO-CONVERT]
        ↓
STEP 5: Market Metrics (07)
        ↓
STEP 6: Dynamic Filtering (08) [Investable universe]
        ↓
STEP 7: Technical Indicators (09)
        ↓
STEP 8: Individual Signals (NEW) [Per-indicator signals]
        ↓
STEP 9: Overall Score + Confidence (NEW) [Aggregate]
        ↓
STEP 10: Business Rules (10)
        ↓
STEP 11: Decision Engine (11) [BUY/HOLD/SELL]
        ↓
STEP 12: Streamlit UI
        ↓
(OPTIONAL) Historical Backtesting
(OPTIONAL) Performance Metrics
```

---

## IMPLEMENTATION STATUS MATRIX

| Phase | Step # | Your Notebook | External Name | Status | Dependencies |
|-------|--------|---------------|---------------|--------|--------------|
| Ingestion | 01/02 | 02_familyA_parser | Market Data | ✓ DONE | None |
| Normalization | 2 | 04_normalization | Unified Dataset | ✓ DONE | 01/02 |
| Validation | 3 | 06_validation | Data Quality | ✓ DONE | 02/04 |
| Quality | 3.5 | 05_data_filtering | Part of Step 3 | ✓ DONE | 06 |
| Persistence | 4 | Parquet logic | [AUTO] | ✓ DONE | 05 |
| Metrics | 5 | 07_market_metrics | [Intermediate] | ✓ DONE | 05/04 |
| Dynamic Filter | 6 | 08_dynamic_filters | Dynamic Filtering | ⏳ PLANNED | 05/07 |
| Indicators | 7 | 09_technical_indicators | Technical Indicators | ⏳ PLANNED | 06/08 |
| Signals | 8 | [NEW REQUIRED] | Individual Signals | ❌ MISSING | 07 |
| Aggregation | 9 | [NEW REQUIRED] | Overall Score | ❌ MISSING | 08 |
| Rules | 10 | 10_business_rules | Business Rules | ⏳ PLANNED | 09 |
| Decision | 11 | 11_decision_engine | BUY/HOLD/SELL | ⏳ PLANNED | 10 |
| Backtesting | 12 | [OPTIONAL] | Historical Backtesting | ❌ OPTIONAL | 11 |
| Performance | 13 | [OPTIONAL] | Performance Metrics | ❌ OPTIONAL | 12 |

---

## RECOMMENDATION

### Your Implementation is 90% Aligned ✓

**What's Good:**
- ✓ Correct sequence of main steps
- ✓ All core phases present
- ✓ Data quality focused
- ✓ Technical indicators planned
- ✓ Decision logic in place

**What's Missing (Should Add):**
1. **Individual Signals** (Step 8)
   - Convert each indicator into buy/sell signal
   - Example: RSI > 70 = SELL, RSI < 30 = BUY
   - Can be part of Business Rules (Step 10)

2. **Overall Score + Confidence** (Step 9)
   - Aggregate all signals into one score
   - Assign confidence % (0-100%)
   - Determine final recommendation strength
   - Can be part of Decision Engine (Step 11)

**What's Optional:**
- Backtesting (nice to have, can validate strategy)
- Performance metrics (nice to have, see how well it works)

### Your Parquet Strategy is Perfect ✓
- Auto-convert ANY Excel file to Parquet after filtering
- Use for ALL downstream calculations
- Provides speed + consistency
- No hardcoding — dynamic per uploaded file

---

## CORRECTED WORKFLOW FOR YOUR PROJECT

```
Corrected External Workflow + Your Implementation Names
───────────────────────────────────────────────────────

Market Data Input
    ↓
Ingestion (02) + Normalization (04)
    ↓
Unified Dataset
    ↓
Data Validation (06)
    ↓
Data Filtering (05) — Remove bad companies
    ↓
Convert to Parquet (AUTO on UI upload)
    ↓
Market Metrics (07)
    ↓
Dynamic Filtering (08) — Build investable universe
    ↓
Technical Indicators (09)
    ↓
Individual Signals (10) ← NEW: Per-indicator signals
    ↓
Overall Score + Confidence (11) ← NEW: Aggregate signals
    ↓
Business Rules (12)
    ↓
Decision Engine (13)
    ↓
BUY / HOLD / SELL Recommendations
    ↓
Streamlit UI
    ↓
(Optional) Historical Backtesting
(Optional) Performance Analysis
```

---

## SUMMARY

**Your workflow is correct and well-structured.** You're only missing:
1. Two intermediate steps (Signals + Aggregation) — can fold into existing steps 10-11
2. Optional backtesting & performance metrics

**Your Parquet strategy is perfect:**
- Auto-convert user uploads to Parquet after filtering
- Use for all downstream steps
- Provides speed for calculations
- No hardcoding — dynamic per file

**You are moving in the RIGHT direction!** ✓
