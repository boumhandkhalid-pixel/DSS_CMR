"""
DSS Methodology Configuration
==============================
All thresholds, weights and signal definitions live here.
The notebooks and production modules import from this file —
nothing is hardcoded in business logic.

IMPORTANT — DYNAMIC PIPELINE DESIGN
-------------------------------------
This system is NOT designed for a fixed dataset.
In production, the portfolio manager uploads two files via Streamlit:

    1. Market data file     (frequent — weekly / monthly)
       → Cours, Bid, Ask, Volume MC, Quantité MC

    2. Index composition file  (less frequent — monthly / quarterly)
       → Facteur flottant, Capitalisation flottante, Poids, Nb titres

The ETL pipeline runs on every upload.
The dynamic filter thresholds are NOT hardcoded absolute values —
they are percentile rules recalculated from the composition file
that was uploaded. This means:
  - A new composition file next month → new absolute thresholds
  - A different index selected → thresholds derived from that index
  - No code change required — only configuration

The reference data in /data/ and /samples/ serves only to
validate the notebooks. The Streamlit UI will compute all
thresholds dynamically at runtime.

Rationale for every value is documented inline.
"""

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# 1. DYNAMIC FILTERING
# ─────────────────────────────────────────────────────────────────────────────
# Thresholds are expressed as PERCENTILE RULES, not absolute values.
# The function compute_filter_thresholds(composition_df) translates
# these rules into absolute values at runtime, using the composition
# file uploaded by the portfolio manager.
#
# Strategy B – Moderate selected after comparing A/B/C on actual data.
# See notebook 08 for the full distribution analysis and comparison.

FILTER_CONFIG = {
    # Gate 1: index universe — securities must belong to this index.
    # Configurable: swap "MASI" for "MASI 20", "MASI ESG", etc.
    # The portfolio manager can change this in the UI without touching code.
    "index": "MASI",

    # Gate 2: Free Float Factor — minimum absolute value.
    # 0.20 corresponds to the natural lower step in BVC data.
    # Below 0.20, less than 20% of shares are freely tradeable —
    # any modest order moves the price (thin float = illiquid in practice).
    # This is an absolute threshold, not percentile-based, because
    # 0.20 has a clear financial meaning independent of the distribution.
    "min_free_float_factor": 0.20,

    # Gate 3: Free Float Market Capitalisation — expressed as a PERCENTILE.
    # At runtime, compute_filter_thresholds() converts this to the
    # actual MAD value from the uploaded composition file.
    # p25 removes only the bottom quartile of micro-caps.
    # → Do NOT hardcode the absolute value here.
    "min_ff_market_cap_percentile": 25,

    # Retained for reference (computed from 2026-07-31 file, n=79 MASI):
    # min_ff_market_cap ≈ 218_136_064 MAD at p25
    # This value will differ when a new composition file is uploaded.

    # Capping Factor: uniform 1.0 across all 79 MASI securities in this file.
    # No discriminative power — excluded from all filters.

    # Index Weight: used as a ranking variable only, NOT a hard filter.
    # A security can be investable with a low weight.
    "weight_as_ranking_only": True,

    # AvgVol20: NOT a hard gate (sample window too sparse for this dataset).
    # It enters the Confidence score instead.
    "min_avg_vol20": None,
}


def compute_filter_thresholds(composition_df):
    """
    Translate percentile rules in FILTER_CONFIG into absolute values,
    computed from the composition DataFrame uploaded by the portfolio manager.

    This is the key function that makes the pipeline dynamic:
    - Called once per upload of a new composition file
    - Returns a resolved config with absolute thresholds ready to use
    - No hardcoded MAD values anywhere in the codebase

    Parameters
    ----------
    composition_df : pd.DataFrame
        Parsed index composition file, already filtered to the selected index.
        Must contain columns: FF, FF_MarketCap, Weight.

    Returns
    -------
    dict with resolved absolute thresholds, plus distribution context.

    Example
    -------
    Upload: Compo_All_Indices_20261031.xlsx  (next quarter)
        → p25(FF_MarketCap) might be 230 M MAD instead of 218 M MAD
        → Filter automatically adapts — no code change needed
    """
    idx = composition_df["FF_MarketCap"].dropna()

    p_ffmc = FILTER_CONFIG["min_ff_market_cap_percentile"]

    resolved = {
        # carried over as-is (absolute value with clear financial meaning)
        "index":                  FILTER_CONFIG["index"],
        "min_free_float_factor":  FILTER_CONFIG["min_free_float_factor"],

        # computed dynamically from the uploaded file
        "min_ff_market_cap":      float(np.percentile(idx, p_ffmc)),

        # context — useful for reporting
        "n_securities":           len(composition_df),
        "ff_market_cap_p25":      float(np.percentile(idx, 25)),
        "ff_market_cap_median":   float(np.percentile(idx, 50)),
        "ff_market_cap_p75":      float(np.percentile(idx, 75)),
        "ff_median":              float(composition_df["FF"].median()),
        "source_percentile_rule": f"FF_MarketCap >= p{p_ffmc}",
    }
    return resolved


# ─────────────────────────────────────────────────────────────────────────────
# 1.5  DATA QUALITY FILTER — Minimum consecutive observations
# ─────────────────────────────────────────────────────────────────────────────
# The filter removes companies that do NOT have a long enough unbroken run
# of price observations.  "Unbroken" means no gap > MAX_GAP_DAYS between two
# successive non-null Cours values.
#
# Why consecutive, not just count?
# ─────────────────────────────────
# RSI and all moving-average indicators compute *differences* between
# adjacent rows.  A delta calculated across a multi-month gap (e.g. a 2019
# price compared with a 2024 price) is not a daily return — it is years of
# market move compressed into one step.  The formula still runs and produces
# a number, but that number is financially meaningless.
#
# Binding constraint: SMA_50 (largest window)
# ───────────────────────────────────────────
# SMA_50 needs 50 consecutive price observations to produce its first valid value.
# This is the strictest requirement among all price-based indicators.
# (RSI-14 needs 15, EMA-20 needs 20, MACD needs 27, SMA-20 needs 20)
#
# MAX_GAP_DAYS: Data Quality Heuristic
# ─────────────────────────────────────
# This is NOT a mathematical requirement of RSI or any indicator.
# It is a practical rule to distinguish:
#   - Normal gaps (weekends, occasional holidays): ≤ 7 days
#   - Abnormal gaps (missing trading sessions): > 7 days
#
# A gap > 7 days likely means at least 1-2 full trading sessions are missing.
#
# More rigorous approach (future improvement):
#   Use the official BVC trading calendar to detect exactly which sessions are missing,
#   rather than relying on a calendar-day threshold.
#
# Therefore:
# ═══════════════════════════════════════════════════════════════════════════════
# NOUVELLE APPROCHE: Coverage Graceful (Pas de rejet global sur MIN_CONSECUTIVE)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Philosophie:
#   - NE PAS rejeter un titre simplement parce qu'il n'a pas 50 observations
#   - Chaque indicateur gère son propre minimum (voir INDICATOR_MIN_OBS ci-dessous)
#   - Si un indicateur manque de données → NaN (pas de rejet du titre)
#   - Coverage et Confidence s'ajustent automatiquement
#   - Décision finale basée sur Data_Coverage global + Coverage par famille
#
# Pourquoi ?
#   - SMA-50 nécessite 50 obs, mais RSI-14 seulement 15 obs
#   - Rejeter un titre à 30 obs = perdre RSI, SMA-20, EMA-20, RVOL, VWAP, HV-20
#   - C'est du gaspillage d'information !
#
# Solution:
#   - Filtrer uniquement sur QUALITÉ TEMPORELLE (MAX_GAP_DAYS)
#   - Pas de trous > 7 jours entre observations
#   - Nombre d'observations = détermine quels indicateurs sont calculables
#
# ═══════════════════════════════════════════════════════════════════════════════

# MAX_GAP_DAYS: Qualité temporelle des données
# Rejette un titre si gap entre 2 observations consécutives > 7 jours
# (7 jours = weekend + quelques fériés)
MAX_GAP_DAYS: int = 7

# MIN_CONSECUTIVE: DEPRECATED (gardé pour compatibilité notebooks anciens)
# ⚠️ NE PLUS UTILISER comme filtre global
# ⚠️ Utilisé uniquement dans filter_companies_by_usable_data() legacy
MIN_CONSECUTIVE: int = 14  # Pour compatibilité backward uniquement
MIN_USABLE_ROWS: int = MIN_CONSECUTIVE  # Alias backward-compatible
MIN_USABLE_ROWS_SAMPLE_OVERRIDE: int = 1


# ─────────────────────────────────────────────────────────────────────────────
# 2. TECHNICAL INDICATOR PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

INDICATOR_PARAMS = {
    "sma_short":    20,   # SMA short window
    "sma_long":     50,   # SMA long window
    "ema_short":    20,   # EMA window
    "rsi_period":   14,   # RSI lookback (Wilder)
    "macd_fast":    12,   # MACD fast EMA
    "macd_slow":    26,   # MACD slow EMA
    "macd_signal":   9,   # MACD signal EMA
    "rvol_window":  20,   # RVOL denominator window
    "hv_window":    20,   # Historical Volatility window (log-return std)
    "hv_annualise": 252,  # trading days per year for annualisation
    # VWAP: cumulative within available date range (no intraday reset possible)
}

# Minimum valid observations required before an indicator can be computed.
# Rows below the minimum → NaN (never filled with zero or forward-fill).
INDICATOR_MIN_OBS = {
    "SMA_20":          20,
    "SMA_50":          50,
    "EMA_20":          20,   # reliable after 3× the span
    "RSI_14":          15,   # 14 deltas + 1 seed
    "MACD":            26,   # slow EMA window
    "MACD_Signal":     35,   # slow + signal windows
    "MACD_Histogram":  35,
    "RVOL":             1,   # degrades gracefully; meaningful at 20
    "VWAP":             1,   # cumulative; degrades gracefully
    "HV_20":           21,   # 20 log-return differences
}

# Computed once from the table above — import this in notebooks and src/
# MIN_USABLE_ROWS defined in section 1.5 above (= MIN_CONSECUTIVE = 14)

# ─────────────────────────────────────────────────────────────────────────────
# 3. INDIVIDUAL SIGNAL MAPPING
# ─────────────────────────────────────────────────────────────────────────────
# Each indicator maps to: BULLISH (+1), BEARISH (−1), or NEUTRAL (0).
# Thresholds are initial hypotheses — will be evaluated via backtesting.

SIGNAL_RULES = {
    # ── Trend ────────────────────────────────────────────────────────────
    "SMA_20": {
        # Price above SMA_20: short-term bullish trend
        "rule": "price_vs_indicator",
        "bullish_if": "Cours > SMA_20",
        "bearish_if": "Cours < SMA_20",
    },
    "SMA_50": {
        # Price above SMA_50: medium-term bullish trend
        "rule": "price_vs_indicator",
        "bullish_if": "Cours > SMA_50",
        "bearish_if": "Cours < SMA_50",
    },
    "EMA_20": {
        # Golden/death cross proxy: SMA_20 crossing EMA_20
        "rule": "price_vs_indicator",
        "bullish_if": "Cours > EMA_20",
        "bearish_if": "Cours < EMA_20",
    },

    # ── Momentum ─────────────────────────────────────────────────────────
    "RSI_14": {
        # Classic oversold/overbought — thresholds configurable
        "rule": "threshold",
        "bullish_if_below": 30,    # oversold
        "bearish_if_above": 70,    # overbought
        # between 30–70 → NEUTRAL
    },
    "MACD": {
        # MACD line crossing Signal line
        "rule": "macd_crossover",
        "bullish_if": "MACD > MACD_Signal",
        "bearish_if": "MACD < MACD_Signal",
        # Histogram confirms direction but is correlated — counted once
        # (histogram enters as MACD_Signal strength modifier, not separate signal)
    },

    # ── Volume / Price-Volume Confirmation ───────────────────────────────
    "RVOL": {
        # Relative Volume confirms whether a price move has volume backing
        # RVOL > 1.5: unusually high activity — confirms trend signal
        # RVOL < 0.5: very low activity — weakens trend signal
        # Used as a CONFIRMATION modifier, not a standalone directional signal
        "rule": "volume_confirmation",
        "confirm_threshold": 1.5,  # strong volume
        "weak_threshold":    0.5,  # thin volume
    },
    "VWAP": {
        # Price above VWAP: buyers dominating intraday
        "rule": "price_vs_indicator",
        "bullish_if": "Cours > VWAP",
        "bearish_if": "Cours < VWAP",
    },

    # ── Risk / Volatility ────────────────────────────────────────────────
    "HV_20": {
        # Historical Volatility is NOT a directional signal.
        # High vol → penalise Confidence, not Score.
        # Thresholds reference the distribution of HV across the universe.
        "rule": "volatility_context",
        "high_vol_percentile": 75,   # above p75 of universe → confidence penalty
        "low_vol_percentile":  25,   # below p25 → confidence bonus
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. SIGNAL FAMILIES & SCORE WEIGHTS
# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  CRITICAL: BASELINE HYPOTHESIS — NOT SCIENTIFICALLY VALIDATED YET  ⚠️
#
# The weights below are INITIAL EXPERT ESTIMATES used to validate that the
# pipeline works end-to-end. They are NOT proven to produce profitable
# trading decisions.
#
# Status: HYPOTHESIS REQUIRING BACKTESTING
# ──────────────────────────────────────────
# These weights will be evaluated via historical backtesting across
# configurations A–E. The final configuration is selected after:
#
#   1. Observing performance on development period
#   2. Confirming stability on validation period
#   3. Evaluating multiple criteria (not just return):
#        • Hit rate (% of BUY decisions with forward_return > 0)
#        • Sharpe ratio (risk-adjusted return)
#        • Maximum drawdown (worst peak-to-trough loss)
#        • Decision stability (turnover, false signals)
#
# The methodology is considered validated ONLY after backtesting shows
# robustness across different weight configurations and time periods.
#
# DO NOT present these weights as "optimal" or "scientifically proven"
# until notebook 12 (backtesting) is complete.
#
# Rationale for baseline hypothesis:
#   Trend 35 %    — captures the dominant directional regime
#   Momentum 35 % — captures entry timing within that regime
#   Volume 20 %   — confirmation layer; secondary to price/momentum
#   Risk 10 %     — context/penalty layer; not a directional vote

SCORE_WEIGHTS = {
    "Trend":     0.35,   # SMA_20, SMA_50, EMA_20
    "Momentum":  0.35,   # RSI_14, MACD
    "Volume":    0.20,   # RVOL (confirmation), VWAP
    "Risk":      0.10,   # HV_20 (context/penalty)
}

# Mark as baseline to prevent accidental use as "validated"
WEIGHTS_STATUS = "BASELINE_HYPOTHESIS"  # Change to "VALIDATED" after backtesting

# Alternative weight configurations for sensitivity analysis:
SCORE_WEIGHT_CONFIGS = {
    "A_baseline":    {"Trend": 0.35, "Momentum": 0.35, "Volume": 0.20, "Risk": 0.10},
    "B_more_mom":    {"Trend": 0.30, "Momentum": 0.40, "Volume": 0.20, "Risk": 0.10},
    "C_more_trend":  {"Trend": 0.40, "Momentum": 0.30, "Volume": 0.20, "Risk": 0.10},
    "D_more_vol":    {"Trend": 0.30, "Momentum": 0.30, "Volume": 0.30, "Risk": 0.10},
    "E_less_risk":   {"Trend": 0.40, "Momentum": 0.35, "Volume": 0.20, "Risk": 0.05},
}

# Score normalisation: final OverallScore is on [0, 100].
# A pure-bullish signal in a family scores 100; pure-bearish scores 0; neutral 50.
SCORE_NEUTRAL = 50.0
SCORE_MAX     = 100.0
SCORE_MIN     = 0.0

# ─────────────────────────────────────────────────────────────────────────────
# 5. CONFIDENCE SCORE — INDEPENDENT OF OVERALL SCORE
# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  CRITICAL DISTINCTION  ⚠️
#
# Overall Score   → measures DIRECTION & STRENGTH of market signals
#                   (0 = strongly bearish, 50 = neutral, 100 = strongly bullish)
#
# Confidence      → measures QUALITY & RELIABILITY of those signals
#                   (0% = unreliable data, 100% = high-quality unanimous signals)
#
# These are INDEPENDENT dimensions. Valid combinations include:
#
#   Score=82, Confidence=42%
#     → Available signals are strongly bullish, but data is sparse or
#        families disagree or volatility is abnormally high.
#        Interpretation: "bullish signal with low conviction"
#
#   Score=48, Confidence=91%
#     → Weak directional signal (near-neutral), but with excellent data
#        coverage, unanimous family agreement, and stable volatility.
#        Interpretation: "no strong move expected, high confidence"
#
# Confidence NEVER looks at whether the score is extreme or moderate —
# it only evaluates the DATA QUALITY behind that score.
#
# Three components:
#   A. Data Coverage   (40%) — fraction of required indicators that are computable
#   B. Family Agreement(40%) — do Trend/Momentum/Volume families agree on direction?
#   C. Risk Penalty    (20%) — reduce confidence when HV is abnormally high

CONFIDENCE_WEIGHTS = {
    "data_coverage":    0.40,   # penalises missing indicators
    "family_agreement": 0.40,   # penalises disagreement between families
    "risk_penalty":     0.20,   # penalises high volatility / thin data
}

# Minimum data coverage to produce any decision (below → INSUFFICIENT_DATA)
MIN_COVERAGE_FOR_DECISION = 0.50   # at least 50% of indicators must be valid

# ─────────────────────────────────────────────────────────────────────────────
# 6. DECISION THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  BASELINE HYPOTHESIS — REQUIRES BACKTESTING VALIDATION  ⚠️
#
# These thresholds are initial estimates. They have NOT been proven to
# produce profitable trading decisions. The backtesting notebook (12) will
# evaluate these thresholds against historical data and may recommend
# adjustments based on:
#   • Hit rate (% of BUY/SELL decisions that were correct)
#   • Risk-adjusted returns (Sharpe ratio)
#   • Drawdown control (maximum loss)
#
# Current policy:
#   BUY  → Score ≥ 60 AND Confidence ≥ 60%
#   SELL → Score ≤ 40 AND Confidence ≥ 60%
#   HOLD → everything else (unless data coverage < 50%)

DECISION_THRESHOLDS = {
    "buy":           {"min_score": 60, "min_confidence": 60},
    "sell":          {"max_score": 40, "min_confidence": 60},
    # Everything else → HOLD
    # Below MIN_COVERAGE_FOR_DECISION → INSUFFICIENT_DATA
}

THRESHOLDS_STATUS = "BASELINE_HYPOTHESIS"  # Change to "VALIDATED" after backtesting

# Sensitivity analysis grid (applied during backtesting evaluation):
DECISION_THRESHOLD_GRID = {
    "buy_score":        [55, 60, 65, 70],
    "sell_score":       [30, 35, 40, 45],
    "min_confidence":   [50, 60, 70, 80],
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. BACKTESTING PROTOCOL
# ─────────────────────────────────────────────────────────────────────────────
# Forward-return horizons to evaluate decisions against.
# Chosen before looking at results — not tuned post-hoc.

BACKTEST_CONFIG = {
    # Forward return horizons (trading sessions, not calendar days)
    "horizons": [5, 10, 20],          # ~1 week, 2 weeks, 1 month

    # Temporal split — strictly chronological, NO random shuffling.
    # Given our 28-session sample window, we use:
    #   Development:  first 60% of dates (sessions 1–17)
    #   Validation:   next 20%           (sessions 18–22)
    #   Test:         final 20%          (sessions 23–28)
    # The test period is only evaluated after methodology is frozen.
    "split": {
        "development": 0.60,
        "validation":  0.20,
        "test":        0.20,
    },

    # Minimum sessions required in a period to be meaningful
    "min_sessions_per_period": 5,

    # Metrics to compute per configuration
    "metrics": [
        "avg_forward_return_BUY",
        "avg_forward_return_SELL",
        "avg_forward_return_HOLD",
        "hit_rate",           # fraction of BUY decisions where forward_return > 0
        "sharpe_ratio",       # annualised return / annualised vol of decisions
        "max_drawdown",       # worst peak-to-trough over evaluation period
        "n_decisions",        # total number of BUY/SELL decisions
    ],

    # Look-ahead bias guard: at date t, ONLY use data available at t.
    # Forward return is computed AFTER the decision is generated.
    # This is enforced in code by shifting price series.
    "lookahead_guard": True,
}
