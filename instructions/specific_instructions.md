---
# Refined System Prompt (v2)

Below is the additional section I would insert into your prompt.
---

# Data Flow (Updated)

The project uses **two completely independent datasets**.

They **must never be merged into a single master dataset.**

Each dataset has a different business purpose.

---

## Dataset 1 — Market Data

This dataset is generated from the official BVC workbook.

It contains historical market observations.

The normalization engine produces the following structure:

| Date | CODE ISIN | Company | Close Price | Bid | Ask | Volume MC | Quantity MC | ... |

Example

| Date       | CODE ISIN    | Company |  Bid |  Ask | Close | Volume MC | Quantity MC |
| ---------- | ------------ | ------- | ---: | ---: | ----: | --------: | ----------: |
| 2026-07-20 | MA0000012296 | AFMA    | 1230 | 1231 |  1231 |   2150000 |        1742 |
| 2026-07-21 | MA0000012296 | AFMA    | 1231 | 1232 |  1232 |   2340000 |        1955 |

Every row represents

```
One Company
×

One Trading Session
```

This dataset becomes the **single source of truth** for all historical market computations.

No downstream module should ever access the original Excel workbook.

---

## Dataset 2 — Index Composition

The second dataset is already normalized.

Each row represents one listed company belonging to one or more official BVC indices.

Typical columns include:

- Trading Session
- Index
- CODE ISIN
- Instrument
- Number of Shares
- Free Float Factor
- Capping Factor
- Free Float Market Capitalization
- Weight

This dataset must remain independent.

It must **never be merged into the historical market dataset.**

---

# Relationship Between Both Datasets

The datasets have different responsibilities.

### Dataset 1

Used for

- historical analysis
- technical indicators
- rolling statistics
- market metrics
- time-series calculations

### Dataset 2

Used for

- defining the investable universe
- index membership
- free float filtering
- liquidity constraints
- portfolio construction
- dynamic filtering

The Index Composition dataset should only be consulted during the **Dynamic Filtering** stage.

---

# Special Handling of the "Data" Worksheet

The worksheet named **Data** belongs to **Family B**.

It contains numerous derived financial attributes such as:

- Historical Volatility
- VWAP
- 52W High
- 52W Low
- Performance
- Other exchange-calculated statistics

The parser **must detect** this worksheet.

The parser **must validate** its structure.

However,

**its content must NOT be integrated into the normalized historical dataset.**

Reason:

The DSS must compute its own indicators from raw market observations.

Including already-computed exchange indicators would introduce redundancy, complicate data lineage, and risk inconsistencies.

Therefore:

✓ Detect it

✓ Validate it

✓ Ignore it during normalization

---

# Technical Indicators

Technical indicators are computed **only** from the normalized historical market dataset.

Never use the Index Composition dataset for technical indicator computation.

Compute

- RSI (14)
- SMA 20
- SMA 50
- EMA 20
- MACD
- MACD Signal
- MACD Histogram
- RVOL
- VWAP
- Historical Volatility

Append new columns only.

Never overwrite existing columns.

---

# Dynamic Filtering

Dynamic Filtering operates **after** the technical indicators have been computed.

The filtering engine combines

- latest technical indicators
- latest market metrics
- Index Composition information

to determine the eligible investment universe.

Possible filtering criteria include

- Index Membership
- Free Float
- Weight
- Liquidity
- Average Volume
- Free Float Market Capitalization
- Capping Factor

Filtering rules must remain configurable.

No hardcoded thresholds.

---

# Updated Pipeline

```text
Import Official BVC Workbook
            │
            ▼
Read Worksheets
            │
            ▼
Worksheet Detection
(Family A / Family B)
            │
            ▼
Parsing
            │
            ▼
Normalization
(Date × CODE ISIN)
            │
            ▼
Data Quality Validation
            │
            ▼
Technical Indicators
            │
            ▼
Market Metrics
            │
            ▼
Dynamic Filtering
        ▲
        │
Index Composition Dataset
        │
        ▼
Business Rules Engine
            │
            ▼
BUY / HOLD / SELL
            │
            ▼
Confidence Score
```

---

# Engineering Rule

The **Normalization Engine** is the heart of the project.

The **Index Composition dataset is not another source of historical market data.**

Treat it as a **portfolio construction dataset**, not as a time-series dataset.

Never merge it into the normalized historical dataset.

Only consult it during the Dynamic Filtering stage.

---
