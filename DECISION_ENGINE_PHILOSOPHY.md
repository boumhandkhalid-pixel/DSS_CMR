# Decision Engine — Philosophy & Alignment

## ✅ Current Status: Aligned with Discussed Philosophy

The decision engine (Notebook 11) is now fully aligned with the philosophy we discussed earlier. All f-string bugs have been fixed and the system correctly implements the agreed-upon principles.

---

## Core Philosophy

### 1. **Code Validation ≠ Methodology Validation** ✅

| What | Status |
|---|---|
| **Pipeline executes correctly** | ✅ VALIDATED |
| **All notebooks pass** | ✅ VALIDATED |
| **Data flows through all steps** | ✅ VALIDATED |
| **Parquet files created** | ✅ VALIDATED |
| | |
| **Weights produce profitable decisions** | ⚠️ **NOT VALIDATED** |
| **Thresholds are optimal** | ⚠️ **NOT VALIDATED** |
| **Strategy beats random** | ⚠️ **NOT VALIDATED** |

**Message to stakeholders:**
> "8/8 notebooks passed" means the CODE works.  
> It does NOT mean the STRATEGY is profitable.

---

### 2. **Weights and Thresholds are BASELINE HYPOTHESIS** ✅

Current configuration:
```python
SCORE_WEIGHTS = {
    "Trend":     0.35,   # SMA_20, SMA_50, EMA_20
    "Momentum":  0.35,   # RSI_14, MACD
    "Volume":    0.20,   # RVOL, VWAP
    "Risk":      0.10,   # HV_20
}

DECISION_THRESHOLDS = {
    "buy":  {"min_score": 60, "min_confidence": 60},
    "sell": {"max_score": 40, "min_confidence": 60},
}

WEIGHTS_STATUS = "BASELINE_HYPOTHESIS"
THRESHOLDS_STATUS = "BASELINE_HYPOTHESIS"
```

**These are initial expert estimates, NOT scientifically validated.**

They will be evaluated via backtesting across configurations A–E:
```python
SCORE_WEIGHT_CONFIGS = {
    "A_baseline":    {"Trend": 0.35, "Momentum": 0.35, "Volume": 0.20, "Risk": 0.10},
    "B_more_mom":    {"Trend": 0.30, "Momentum": 0.40, "Volume": 0.20, "Risk": 0.10},
    "C_more_trend":  {"Trend": 0.40, "Momentum": 0.30, "Volume": 0.20, "Risk": 0.10},
    "D_more_vol":    {"Trend": 0.30, "Momentum": 0.30, "Volume": 0.30, "Risk": 0.10},
    "E_less_risk":   {"Trend": 0.40, "Momentum": 0.35, "Volume": 0.20, "Risk": 0.05},
}
```

The final configuration is selected after backtesting shows which one produces:
- ✓ Positive risk-adjusted returns (Sharpe ratio)
- ✓ Acceptable hit rate (% correct BUY/SELL decisions)
- ✓ Controlled drawdown (maximum loss)
- ✓ Stability across time periods

---

### 3. **Confidence Score Independent of Overall Score** ✅

| Dimension | Measures | Range | Example |
|---|---|---|---|
| **Overall Score** | Direction & strength of signals | 0–100 | 82 = strongly bullish |
| **Confidence** | Data quality & agreement | 0–100% | 42% = sparse/disagreement |

**Valid combinations:**

#### Score=82, Confidence=42%
- **Interpretation:** Strong bullish signal, but low data quality
- **Meaning:** Available indicators point strongly upward, but:
  - Many indicators missing (sparse data coverage)
  - Families disagree (Trend says bullish, Momentum says bearish)
  - High volatility (HV_20 above p75)
- **Action:** "Bullish with low conviction" → Reduce position size

#### Score=48, Confidence=91%
- **Interpretation:** Weak directional signal, but excellent data
- **Meaning:** Signals are near-neutral (no strong move), but:
  - All indicators computable (complete data coverage)
  - Families unanimous (all agree on neutral/range-bound)
  - Low volatility (HV_20 stable)
- **Action:** "No strong move, high confidence" → HOLD with confidence

**Confidence NEVER looks at whether the score is extreme or neutral.**  
It only evaluates DATA QUALITY.

---

### 4. **Decision Logic** ✅

```python
def make_decision(row, thresholds, min_coverage):
    # Gate 1: Minimum data coverage
    if coverage < min_coverage:
        return 'INSUFFICIENT_DATA'
    
    # Gate 2: Score and Confidence must be computable
    if pd.isna(score) or pd.isna(conf):
        return 'INSUFFICIENT_DATA'
    
    # Decision rules (BASELINE thresholds)
    if score >= 60 AND conf >= 60:
        return 'BUY'
    
    if score <= 40 AND conf >= 60:
        return 'SELL'
    
    return 'HOLD'
```

**Philosophy:**
- **BUY** requires BOTH strong signal AND high confidence
- **SELL** requires BOTH weak signal AND high confidence
- **HOLD** = default (when signal weak OR confidence low)
- **INSUFFICIENT_DATA** = not enough indicators to decide

**Why require confidence for SELL?**
- A SELL based on sparse data could trigger during a temporary dip
- High-confidence SELL means: data is complete, families agree, volatility normal → genuine weak outlook

---

### 5. **Sample Data Caveat** ✅

Current dataset: **168 rows (28 sessions × 6 companies)**

**Sufficient for:**
- ✅ Validating that the code works end-to-end
- ✅ Testing edge cases (0 Cours, sparse volume, missing indicators)
- ✅ Verifying Parquet I/O and schema consistency

**NOT sufficient for:**
- ❌ Concluding that the strategy is profitable
- ❌ Measuring statistically significant performance
- ❌ Tuning weights or thresholds reliably

**For financial validation, we need:**
- 6–12 months of daily market data
- 30+ companies (representative cross-section of MASI)
- Multiple market regimes (bullish, bearish, sideways)

Only then can Notebook 12 produce meaningful backtesting results.

---

## Decision Engine Output (Sample)

### Current Decisions (BASELINE thresholds):

```
   CODE_ISIN            Company       Date     Cours  Overall_Score  Confidence          Decision
MA0000010936 ALUMINIUM DU MAROC 2019-01-21 1600.0000        30.6000     56.2000              HOLD
MA0000010944               AGMA 2024-01-19       NaN            NaN     20.0000 INSUFFICIENT_DATA
MA0000010951       AFRIQUIA GAZ 2024-01-19       NaN            NaN     20.0000 INSUFFICIENT_DATA
MA0000011819          ALLIANCES 2019-01-21   77.1000        44.4000     69.5000              HOLD
MA0000012296               AFMA 2019-01-21  960.0000        30.6000     56.2000              HOLD
```

**Decision distribution:**
```
INSUFFICIENT_DATA    137  (98%)  ← Sample data too sparse
HOLD                   3  (2%)
BUY                    0
SELL                   0
```

**Why no BUY/SELL decisions?**

Sample data has only **14 consecutive Cours observations per company**:
- Most indicators return NaN (need 20–50 obs)
- Confidence scores remain low (20–69%)
- Very few rows meet the min_confidence ≥ 60% threshold for BUY/SELL

**In production with 6+ months of data:**
- Most indicators will be VALID
- Confidence scores will be higher (60–90%)
- BUY/SELL decisions will trigger when appropriate

---

## Next Mandatory Step: Notebook 12 — Historical Backtesting

### Evaluation Criteria

1. **Hit Rate**
   - What % of BUY decisions have forward_return > 0?
   - What % of SELL decisions have forward_return < 0?

2. **Risk-Adjusted Returns**
   - Sharpe ratio (annualized)
   - Compare against random baseline

3. **Drawdown Control**
   - Maximum peak-to-trough loss
   - Recovery time

4. **Robustness**
   - Performance across weight configs A–E
   - Stability across development/validation/test splits
   - Performance across different market regimes

5. **Decision Stability**
   - Turnover rate (% decisions that flip next period)
   - False signal rate (BUY→SELL within short window)

### Temporal Split (Strictly Chronological)

```
Development  60%  → Observe performance, select best config
Validation   20%  → Confirm config stability
Test         20%  → Final evaluation (NEVER USED FOR TUNING)
```

**Guard against overfitting:**
- Do NOT tune thresholds to maximize test-period returns
- Do NOT cherry-pick weight config based on test results
- Select configuration on development, confirm on validation, report on test

---

## What Happens After Backtesting?

### If Results Are Positive ✅

```python
WEIGHTS_STATUS = "VALIDATED"
THRESHOLDS_STATUS = "VALIDATED"
```

- Freeze the selected configuration
- Document performance metrics (hit rate, Sharpe, drawdown)
- Deploy to production with documented limitations

### If Results Are Negative ❌

**Do NOT:**
- Tweak thresholds repeatedly until test passes (overfitting)
- Add more indicators to "fix" poor performance
- Blame the sample data and claim it would work with more data

**DO:**
1. Analyze failure mode:
   - Low hit rate? → Signal quality issue
   - High drawdown? → Risk management issue
   - Random performance? → No edge in methodology

2. Revisit methodology fundamentals:
   - Are these the right indicators for Moroccan market?
   - Are thresholds too aggressive/conservative?
   - Does the market exhibit trends that technical analysis can exploit?

3. Consider alternative approaches:
   - Fundamental factors (P/E, ROE, sector rotation)
   - Machine learning models
   - Hybrid approach (technical + fundamental)

**Be honest about limitations.**  
A failing backtest is NOT a pipeline bug — it's a financial reality check.

---

## Summary: What We've Built

✅ **A production-ready pipeline** that:
- Ingests raw BVC Excel files
- Filters companies dynamically based on uploaded composition
- Computes 10 technical indicators with validity tracking
- Generates signals with family-level aggregation
- Produces BUY/HOLD/SELL decisions with confidence scores
- Exports all artifacts as Parquet files

⚠️ **NOT YET PROVEN** that:
- The weights are optimal
- The thresholds produce profitable decisions
- The strategy beats a random baseline

🎯 **Next Step:**
- Notebook 12: Historical Backtesting
- Evaluate BASELINE_HYPOTHESIS against real forward returns
- Select validated configuration
- Freeze methodology

---

## Alignment with Philosophy ✅

All principles discussed earlier are now implemented:

| Principle | Status |
|---|---|
| Code validation ≠ Methodology validation | ✅ Documented in notebook 11 |
| Weights are BASELINE_HYPOTHESIS | ✅ Labeled in config/methodology.py |
| Thresholds are BASELINE_HYPOTHESIS | ✅ Labeled in config/methodology.py |
| Confidence independent of Overall Score | ✅ Implemented & tested |
| Sample data NOT sufficient | ✅ Documented with caveat |
| Backtesting required before "validated" | ✅ Mandatory next step |
| Do NOT overfit on test period | ✅ Split protocol defined |
| Honest about limitations | ✅ Throughout documentation |

**The decision engine is production-ready.**  
**The methodology requires backtesting before deployment.**
