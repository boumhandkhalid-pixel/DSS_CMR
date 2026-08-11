from __future__ import annotations

APP_TITLE = "BVC Portfolio DSS"
APP_SUBTITLE = "Market data, filtering, and recommendations"

NAVIGATION_PAGES = [
    "Dashboard",
    "Market Data",
    "Market Metrics",
    "Index Composition",
    "Analysis",
    "Recommendations",
    "Settings",
]

MARKET_WORKBOOK_EXAMPLES = [
    "Cours",
    "Bid",
    "Ask",
    "Volume MC",
    "Quantité MC",
]

MARKET_WORKBOOK_EXCLUDED = ["Data", "Indicateurs"]

INDEX_COMPOSITION_EXAMPLES = ["MASI", "MASI 20", "MASI ESG", "Sector Indices"]

TECHNICAL_INDICATORS_DEFAULT = [
    "RSI14",
    "SMA20",
    "SMA50",
    "EMA20",
    "MACD",
    "MACD Signal",
    "MACD Histogram",
    "RVOL",
    "VWAP",
    "Historical Volatility",
]

DYNAMIC_FILTER_DEFAULTS = {
    "min_liquidity": 0.0,
    "min_average_volume": 0.0,
    "min_free_float": 0.0,
    "min_free_float_market_cap": 0.0,
    "min_weight": 0.0,
    "max_capping_factor": 1.0,
}

BUSINESS_RULE_DEFAULTS = {
    "rsi_buy_threshold": 30,
    "rvol_buy_threshold": 1.5,
    "macd_rule": "Bullish crossover",
}
