"""
Score Technique « Flash Momentum » (0–100) — implémentation des règles métier.

⚠️ IMPORTANT
-----------
Ce module est une IMPLÉMENTATION TECHNIQUE de la méthodologie fournie par
l'encadrant (voir FLASH_MOMENTUM_CONFIG dans config/methodology.py). Ce n'est PAS
une nouvelle méthodologie.

Le score technique final est sur [0, 100] et additionne quatre piliers :
    • Pression des volumes ...... 20 points (RVOL 10 + tendance OBV 10)
    • RSI (momentum) ............ 25 points
    • Moyennes mobiles .......... 35 points (position 15 + alignement 15 + golden cross 5)
    • MACD ...................... 20 points

Distinctions à ne jamais confondre :
    - Ce score ≠ signaux individuels {-1, 0, +1} (src/signals.py) réservés à
      l'analyse valeur-par-valeur.
    - Ce score ≠ Data Coverage. La couverture (qualité/complétude des données)
      est calculée séparément et sert uniquement à décider INSUFFICIENT_DATA.

Toutes les fonctions de pilier sont PURES et déterministes : mêmes entrées →
même sortie, aucune fuite d'information future (les helpers de séries utilisent
uniquement des valeurs passées via .shift()).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# PILIER 1 — RSI (25 points)
# ─────────────────────────────────────────────────────────────────────────────
def score_rsi(rsi: float, cfg: Dict) -> float:
    """
    Score RSI selon la grille encadrant (0–25).

        55 ≤ RSI ≤ 70        → 25
        45 ≤ RSI < 55        → 15
        RSI > 70             → 10
        RSI < 30             → 0
        30 ≤ RSI < 45        → rsi_weak_recovery_points (zone non définie, SIGNALÉE)

    Retourne 0.0 si RSI est NaN (pilier non couvert ; la couverture est gérée ailleurs).
    """
    if pd.isna(rsi):
        return 0.0

    r = cfg["rsi"]
    if r["sweet_low"] <= rsi <= r["sweet_high"]:
        return float(r["sweet_points"])          # 55–70 → 25
    if rsi > r["overbought"]:
        return float(r["overbought_points"])      # > 70 → 10
    if r["mid_low"] <= rsi < r["sweet_low"]:
        return float(r["mid_points"])             # 45–55 → 15
    if rsi < r["oversold"]:
        return float(r["oversold_points"])        # < 30 → 0
    # Zone [30, 45) — non définie explicitement par la méthodologie (SIGNALÉE)
    return float(r["rsi_weak_recovery_points"])


# ─────────────────────────────────────────────────────────────────────────────
# PILIER 2 — MACD (20 points)
# ─────────────────────────────────────────────────────────────────────────────
def score_macd(macd: float, signal: float, cfg: Dict) -> float:
    """
    Score MACD selon les 4 états (croisement ET signe) — grille encadrant (0–20).

        MACD > Signal ET MACD > 0 → 20
        MACD > Signal ET MACD < 0 → 12
        MACD < Signal ET MACD > 0 → 5
        MACD < Signal ET MACD < 0 → 0

    Convention aux bornes : MACD == Signal traité comme « non au-dessus » ;
    MACD == 0 traité comme « non positif ».
    Retourne 0.0 si MACD ou Signal est NaN (pilier non couvert).
    """
    if pd.isna(macd) or pd.isna(signal):
        return 0.0

    m = cfg["macd"]
    above = macd > signal
    positive = macd > 0

    if above and positive:
        return float(m["above_positive_points"])   # 20
    if above and not positive:
        return float(m["above_negative_points"])    # 12
    if (not above) and positive:
        return float(m["below_positive_points"])    # 5
    return float(m["below_negative_points"])        # 0


# ─────────────────────────────────────────────────────────────────────────────
# PILIER 3 — VOLUME (20 points) = RVOL (10) + tendance OBV (10)
# ─────────────────────────────────────────────────────────────────────────────
def score_volume_rvol(rvol: float, cfg: Dict) -> float:
    """
    Sous-pilier RVOL (Volume du jour vs moyenne 20j) — 0/5/10.

        RVOL > 1.5        → 10  (pression acheteuse forte)
        0.5 ≤ RVOL ≤ 1.5  → 5   (dans la moyenne)
        RVOL < 0.5        → 0   (volume très faible / pression vendeuse)
    """
    if pd.isna(rvol):
        return 0.0
    v = cfg["volume"]
    if rvol > v["rvol_strong"]:
        return float(v["points_strong"])
    if rvol < v["rvol_weak"]:
        return float(v["points_weak"])
    return float(v["points_average"])


def score_volume_obv(obv_trend_state: Optional[str], cfg: Dict) -> float:
    """
    Sous-pilier tendance OBV (flux) — 0/5/10.

        'rising'  → 10
        'neutral' → 5
        'falling' → 0
        None      → 0  (historique OBV insuffisant → non couvert)
    """
    v = cfg["volume"]
    if obv_trend_state == "rising":
        return float(v["obv_points_rising"])
    if obv_trend_state == "neutral":
        return float(v["obv_points_neutral"])
    if obv_trend_state == "falling":
        return float(v["obv_points_falling"])
    return 0.0


def score_volume(rvol: float, obv_trend_state: Optional[str], cfg: Dict) -> float:
    """Pilier Volume complet (0–20)."""
    return score_volume_rvol(rvol, cfg) + score_volume_obv(obv_trend_state, cfg)


# ─────────────────────────────────────────────────────────────────────────────
# PILIER 4 — MOYENNES MOBILES (35 points) = position (15) + alignement (15) + golden cross (5)
# ─────────────────────────────────────────────────────────────────────────────
def score_ma_position(cours: float, mm20: float, mm50: float, mm200: float, cfg: Dict) -> float:
    """
    Position du cours vs moyennes mobiles (0–15). Dégradation gracieuse si MM200 absente.

        Cours > MM20, MM50 ET MM200  → 15
        Cours > MM20 ET MM50         → 10
        Cours < MM20 ET MM50         → 0
        cas mixte                    → position_mixed_points (SIGNALÉ)
    """
    m = cfg["ma"]
    if pd.isna(cours) or pd.isna(mm20) or pd.isna(mm50):
        return 0.0  # position indéterminable sans MM20/MM50

    above_20 = cours > mm20
    above_50 = cours > mm50

    if above_20 and above_50:
        # Palier supérieur uniquement si MM200 disponible ET cours au-dessus
        if pd.notna(mm200) and cours > mm200:
            return float(m["position_all_points"])   # 15
        return float(m["position_20_50_points"])      # 10 (MM200 absente ou en dessous)
    if (not above_20) and (not above_50):
        return float(m["position_below_points"])      # 0
    return float(m["position_mixed_points"])          # cas mixte (SIGNALÉ)


def score_ma_alignment(mm20: float, mm50: float, mm200: float, cfg: Dict) -> float:
    """
    Alignement des moyennes mobiles (0–15). Dégradation gracieuse si MM200 absente.

        MM20 > MM50 > MM200  → 15
        MM20 < MM50 < MM200  → 0
        alignement partiel   → 8
        (MM200 absente)      → 8 si MM20 > MM50, sinon 0
    """
    m = cfg["ma"]
    if pd.isna(mm20) or pd.isna(mm50):
        return 0.0  # alignement indéterminable

    if pd.notna(mm200):
        if mm20 > mm50 > mm200:
            return float(m["alignment_full_points"])      # 15
        if mm20 < mm50 < mm200:
            return float(m["alignment_bearish_points"])   # 0
        return float(m["alignment_partial_points"])       # 8
    # MM200 absente → on ne peut confirmer l'alignement complet → au mieux partiel
    if mm20 > mm50:
        return float(m["alignment_partial_points"])       # 8
    return float(m["alignment_bearish_points"])           # 0


def score_ma_golden_cross(golden_cross_recent: bool, cfg: Dict) -> float:
    """Golden Cross (MM50 croise MM200 vers le haut) récent → +5, sinon 0."""
    return float(cfg["ma"]["golden_cross_points"]) if bool(golden_cross_recent) else 0.0


def score_moving_averages(
    cours: float, mm20: float, mm50: float, mm200: float,
    golden_cross_recent: bool, cfg: Dict
) -> float:
    """Pilier Moyennes Mobiles complet (0–35)."""
    return (
        score_ma_position(cours, mm20, mm50, mm200, cfg)
        + score_ma_alignment(mm20, mm50, mm200, cfg)
        + score_ma_golden_cross(golden_cross_recent, cfg)
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION DU SCORE
# ─────────────────────────────────────────────────────────────────────────────
def classify_score(score: float, cfg: Dict) -> str:
    """
    Classe le score 0–100 selon la grille encadrant.
        80–100 → Très Fort
        60–79  → Modéré à Positif
        40–59  → Neutre
        0–39   → Faible / Baissier
    """
    if pd.isna(score):
        return "N/A"
    for min_bound, label in cfg["classification"]:
        if score >= min_bound:
            return label
    return cfg["classification"][-1][1]


def classify_symbol(score: float, cfg: Dict) -> str:
    """
    Symbole de classe (gradient +++ / ++ / + / − / −−) selon class_symbol_scale.
    Suit la notation du guide encadrant. Retourne '' si score indisponible.
    """
    if pd.isna(score):
        return ""
    scale = cfg.get("class_symbol_scale")
    if not scale:
        return ""
    for min_bound, symbol in scale:
        if score >= min_bound:
            return symbol
    return scale[-1][1]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE SÉRIE (par société) — OBV trend & Golden Cross
# ─────────────────────────────────────────────────────────────────────────────
def _compute_obv_trend_states(group: pd.DataFrame, cfg: Dict) -> pd.Series:
    """
    Détermine l'état de tendance OBV ('rising'/'neutral'/'falling'/None) par ligne.

    Normalisation bornée : variation d'OBV sur la fenêtre divisée par le volume total
    échangé sur la même fenêtre (|variation| max possible) → valeur dans [-1, 1].
    Bande neutre configurable. Utilise uniquement des valeurs passées (.shift()) →
    aucune fuite d'information future.
    """
    v = cfg["volume"]
    window = v["obv_trend_window"]
    band = v["obv_neutral_band"]

    obv = group["OBV"]
    obv_prev = obv.shift(window)
    delta = obv - obv_prev

    # Volume total sur la fenêtre (borne supérieure de |delta OBV|)
    vol = group["Volume MC"].astype(float)
    vol_sum = vol.rolling(window, min_periods=window).sum()

    states = pd.Series([None] * len(group), index=group.index, dtype=object)
    valid = obv.notna() & obv_prev.notna() & vol_sum.notna() & (vol_sum > 0)

    normalized = pd.Series(np.nan, index=group.index)
    normalized[valid] = delta[valid] / vol_sum[valid]

    states[valid & (normalized > band)] = "rising"
    states[valid & (normalized < -band)] = "falling"
    states[valid & (normalized >= -band) & (normalized <= band)] = "neutral"
    return states


def _compute_golden_cross_recent(group: pd.DataFrame, cfg: Dict) -> pd.Series:
    """
    Marque True si un Golden Cross (MM50 franchit MM200 vers le haut) s'est produit
    sur les `golden_cross_window` dernières séances (incluant la séance courante).

    Croisement à t : SMA_50[t] > SMA_200[t] ET SMA_50[t-1] ≤ SMA_200[t-1].
    Utilise uniquement des valeurs passées → aucune fuite d'information future.
    """
    window = cfg["ma"]["golden_cross_window"]
    sma50 = group["SMA_50"]
    sma200 = group["SMA_200"]

    prev50 = sma50.shift(1)
    prev200 = sma200.shift(1)

    cross_up = (
        sma50.notna() & sma200.notna() & prev50.notna() & prev200.notna()
        & (sma50 > sma200) & (prev50 <= prev200)
    )
    # « récent » = au moins un croisement sur la fenêtre glissante
    recent = cross_up.rolling(window, min_periods=1).max().fillna(0).astype(bool)
    return recent


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATEUR
# ─────────────────────────────────────────────────────────────────────────────
def compute_flash_scores(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Calcule le Technical Score Flash Momentum (0–100) et ses sous-scores par pilier.

    Ajoute les colonnes :
        - Flash_Vol_Score, Flash_RSI_Score, Flash_MM_Score, Flash_MACD_Score
        - Technical_Score (0–100)
        - Score_Class (Très Fort / Modéré à Positif / Neutre / Faible / Baissier)
        - Flash_Coverage (0.0–1.0) : couverture des données requises par le score
        - OBV_Trend, Golden_Cross_Recent (traçabilité)

    Le Flash_Coverage est INDÉPENDANT du Technical_Score (dimension qualité données).

    Args:
        df: DataFrame avec indicateurs (doit contenir les colonnes indicateurs)
        config: FLASH_MOMENTUM_CONFIG

    Returns:
        DataFrame enrichi (copie).
    """
    out = df.copy()

    # 1) Helpers de série par société (OBV trend, Golden Cross)
    obv_states = []
    gc_recent = []
    for _, grp in out.groupby("CODE_ISIN", sort=False):
        grp_sorted = grp.sort_values("Date")
        obv_states.append(_compute_obv_trend_states(grp_sorted, config))
        gc_recent.append(_compute_golden_cross_recent(grp_sorted, config))

    out["OBV_Trend"] = pd.concat(obv_states).reindex(out.index)
    out["Golden_Cross_Recent"] = pd.concat(gc_recent).reindex(out.index)

    # 2) Scoring par ligne (fonctions pures)
    def _score_row(row: pd.Series) -> pd.Series:
        vol = score_volume(row.get("RVOL", np.nan), row.get("OBV_Trend"), config)
        rsi = score_rsi(row.get("RSI_14", np.nan), config)
        mm = score_moving_averages(
            row.get("Cours", np.nan),
            row.get("SMA_20", np.nan),
            row.get("SMA_50", np.nan),
            row.get("SMA_200", np.nan),
            row.get("Golden_Cross_Recent", False),
            config,
        )
        macd = score_macd(row.get("MACD", np.nan), row.get("MACD_Signal", np.nan), config)
        total = vol + rsi + mm + macd
        return pd.Series({
            "Flash_Vol_Score": vol,
            "Flash_RSI_Score": rsi,
            "Flash_MM_Score": mm,
            "Flash_MACD_Score": macd,
            "Technical_Score": total,
        })

    scores = out.apply(_score_row, axis=1)
    for col in scores.columns:
        out[col] = scores[col]

    # 3) Classification + symbole de classe (+++ / ++ / + / − / −−)
    out["Score_Class"] = out["Technical_Score"].apply(lambda s: classify_score(s, config))
    out["Score_Symbol"] = out["Technical_Score"].apply(lambda s: classify_symbol(s, config))

    # 4) Data Coverage dédié au score (indépendant du score lui-même)
    coverage_inputs = config["coverage_inputs"]
    n_inputs = len(coverage_inputs)

    def _coverage(row: pd.Series) -> float:
        valid = sum(1 for c in coverage_inputs if pd.notna(row.get(c, np.nan)))
        return valid / n_inputs if n_inputs > 0 else 0.0

    out["Flash_Coverage"] = out.apply(_coverage, axis=1)

    return out
