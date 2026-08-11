# Notebook 09 — Corrections Applied

## Issues Found & Fixed

### 1. F-String Bug in Cell 4
**Problem:** Double curly braces in f-strings caused literal output instead of variable interpolation

```python
# BEFORE (broken):
print(f'Shape: {{inv.shape}} | companies: {{inv["CODE_ISIN"].nunique()}}')
print(f'  {{g["Company"].iloc[0]:25s}} {{n:2d}}/{{len(g)}} sessions with Cours')

# AFTER (fixed):
print(f'Shape: {inv.shape} | companies: {inv["CODE_ISIN"].nunique()}')
print(f'  {g["Company"].iloc[0]:25s} {n:2d}/{len(g)} sessions with Cours')
```

**Result:**
```
# Before: literal curly braces appeared in output
Shape: {inv.shape} | companies: {inv["CODE_ISIN"].nunique()}

# After: proper variable values
Shape: (140, 11) | companies: 5
```

---

### 2. Misleading `1*` Notation in Documentation

**Problem:** Confusing asterisk notation didn't explain the difference between technical and reliable minimums

**BEFORE:**
| Family | Indicator | Min obs | Validity tracked |
|---|---|---|---|
| Trend | EMA_20 | 1* | ✓ |
| Momentum | RSI_14 | 14 | ✓ |
| Volume | RVOL | 1 | ✓ |

**AFTER:**
| Family | Indicator | Min obs (strict) | Min obs (reliable) | Validity tracked |
|---|---|---|---|---|
| Trend | EMA_20 | 1 | 20 (3× span) | ✓ |
| Momentum | RSI_14 | 15 | 15 | ✓ |
| Volume | RVOL | 1 | 20 | ✓ |
| Volume | VWAP | 1 | 1 (cumulative) | ✓ |

**Added clarification:**
> **Important distinction:**
> - **Min obs (strict)**: Technical minimum for formula to execute (may produce meaningless values)
> - **Min obs (reliable)**: Minimum for statistically meaningful result
>
> For example, EMA_20 uses `min_periods=1` (degrades gracefully), but results aren't reliable until ~20 observations.

---

## Explanation: Why EMA_20 Has Two Minimums

### The Code
```python
g.loc[mask,'EMA_20'] = pr.ewm(span=P['ema_short'], adjust=False, min_periods=1).mean().values
#                                                                   ↑↑↑↑↑↑↑↑↑↑↑↑
```

### The Issue
With `min_periods=1`:
- **After 1 observation**: EMA_20 = that single price → **meaningless**
- **After 2 observations**: EMA starts exponential weighting
- **After ~20 observations**: EMA_20 becomes **statistically reliable** (≈3× span)

### The Solution
Document both minimums:
- **Strict (1)**: Formula executes, prevents NaN
- **Reliable (20)**: Result is financially meaningful

This makes it clear that EMA_20 with only 1-5 observations is technically valid but financially unreliable.

---

## Verification Results

✅ **All 9 cells execute successfully**
✅ **F-string output now correct** (prints actual company names and counts)
✅ **Documentation clear** (no more confusing asterisks)
✅ **Validity tracking working** (10 Valid_{indicator} columns added)

### Sample Output (Cell 4)
```
Shape: (140, 11) | companies: 5
   CODE_ISIN            Company
MA0000010936 ALUMINIUM DU MAROC
MA0000010944               AGMA
MA0000010951       AFRIQUIA GAZ
MA0000011819          ALLIANCES
MA0000012296               AFMA

Cours coverage per company:
  ALUMINIUM DU MAROC        14/28 sessions with Cours
  AGMA                      14/28 sessions with Cours
  AFRIQUIA GAZ              14/28 sessions with Cours
  ALLIANCES                 14/28 sessions with Cours
  AFMA                      14/28 sessions with Cours
```

---

## Summary

**Fixed:**
1. F-string bugs in cell 4 (double braces → single braces)
2. Misleading `1*` notation → clear two-column format
3. Added explicit explanation of strict vs reliable minimums

**Impact:**
- Code now executes correctly with proper output
- Documentation is clear and unambiguous
- Users understand why indicators may be technically valid but financially unreliable

**Status:** ✅ Production-ready
