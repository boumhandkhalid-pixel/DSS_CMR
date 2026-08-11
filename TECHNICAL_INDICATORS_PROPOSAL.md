# Technical Indicators — Calculation Approach Proposal

## Unified Dataset Status

### Dataset Overview
```
Shape: (182, 8)
- Records: 182 (7 companies × ~26 sessions each)
- Companies: 7 unique CODE_ISINs
- Date range: 2018-12-31 to 2024-01-19 (1,846 days)
- Sessions: 28 unique trading dates
```

### Structure
```
Columns:
1. Date (datetime64)    — Trading session date
2. CODE_ISIN (str)      — Unique company identifier
3. Company (str)        — Company name
4. Cours (float64)      — Close price [KEY FOR INDICATORS]
5. Bid (float64)        — Bid price
6. Ask (float64)        — Ask price
7. Volume MC (float64)  — Trading volume
8. Quantité MC (float64)— Trading quantity
```

### Data Quality for Technical Indicators
```
Company                 Records  Cours_Available  Coverage  Sufficient?
─────────────────────────────────────────────────────────────────────
MA0000010936  (ALUMINIUM)   28        14/28        50%        ✓ Yes
MA0000010944  (AGMA)        28        14/28        50%        ✓ Yes
MA0000010951  (AFRIQUIA)    28        14/28        50%        ✓ Yes
MA0000011819  (ALLIANCES)   28        14/28        50%        ✓ Yes
MA0000012114  (AFRIC INDUSTRIES) 28   14/28        50%        ✓ Yes
MA0000012296  (AFMA)        28        14/28        50%        ✓ Yes
MA0000012585  (AKDITAL)     14         0/14         0%        ⚠ Insufficient
```

**Key Issue:** AKDITAL has NO Cours data → cannot compute price-based indicators.

---

## Technical Analysis Library Status

### Available Libraries
- ✓ pandas (data manipulation)
- ✓ numpy (numerical operations)
- ✗ pandas-ta (not installed)
- ✗ TA-Lib (not installed)

### Decision: Manual Implementation
Since standard TA libraries are not available, we will implement all indicators manually using pandas/numpy. This approach:
- ✓ Maintains control over calculations
- ✓ Avoids external dependencies
- ✓ Clear documentation of each formula
- ✓ Easy to debug and validate

---

## Technical Indicators — Calculation Approach

### 1. RSI (Relative Strength Index, Period=14)

**Formula:**
```
RS = Average(Gains) / Average(Losses)
RSI = 100 - (100 / (1 + RS))
```

**Implementation:**
```python
def compute_rsi(prices, period=14):
    # Calculate price changes
    deltas = prices.diff()
    
    # Separate gains and losses
    gains = deltas.where(deltas > 0, 0)
    losses = -deltas.where(deltas < 0, 0)
    
    # Calculate average gains/losses (with smoothing)
    avg_gain = gains.rolling(period).mean()
    avg_loss = losses.rolling(period).mean()
    
    # Apply smoothing after first window
    for i in range(period, len(avg_gain)):
        avg_gain[i] = (avg_gain[i-1] * (period-1) + gains[i]) / period
        avg_loss[i] = (avg_loss[i-1] * (period-1) + losses[i]) / period
    
    # Calculate RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
```

**Expected Output:** Float values 0-100
**Minimum History Required:** 14+ periods
**Suitable for:** Momentum analysis, oversold/overbought signals

---

### 2. SMA (Simple Moving Average)

**Formula (Period=20, 50):**
```
SMA_20 = MEAN(Close[t-19:t])
SMA_50 = MEAN(Close[t-49:t])
```

**Implementation:**
```python
def compute_sma(prices, period):
    return prices.rolling(window=period, min_periods=1).mean()
```

**Expected Output:** Float values (same units as price)
**Minimum History Required:** 20 for SMA_20, 50 for SMA_50
**Suitable for:** Trend identification, support/resistance levels

---

### 3. EMA (Exponential Moving Average, Period=20)

**Formula:**
```
Multiplier = 2 / (Period + 1) = 2/21 ≈ 0.0952
EMA[t] = Close[t] × Multiplier + EMA[t-1] × (1 - Multiplier)
```

**Implementation:**
```python
def compute_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()
```

**Expected Output:** Float values (same units as price)
**Minimum History Required:** 20 periods (more reliable with more history)
**Suitable for:** Faster trend following vs SMA, crossover signals

---

### 4. MACD (Moving Average Convergence Divergence)

**Formula:**
```
MACD_Line = EMA(Close, 12) - EMA(Close, 26)
Signal_Line = EMA(MACD_Line, 9)
Histogram = MACD_Line - Signal_Line
```

**Implementation:**
```python
def compute_macd(prices):
    ema_12 = prices.ewm(span=12, adjust=False).mean()
    ema_26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
```

**Expected Output:** Three float series (can be positive or negative)
**Minimum History Required:** 26 periods (reliable with more)
**Suitable for:** Momentum changes, bullish/bearish crossovers

---

### 5. RVOL (Relative Volume)

**Formula:**
```
RVOL = Current_Volume / Average_Volume(20-period lookback)
```

**Implementation:**
```python
def compute_rvol(volumes, period=20):
    avg_volume = volumes.rolling(window=period, min_periods=1).mean()
    rvol = volumes / avg_volume
    return rvol
```

**Expected Output:** Float values (typically 0.5 to 2.0+)
**Minimum History Required:** 1 (but more reliable with 20)
**Suitable for:** Volume analysis, unusual trading activity detection
**Note:** Values > 1.0 = above average volume, < 1.0 = below average

---

### 6. VWAP (Volume Weighted Average Price)

**Formula:**
```
VWAP = Σ(Price × Volume) / Σ(Volume)
  
Cumulative from session start or reset period
```

**Implementation:**
```python
def compute_vwap(prices, volumes, reset_column=None):
    # If reset_column provided, reset at start of each group
    pv = prices * volumes
    cumsum_pv = pv.cumsum()
    cumsum_vol = volumes.cumsum()
    vwap = cumsum_pv / cumsum_vol
    return vwap
```

**Expected Output:** Float values (same units as price)
**Minimum History Required:** 1 (but cumulative from period start)
**Suitable for:** Average trading price, price level validation
**Important:** VWAP is typically cumulative from start of trading session/day

---

### 7. Historical Volatility

**Formula (20-period):**
```
Log_Returns = LN(Close[t] / Close[t-1])
Std_Dev = STDEV(Log_Returns, 20-period)
Annualized_Vol = Std_Dev × √252  (252 trading days/year)
```

**Implementation:**
```python
def compute_historical_volatility(prices, period=20, annualize=True):
    # Calculate log returns
    log_returns = np.log(prices / prices.shift(1))
    
    # Calculate rolling standard deviation
    volatility = log_returns.rolling(window=period, min_periods=1).std()
    
    if annualize:
        volatility = volatility * np.sqrt(252)
    
    return volatility
```

**Expected Output:** Float values (percentage as decimal, e.g., 0.25 = 25%)
**Minimum History Required:** 2 (but 20+ for meaningful value)
**Suitable for:** Risk assessment, option pricing, position sizing

---

## Implementation Strategy

### Phase 1: Notebook Testing (09_technical_indicators.ipynb)
1. Load unified dataset
2. Sort by CODE_ISIN + Date (chronological per company)
3. Implement each indicator separately
4. Calculate for each company independently
5. Validate calculations (sample checks)
6. Display results and visualizations
7. Handle edge cases (insufficient data, nulls)

### Phase 2: Data Handling

**Chronological Sort (Critical):**
```python
df = df.sort_values(['CODE_ISIN', 'Date']).reset_index(drop=True)
```

**Per-Company Calculation (Independent):**
```python
for isin in df['CODE_ISIN'].unique():
    company_df = df[df['CODE_ISIN'] == isin]
    # Calculate indicators for this company only
    # Merge back into main dataframe
```

**Missing Data Strategy:**
- NaN Cours → indicator = NaN (propagate)
- Insufficient history → first N rows = NaN until min_periods reached
- Zero Volume → VWAP/RVOL = NaN (to avoid division issues)

### Phase 3: Output Structure

**Dataset Enhancement:**
```
Input:  (182, 8)   — Date, CODE_ISIN, Company, Cours, Bid, Ask, Volume MC, Quantité MC
Output: (182, 18)  — Original 8 + 10 new indicator columns

New Columns:
1. RSI_14
2. SMA_20
3. SMA_50
4. EMA_20
5. MACD
6. MACD_Signal
7. MACD_Histogram
8. RVOL
9. VWAP
10. Historical_Vol_20
```

---

## Data Quality & Edge Cases

### Minimum Requirements for Indicators
```
Company              Cours_Records  Can_Calculate?  Issues
──────────────────────────────────────────────────────────
MA0000010936              14              ✓         OK (50% coverage, 14 records min)
MA0000010944              14              ✓         OK (50% coverage, 14 records min)
MA0000010951              14              ✓         OK (50% coverage, 14 records min)
MA0000011819              14              ✓         OK (100% coverage)
MA0000012114              14              ✓         OK (50% coverage)
MA0000012296              14              ✓         OK (50% coverage)
MA0000012585               0              ✗         NO COURS DATA → All indicators = NaN
```

### Handling Edge Cases

**Insufficient Data:**
- For RSI (14-period): first 13 rows = NaN
- For SMA_50: first 49 rows = NaN
- For MACD (26-period base): first 25 rows = NaN

**Missing Cours Data:**
- Row = NaN for all price-based indicators
- AKDITAL = all indicators = NaN (no price data)
- Some companies sparse dates → fill with NaN appropriately

**Zero or Negative Volumes:**
- RVOL = NaN (avoid division by zero)
- VWAP = NaN (volume weight = zero)

---

## Validation Strategy

### Sample Calculations to Verify
```
1. RSI Validation:
   - Check output range [0, 100]
   - Verify extremes: RSI > 70 = overbought, RSI < 30 = oversold
   
2. SMA Validation:
   - Compare with manual MEAN calculation
   - Verify first value = first N prices' average
   
3. EMA Validation:
   - Verify smooth curve between SMA and price
   - Check responds faster to recent changes
   
4. MACD Validation:
   - MACD crosses Signal line → trading signals
   - Histogram positive when MACD > Signal
   
5. RVOL Validation:
   - RVOL ≈ 1.0 when volume = average
   - Check for unusual spikes (RVOL > 2.0)
   
6. VWAP Validation:
   - VWAP should be between daily high and low
   - Cumulative nature → always increasing with volume
   
7. Historical Vol Validation:
   - Compare with pandas std() × √252
   - Reasonable values: typically 10-50% annually
```

---

## Next Steps

### Immediate (Notebook Phase)
1. ✓ Validate unified dataset structure
2. ✓ Propose calculation methods (THIS DOCUMENT)
3. → Implement notebook 09 with all indicators
4. → Test calculations and edge cases
5. → Display results and sample validations

### Later (Production Phase — Step 10)
- Move to src/technical_indicators.py
- Create comprehensive test suite
- UI integration in Streamlit
- Combine with business rules (Step 11)

---

## Summary: Ready to Implement

**Dataset Status:** ✓ Ready
**Library Status:** ✓ Manual implementation (numpy/pandas)
**Approach:** ✓ Defined for all 10 indicators
**Edge Cases:** ✓ Identified and strategies planned

**Key Takeaways:**
- 6 companies can compute all indicators
- 1 company (AKDITAL) has no price data → all NaN
- Minimum 14 Cours values needed for RSI
- Sort by CODE_ISIN + Date before calculating
- Each company calculated independently
- All indicators appended as new columns (182 rows → 182 rows)

Proceeding with notebook implementation...
