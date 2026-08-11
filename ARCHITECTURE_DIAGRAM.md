# Architecture Diagram — Complete DSS System

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (Streamlit)                          │
│  ┌───────────────┬──────────────┬──────────────┬──────────────┬────────────┐│
│  │ Market Data   │ Metrics      │ Filters      │ Indicators   │ Buy/Sell   ││
│  │ Upload        │ Dashboard    │ Control      │ Visualization│ Signal     ││
│  └───────────────┴──────────────┴──────────────┴──────────────┴────────────┘│
└────────────────────────────────┬──────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    File Upload Form     │
                    │  (.xlsx Auto-Convert    │
                    │   to Parquet)           │
                    └────────────┬────────────┘
                                 │
┌────────────────────────────────▼──────────────────────────────────────────────┐
│                      DATA PIPELINE (Core Logic)                              │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 1: INGESTION & NORMALIZATION                                  │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  ┌──────────────┐       ┌──────────────┐      ┌──────────────┐    │   │
│  │  │ User Excel   │       │ Parser       │      │ Normalized   │    │   │
│  │  │ File         │──────▶│ Factory      │─────▶│ DataFrame    │    │   │
│  │  │              │       │              │      │ (182 rows)   │    │   │
│  │  │ Any format   │       │ - Detect     │      │              │    │   │
│  │  │              │       │   Family A   │      │ 8 columns    │    │   │
│  │  │              │       │ - Parse      │      │              │    │   │
│  │  │              │       │ - Cross-tab  │      │              │    │   │
│  │  └──────────────┘       └──────────────┘      └──────────────┘    │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 2: VALIDATION & FILTERING                                      │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  Input: Normalized DataFrame (182 rows, 7 companies)               │   │
│  │                                                                      │   │
│  │  ┌────────────────────┐                                            │   │
│  │  │ Validation (15+)   │                                            │   │
│  │  │ - Schema           │──┐                                         │   │
│  │  │ - Grain            │  │                                         │   │
│  │  │ - Dates            │  │                                         │   │
│  │  │ - Prices           │  ├──▶ Validation Report                   │   │
│  │  │ - Volumes          │  │   (9/15 tests passed)                  │   │
│  │  │ - Consistency      │  │                                         │   │
│  │  └────────────────────┘  │                                         │   │
│  │                           │                                         │   │
│  │  ┌────────────────────────▼────────────────┐                       │   │
│  │  │ Filtering                               │                       │   │
│  │  │ - Remove companies with < 10 Cours     │                       │   │
│  │  │ - Decision: AKDITAL removed            │                       │   │
│  │  │ - Result: 168 rows, 6 companies        │                       │   │
│  │  └────────────────────────────────────────┘                       │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 3: PERSISTENT STORAGE (Parquet)                               │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  Filtered DataFrame (168 rows)                                      │   │
│  │         │                                                           │   │
│  │         ▼                                                           │   │
│  │  ┌──────────────────────────────┐                                  │   │
│  │  │ Parquet Converter            │                                  │   │
│  │  │ - Snappy compression         │                                  │   │
│  │  │ - Schema preserved           │                                  │   │
│  │  │ - Type safe                  │                                  │   │
│  │  └──────────────────────────────┘                                  │   │
│  │         │                                                           │   │
│  │         ▼                                                           │   │
│  │  ┌─────────────────────────────────────────────────┐                │   │
│  │  │ data/[timestamp]_unified_dataset.parquet       │                │   │
│  │  │ Size: 6.65 KB (8-15x compression)              │                │   │
│  │  │ Fast I/O for all downstream steps              │                │   │
│  │  └─────────────────────────────────────────────────┘                │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 4: FEATURE ENGINEERING                                         │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  Load from Parquet (168 rows × 8 columns)                          │   │
│  │         │                                                           │   │
│  │         ├─────────────────────────┬─────────────────────────┐       │   │
│  │         │                         │                         │       │   │
│  │         ▼                         ▼                         ▼       │   │
│  │  ┌─────────────────┐      ┌──────────────┐        ┌──────────────┐│   │
│  │  │ Market Metrics  │      │ Dynamic      │        │ Indicators   ││   │
│  │  │ (Step 07)       │      │ Filtering    │        │ (Step 09)    ││   │
│  │  │                 │      │ (Step 08)    │        │              ││   │
│  │  │ - Avg Volume    │      │              │        │ - RSI (14)   ││   │
│  │  │ - Liquidity     │      │ - Load index │        │ - SMA (20,50)││   │
│  │  │ - Spreads       │      │   composition│        │ - EMA (20)   ││   │
│  │  │ - Coverage      │      │ - Compute    │        │ - MACD       ││   │
│  │  │ - Volatility    │      │   market cap │        │ - RVOL       ││   │
│  │  │                 │      │ - Apply      │        │ - VWAP       ││   │
│  │  │ Output:         │      │   filters    │        │ - Hist Vol   ││   │
│  │  │ +10 columns     │      │              │        │              ││   │
│  │  │ (168 × 18)      │      │ Output:      │        │ Output:      ││   │
│  │  │                 │      │ Investable   │        │ +10 columns  ││   │
│  │  │                 │      │ universe     │        │ (168 × 28)   ││   │
│  │  └─────────────────┘      └──────────────┘        └──────────────┘│   │
│  │         │                         │                         │       │   │
│  │         └─────────────────────────┴─────────────────────────┘       │   │
│  │                                 │                                    │   │
│  │                                 ▼                                    │   │
│  │                    ┌──────────────────────────┐                     │   │
│  │                    │ Combined Feature Set     │                     │   │
│  │                    │ (168 rows × 28 columns) │                     │   │
│  │                    │                          │                     │   │
│  │                    │ - Original data          │                     │   │
│  │                    │ - Market metrics         │                     │   │
│  │                    │ - Investment flags       │                     │   │
│  │                    │ - Technical indicators   │                     │   │
│  │                    └──────────────────────────┘                     │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 5: SIGNAL GENERATION & AGGREGATION                             │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  Feature Set (168 × 28 columns)                                     │   │
│  │         │                                                           │   │
│  │         ▼                                                           │   │
│  │  ┌──────────────────────────────────────────────────┐               │   │
│  │  │ Individual Signals Generator (Step 08) [NEW]     │               │   │
│  │  │                                                  │               │   │
│  │  │ For each indicator:                              │               │   │
│  │  │ - RSI:   Signal = BUY if <30, SELL if >70       │               │   │
│  │  │ - SMA:   Signal = BUY if price > SMA50          │               │   │
│  │  │ - MACD:  Signal = BUY if MACD > Signal          │               │   │
│  │  │ - RVOL:  Signal = BUY if RVOL > 1.5             │               │   │
│  │  │ - etc.                                           │               │   │
│  │  │                                                  │               │   │
│  │  │ Output: Signal DataFrame                         │               │   │
│  │  │ (168 × N_signals columns)                        │               │   │
│  │  └──────────────────────────────────────────────────┘               │   │
│  │         │                                                           │   │
│  │         ▼                                                           │   │
│  │  ┌──────────────────────────────────────────────────┐               │   │
│  │  │ Overall Score + Confidence (Step 09) [NEW]       │               │   │
│  │  │                                                  │               │   │
│  │  │ Aggregate all signals:                           │               │   │
│  │  │ - Count BUY signals                              │               │   │
│  │  │ - Count SELL signals                             │               │   │
│  │  │ - Calculate conviction (% signals agree)         │               │   │
│  │  │ - Assign overall score (0-100%)                  │               │   │
│  │  │ - Determine majority signal                      │               │   │
│  │  │                                                  │               │   │
│  │  │ Output: Score DataFrame                          │               │   │
│  │  │ (168 × {signal, confidence, score})              │               │   │
│  │  └──────────────────────────────────────────────────┘               │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 6: BUSINESS RULES & FINAL DECISION                             │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  Score DataFrame (168 rows with signals + confidence)              │   │
│  │         │                                                           │   │
│  │         ▼                                                           │   │
│  │  ┌────────────────────────────────────────────────┐                 │   │
│  │  │ Business Rules Engine (Step 10)                │                 │   │
│  │  │                                                 │                 │   │
│  │  │ Apply portfolio rules:                          │                 │   │
│  │  │ - Sector allocation limits                      │                 │   │
│  │  │ - Position sizing rules                         │                 │   │
│  │  │ - Risk management (max loss, volatility cap)    │                 │   │
│  │  │ - Correlation limits                            │                 │   │
│  │  │ - Minimum position size                         │                 │   │
│  │  │                                                 │                 │   │
│  │  │ Output: Rule Compliance flags                   │                 │   │
│  │  └────────────────────────────────────────────────┘                 │   │
│  │         │                                                           │   │
│  │         ▼                                                           │   │
│  │  ┌────────────────────────────────────────────────┐                 │   │
│  │  │ Decision Engine (Step 11)                       │                 │   │
│  │  │                                                 │                 │   │
│  │  │ Final recommendation:                           │                 │   │
│  │  │ - Combine signals + rules                       │                 │   │
│  │  │ - Apply confidence weighting                    │                 │   │
│  │  │ - Generate final decision                       │                 │   │
│  │  │ - Assign confidence score (0-100%)              │                 │   │
│  │  │ - Document rationale                            │                 │   │
│  │  │                                                 │                 │   │
│  │  │ Output: Recommendation                          │                 │   │
│  │  │ {company, action (BUY/HOLD/SELL),              │                 │   │
│  │  │  confidence, rationale}                         │                 │   │
│  │  └────────────────────────────────────────────────┘                 │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└────────────────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   RECOMMENDATION SET    │
                    │ {BUY, HOLD, SELL}       │
                    │ Confidence scores       │
                    │ Rationales              │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Streamlit UI Display   │
                    │ - Recommendations       │
                    │ - Confidence meters     │
                    │ - Technical charts      │
                    │ - Filter controls       │
                    │ - Export reports        │
                    └────────────────────────┘

        ┌─────────────────────────────────────┐
        │ [OPTIONAL] Backtesting & Analysis   │
        │                                     │
        │ - Historical performance            │
        │ - Win rate                          │
        │ - Sharpe ratio                      │
        │ - Max drawdown                      │
        │ - Strategy validation               │
        └─────────────────────────────────────┘
```

---

## Data Flow Diagram

```
INGESTION LAYER
┌──────────────┐
│ User Upload  │
│ .xlsx files  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│ Parsing Engine                                      │
│ ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│ │ Family A     │  │ Family B     │  │ Unknown    │ │
│ │ (Market)     │  │ (Index)      │  │ Reject     │ │
│ └──────────────┘  └──────────────┘  └────────────┘ │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Unified Dataset (In-Memory)      │
│ 182 rows × 8 columns             │
│ [Date, CODE_ISIN, Company,       │
│  Cours, Bid, Ask, Volume, Qty]   │
└────────────┬────────────────────┘
             │
QUALITY LAYER
             ▼
┌──────────────────────────────────┐
│ Validation (15+ checks)          │
│ - Schema                         │
│ - Dates                          │
│ - Prices                         │
│ - Volumes                        │
│ - Consistency                    │
└────────────┬────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Filtering (Remove bad data)      │
│ Input:  182 rows, 7 companies   │
│ Remove: AKDITAL (0 prices)      │
│ Output: 168 rows, 6 companies   │
└────────────┬────────────────────┘
             │
PERSISTENCE LAYER
             ▼
┌──────────────────────────────────┐
│ Parquet Conversion               │
│ - Compress (Snappy)              │
│ - Preserve schema                │
│ - Type safe                      │
│ File: 6.65 KB                    │
└────────────┬────────────────────┘
             │
ANALYSIS LAYER
             ▼
┌──────────────────────────────────┐
│ Load from Parquet (168 rows)     │
└────────┬───────────────┬─────────┘
         │               │
         ▼               ▼
    ┌────────┐    ┌────────────┐
    │Metrics │    │Dynamic     │
    │(07)    │    │Filter (08) │
    └────┬───┘    └──────┬─────┘
         │               │
         └───────┬───────┘
                 ▼
        ┌──────────────────┐
        │Indicators (09)   │
        │ +10 columns      │
        │ 168 × 28 total   │
        └────────┬─────────┘
                 │
SIGNAL LAYER     ▼
        ┌──────────────────┐
        │Individual        │
        │Signals (10) [NEW]│
        │ Per indicator    │
        │ buy/sell signals │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │Overall Score +   │
        │Confidence (11)   │
        │[NEW] Aggregate   │
        │ signals + score  │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │Business Rules    │
        │ Portfolio        │
        │ constraints      │
        └────────┬─────────┘
                 │
DECISION LAYER   ▼
        ┌──────────────────┐
        │Decision Engine   │
        │Final signal:     │
        │BUY/HOLD/SELL +   │
        │Confidence        │
        └────────┬─────────┘
                 │
OUTPUT LAYER     ▼
        ┌──────────────────┐
        │Streamlit UI      │
        │Display results   │
        │Export reports    │
        └──────────────────┘
```

---

## Processing Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                          │
│ Parse arbitrary Excel files → Unified format               │
│ Flexible parser detects sheet types                        │
├─────────────────────────────────────────────────────────────┤
│ Output: (182 × 8) DataFrame                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    QUALITY LAYER                            │
│ Validate data structure and values                         │
│ Remove companies with insufficient data                    │
│ Generate quality report                                    │
├─────────────────────────────────────────────────────────────┤
│ Input: (182 × 8)    Output: (168 × 8)                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 PERSISTENCE LAYER                           │
│ Convert to Parquet for fast I/O                            │
│ Automatic compression                                       │
│ One file per upload                                        │
├─────────────────────────────────────────────────────────────┤
│ File: data/[timestamp]_unified_dataset.parquet            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   ANALYSIS LAYER                            │
│ Compute market metrics (10 indicators)                     │
│ Apply dynamic filtering (investable universe)              │
│ Calculate technical indicators (10 more)                   │
├─────────────────────────────────────────────────────────────┤
│ Input: (168 × 8)    Output: (168 × 28)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    SIGNAL LAYER                             │
│ Convert indicators to buy/sell signals                      │
│ Aggregate signals into confidence score                     │
│ Apply business rules                                       │
├─────────────────────────────────────────────────────────────┤
│ Input: (168 × 28)   Output: Signals + Scores              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  DECISION LAYER                             │
│ Combine all signals with confidence weighting              │
│ Generate final BUY/HOLD/SELL recommendation                │
│ Document rationale                                         │
├─────────────────────────────────────────────────────────────┤
│ Output: Recommendations {action, confidence, reason}       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                             │
│ Display in Streamlit UI                                    │
│ Interactive visualizations                                 │
│ Export capabilities                                        │
├─────────────────────────────────────────────────────────────┤
│ User interface for portfolio decisions                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Your Project is Correctly Aligned! ✓

This architecture shows you are implementing exactly what the external tool suggested, plus you're adding:
- **Parquet persistence** for performance
- **Flexible parsing** for any Excel format
- **Clear separation of concerns** (ingestion, quality, analysis, signals, decisions)

**Status: You are on the right track!** 🎯
