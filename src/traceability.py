"""
Couche de RESTITUTION (traçabilité) — PAS de logique métier.

Ce module ne recalcule AUCUN score ni indicateur. Il reformate uniquement les
colonnes déjà produites par le pipeline (src/indicators.py, src/signals.py,
src/scoring_flash.py, src/decisions.py) pour alimenter la page Traçabilité et la
vue Détails de l'UI.

Il produit une « trace » temporaire par société (une ligne = la dernière séance
exploitable de la société), avec :
  - identité, décision, Technical Score, classification ;
  - scores par pilier Flash Momentum (déjà calculés) ;
  - couverture des indicateurs (dynamique, basée sur FLASH_MOMENTUM_CONFIG) ;
  - valeur + signal + statut de chaque indicateur attendu.

La trace est SESSION-SCOPED : écrasée à chaque nouvelle analyse / reset.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


# Indicateurs présentés dans la vue Détails.
# (clé colonne, libellé, pilier, source du signal déjà calculé)
# La source du signal réutilise UNIQUEMENT des colonnes déjà produites par le backend.
EXPECTED_INDICATORS: List[Tuple[str, str, str, str]] = [
    ("RVOL",        "RVOL (volume relatif)",   "Volume",   "Sig_RVOL"),
    ("OBV",         "OBV (flux de volume)",    "Volume",   "OBV_Trend"),
    ("RSI_14",      "RSI (14)",                "Momentum", "Sig_RSI_14"),
    ("SMA_20",      "Moyenne mobile 20",       "Tendance", "Sig_SMA_20"),
    ("SMA_50",      "Moyenne mobile 50",       "Tendance", "Sig_SMA_50"),
    ("SMA_200",     "Moyenne mobile 200",      "Tendance", None),
    ("MACD",        "MACD",                    "MACD",     "Sig_MACD"),
    ("MACD_Signal", "MACD — ligne de signal",  "MACD",     None),
]

# Libellés lisibles pour les signaux individuels {-1, 0, +1} déjà calculés.
_SIG_LABELS = {
    "Sig_RVOL":   {1: "Fort (>1.5)", 0: "Moyen", -1: "Faible (<0.5)"},
    "Sig_RSI_14": {1: "Survente (<30)", 0: "Neutre", -1: "Surachat (>70)"},
    "Sig_SMA_20": {1: "Cours > MM20", 0: "Cours = MM20", -1: "Cours < MM20"},
    "Sig_SMA_50": {1: "Cours > MM50", 0: "Cours = MM50", -1: "Cours < MM50"},
    "Sig_MACD":   {1: "MACD > Signal", 0: "—", -1: "MACD < Signal"},
}
_OBV_LABELS = {"rising": "Hausse", "neutral": "Neutre", "falling": "Baisse"}


def expected_indicator_keys(config: Dict) -> List[str]:
    """Liste dynamique des indicateurs attendus pour la couverture (depuis la config)."""
    return list(config.get("coverage_inputs", []))


def _is_computed(row: pd.Series, key: str) -> bool:
    """Un indicateur est 'calculé' si son statut Valid_* == VALID, sinon si sa valeur est non-NaN."""
    vcol = f"Valid_{key}"
    if vcol in row.index and pd.notna(row.get(vcol)):
        return str(row.get(vcol)) == "VALID"
    return pd.notna(row.get(key, np.nan))


def indicator_coverage(row: pd.Series, config: Dict) -> Tuple[int, int, List[str]]:
    """
    Couverture dynamique des indicateurs pour une société.

    Returns:
        (nb_calculés, nb_attendus, liste_indisponibles)
    Le nombre attendu vient de FLASH_MOMENTUM_CONFIG['coverage_inputs'] (jamais codé en dur).
    """
    keys = expected_indicator_keys(config)
    computed, unavailable = [], []
    for k in keys:
        (computed if _is_computed(row, k) else unavailable).append(k)
    return len(computed), len(keys), unavailable


def _signal_label(row: pd.Series, sig_src) -> str:
    if sig_src == "OBV_Trend":
        return _OBV_LABELS.get(row.get("OBV_Trend"), "—")
    if sig_src and sig_src in row.index and pd.notna(row.get(sig_src)):
        try:
            return _SIG_LABELS.get(sig_src, {}).get(int(row.get(sig_src)), "—")
        except (ValueError, TypeError):
            return "—"
    return "—"


def company_indicator_table(row: pd.Series) -> List[Dict]:
    """
    Table indicateur-par-indicateur pour la vue Détails (restitution pure).

    Chaque entrée : Pilier, Indicateur, Valeur, Signal, Statut (Calculé / Indisponible).
    """
    out = []
    for key, label, pillar, sig_src in EXPECTED_INDICATORS:
        val = row.get(key, np.nan)
        computed = _is_computed(row, key)
        out.append({
            "Pilier": pillar,
            "Indicateur": label,
            "Valeur": "—" if pd.isna(val) else f"{float(val):,.2f}",
            "Signal": _signal_label(row, sig_src) if computed else "—",
            "Statut": "✅ Calculé" if computed else "⚠️ Indisponible",
        })
    return out


def build_company_traces(decisions_df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Construit la trace par société : une ligne = dernière séance exploitable de la société.

    Ne recalcule rien : sélectionne la dernière ligne (décision != INSUFFICIENT_DATA de
    préférence) et conserve les colonnes déjà produites nécessaires à l'affichage.

    Args:
        decisions_df: DataFrame par (Date, société) issu du pipeline (indicateurs +
                      Valid_* + Sig_* + scores piliers Flash + Decision + Data_Coverage)
        config: FLASH_MOMENTUM_CONFIG

    Returns:
        DataFrame (une ligne par société) — la trace temporaire.
    """
    ind_keys = [k for k, _, _, _ in EXPECTED_INDICATORS]
    sig_cols = [s for *_, s in EXPECTED_INDICATORS if s and str(s).startswith("Sig_")]
    valid_cols = [f"Valid_{k}" for k in ind_keys]
    base_cols = [
        "CODE_ISIN", "Company", "Date", "Cours", "Decision", "Data_Coverage",
        "Technical_Score", "Score_Class", "Score_Symbol",
        "Flash_Vol_Score", "Flash_RSI_Score", "Flash_MM_Score", "Flash_MACD_Score",
        "Flash_Coverage", "OBV_Trend", "Golden_Cross_Recent",
    ]
    keep = [c for c in (base_cols + ind_keys + sig_cols + valid_cols) if c in decisions_df.columns]

    rows = []
    for _, grp in decisions_df.groupby("CODE_ISIN", sort=False):
        g = grp.sort_values("Date")
        if "Decision" in g.columns:
            valid = g[g["Decision"] != "INSUFFICIENT_DATA"]
            latest = valid.tail(1) if len(valid) else g.tail(1)
        else:
            latest = g.tail(1)
        if len(latest):
            rows.append(latest[keep].iloc[0])

    if not rows:
        return pd.DataFrame(columns=keep)

    trace = pd.DataFrame(rows).reset_index(drop=True)

    # Ajout des colonnes de couverture (dynamiques) pour un accès direct dans l'UI
    cov = trace.apply(lambda r: pd.Series(dict(zip(
        ["_cov_computed", "_cov_total", "_cov_missing"],
        _coverage_triplet(r, config)
    ))), axis=1)
    trace["Indicators_Computed"] = cov["_cov_computed"].astype(int)
    trace["Indicators_Total"] = cov["_cov_total"].astype(int)
    trace["Indicators_Missing"] = cov["_cov_missing"]  # liste (objet)
    return trace


def _coverage_triplet(row: pd.Series, config: Dict):
    n_ok, n_tot, missing = indicator_coverage(row, config)
    return n_ok, n_tot, missing


def pillar_breakdown(row: pd.Series, config: Dict) -> List[Dict]:
    """
    Explicabilité du score : points par pilier / maximum (depuis colonnes déjà calculées).
    """
    pmax = config.get("pillar_max", {"volume": 20, "rsi": 25, "ma": 35, "macd": 20})
    items = [
        ("Volume (RVOL + OBV)", "Flash_Vol_Score", pmax.get("volume", 20)),
        ("Momentum (RSI)",      "Flash_RSI_Score", pmax.get("rsi", 25)),
        ("Tendance (MM20/50/200)", "Flash_MM_Score", pmax.get("ma", 35)),
        ("MACD",                "Flash_MACD_Score", pmax.get("macd", 20)),
    ]
    out = []
    for label, col, maxp in items:
        v = row.get(col, np.nan)
        out.append({
            "Pilier": label,
            "Points": None if pd.isna(v) else int(round(float(v))),
            "Max": maxp,
            "Barème": "—" if pd.isna(v) else f"{int(round(float(v)))} / {maxp}",
        })
    return out
