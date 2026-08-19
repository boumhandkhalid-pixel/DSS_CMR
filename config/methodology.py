"""
Configuration Méthodologique DSS
=================================
Tous les seuils, poids et définitions de signaux sont centralisés ici.
Les notebooks et modules de production importent depuis ce fichier —
aucune logique métier n'est codée en dur.

IMPORTANT — CONCEPTION PIPELINE DYNAMIQUE
------------------------------------------
Ce système N'EST PAS conçu pour un jeu de données fixe.
En production, le gestionnaire de portefeuille télécharge deux fichiers via Streamlit :

    1. Fichier données marché (fréquent — hebdomadaire / mensuel)
       → Cours, Bid, Ask, Volume MC, Quantité MC

    2. Fichier composition d'indice (moins fréquent — mensuel / trimestriel)
       → Facteur flottant, Capitalisation flottante, Poids, Nb titres

Le pipeline ETL s'exécute à chaque téléchargement.
Les seuils de filtrage dynamique NE SONT PAS des valeurs absolues codées en dur —
ce sont des règles de percentiles recalculées à partir du fichier de composition
qui a été téléchargé. Cela signifie :
  - Un nouveau fichier de composition le mois prochain → nouveaux seuils absolus
  - Un indice différent sélectionné → seuils dérivés de cet indice
  - Aucune modification de code requise — uniquement la configuration

Les données de référence dans /data/ et /samples/ servent uniquement à
valider les notebooks. L'interface Streamlit calculera tous les
seuils dynamiquement à l'exécution.

La justification de chaque valeur est documentée en ligne.
"""

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# 1. FILTRAGE DYNAMIQUE
# ─────────────────────────────────────────────────────────────────────────────
# Les seuils sont exprimés en RÈGLES DE PERCENTILES, pas en valeurs absolues.
# La fonction compute_filter_thresholds(composition_df) traduit ces règles
# en valeurs absolues à l'exécution, en utilisant le fichier de composition
# téléchargé par le gestionnaire de portefeuille.
#
# Stratégie B – Modérée sélectionnée après comparaison A/B/C sur données réelles.
# Voir notebook 08 pour l'analyse complète de distribution et comparaison.

FILTER_CONFIG = {
    # Gate 1 : univers d'indice — les titres doivent appartenir à cet indice.
    # ⚠️ Décision encadrant : SEULS deux indices de référence sont supportés :
    #    - "MASI"    → on retient les N PREMIÈRES sociétés par POIDS FLOTTANT (top-N).
    #    - "MASI 20" → on retient TOUS les titres listés dans la feuille (≈ 20).
    #    Les autres indices (MASI ESG, sectoriels, etc.) sont ignorés.
    "index": "MASI 20",

    # Indices de référence autorisés (le dropdown de l'UI ne propose que ceux-ci).
    "supported_indices": ["MASI", "MASI 20"],

    # Règle de sélection propre à chaque indice.
    #   MASI    : top-N par poids flottant (Weight), N configurable ci-dessous.
    #   MASI 20 : tous les titres de la feuille (aucun filtrage supplémentaire).
    "selection_rules": {
        "MASI":    {"mode": "top_n_by_weight", "n": 40},
        "MASI 20": {"mode": "all"},
    },

    # Nombre de sociétés retenues pour le MASI (top-N par poids flottant).
    "masi_top_n_by_weight": 40,

    # ── Paramètres conservés pour compatibilité / reporting (NON utilisés comme portes) ──
    # Le Facteur flottant et la Capitalisation flottante restent calculés et disponibles
    # pour l'analyse, mais ne filtrent plus l'univers (décision encadrant).
    "min_float_weight": 0.0,
    "min_ff_market_cap_percentile": 25,
    "weight_as_ranking_only": True,
    "min_avg_vol20": None,
}


def compute_filter_thresholds(composition_df):
    """
    Traduit les règles de percentiles dans FILTER_CONFIG en valeurs absolues,
    calculées à partir du DataFrame de composition téléchargé par le gestionnaire de portefeuille.

    C'est la fonction clé qui rend le pipeline dynamique :
    - Appelée une fois par téléchargement d'un nouveau fichier de composition
    - Retourne une config résolue avec seuils absolus prêts à utiliser
    - Aucune valeur MAD codée en dur nulle part dans le code

    Paramètres
    ----------
    composition_df : pd.DataFrame
        Fichier de composition d'indice analysé, déjà filtré sur l'indice sélectionné.
        Doit contenir les colonnes : FF, FF_MarketCap, Weight.

    Retourne
    --------
    dict avec seuils absolus résolus, plus contexte de distribution.

    Exemple
    -------
    Upload : Compo_All_Indices_20261031.xlsx  (trimestre suivant)
        → p25(FF_MarketCap) pourrait être 230 M MAD au lieu de 218 M MAD
        → Le filtre s'adapte automatiquement — aucun changement de code nécessaire
    """
    # Validation 1: DataFrame vide
    if composition_df.empty:
        raise ValueError(
            "❌ Le fichier de composition ne contient aucune ligne pour l'indice sélectionné.\n"
            "Vérifiez que le nom de l'indice choisi correspond bien à une valeur présente "
            "dans la colonne 'Indice' du fichier importé."
        )
    
    # Validation 2: Colonne FF_MarketCap vide
    idx = composition_df["FF_MarketCap"].dropna()
    
    if idx.empty:
        raise ValueError(
            "❌ La colonne 'FF_MarketCap' est vide ou entièrement manquante dans le fichier "
            "de composition importé. Vérifiez le format du fichier."
        )

    p_ffmc = FILTER_CONFIG["min_ff_market_cap_percentile"]

    resolved = {
        # reporté tel quel (valeur absolue avec signification financière claire)
        "index":                  FILTER_CONFIG["index"],
        "min_float_weight":       FILTER_CONFIG["min_float_weight"],

        # calculé dynamiquement à partir du fichier téléchargé
        "min_ff_market_cap":      float(np.percentile(idx, p_ffmc)),

        # contexte — utile pour les rapports
        "n_securities":           len(composition_df),
        "ff_market_cap_p25":      float(np.percentile(idx, 25)),
        "ff_market_cap_median":   float(np.percentile(idx, 50)),
        "ff_market_cap_p75":      float(np.percentile(idx, 75)),
        "weight_median":          float(composition_df["Weight"].median()),
        "source_percentile_rule": f"FF_MarketCap >= p{p_ffmc}",
    }
    return resolved


# ─────────────────────────────────────────────────────────────────────────────
# 1.5  FILTRE DE QUALITÉ DES DONNÉES — Observations consécutives minimales
# ─────────────────────────────────────────────────────────────────────────────
# Le filtre supprime les sociétés qui n'ont PAS une séquence suffisamment longue
# d'observations de prix ininterrompues. "Ininterrompu" signifie aucun gap > MAX_GAP_DAYS
# entre deux valeurs Cours non nulles successives.
#
# Pourquoi consécutif, et pas seulement un décompte ?
# ────────────────────────────────────────────────────
# Le RSI et tous les indicateurs de moyennes mobiles calculent des *différences* entre
# lignes adjacentes. Un delta calculé sur un gap de plusieurs mois (ex : un prix de 2019
# comparé à un prix de 2024) n'est pas un rendement quotidien — c'est des années de
# mouvement de marché compressées en une seule étape. La formule s'exécute quand même et produit
# un nombre, mais ce nombre n'a aucun sens financier.
#
# Contrainte principale : SMA_50 (fenêtre la plus large)
# ───────────────────────────────────────────────────────
# SMA_50 nécessite 50 observations de prix consécutives pour produire sa première valeur valide.
# C'est l'exigence la plus stricte parmi tous les indicateurs basés sur les prix.
# (RSI-14 nécessite 15, EMA-20 nécessite 20, MACD nécessite 27, SMA-20 nécessite 20)
#
# MAX_GAP_DAYS : Heuristique de Qualité des Données
# ──────────────────────────────────────────────────
# Ce n'est PAS une exigence mathématique du RSI ou d'un quelconque indicateur.
# C'est une règle pratique pour distinguer :
#   - Gaps normaux (week-ends, congés occasionnels) : ≤ 7 jours
#   - Gaps anormaux (séances de trading manquantes) : > 7 jours
#
# Un gap > 7 jours signifie probablement qu'au moins 1-2 séances de trading complètes sont manquantes.
#
# Approche plus rigoureuse (amélioration future) :
#   Utiliser le calendrier officiel de trading de la BVC pour détecter exactement quelles séances manquent,
#   plutôt que de se fier à un seuil en jours calendaires.
#
# Par conséquent :
# ═══════════════════════════════════════════════════════════════════════════════
# NOUVELLE APPROCHE : Coverage Graceful (Pas de rejet global sur MIN_CONSECUTIVE)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Philosophie :
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
# Solution :
#   - Filtrer uniquement sur QUALITÉ TEMPORELLE (MAX_GAP_DAYS)
#   - Pas de trous > 7 jours entre observations
#   - Nombre d'observations = détermine quels indicateurs sont calculables
#
# ═══════════════════════════════════════════════════════════════════════════════

# MAX_GAP_DAYS : Qualité temporelle des données
# Rejette un titre si gap entre 2 observations consécutives > 7 jours
# (7 jours = week-end + quelques jours fériés)
MAX_GAP_DAYS: int = 7

# MIN_CONSECUTIVE : DÉPRÉCIÉ (conservé pour compatibilité avec anciens notebooks)
# ⚠️ NE PLUS UTILISER comme filtre global
# ⚠️ Utilisé uniquement dans filter_companies_by_usable_data() legacy
MIN_CONSECUTIVE: int = 14  # Pour compatibilité backward uniquement
MIN_USABLE_ROWS: int = MIN_CONSECUTIVE  # Alias rétro-compatible
MIN_USABLE_ROWS_SAMPLE_OVERRIDE: int = 1


# ─────────────────────────────────────────────────────────────────────────────
# 2. PARAMÈTRES DES INDICATEURS TECHNIQUES
# ─────────────────────────────────────────────────────────────────────────────

INDICATOR_PARAMS = {
    "sma_short":    20,   # Fenêtre SMA court terme
    "sma_long":     50,   # Fenêtre SMA long terme
    "sma_very_long": 200, # Fenêtre SMA très long terme (MM200 — requis par Flash Momentum)
    "ema_short":    20,   # Fenêtre EMA
    "rsi_period":   14,   # Période de rétrospection RSI (Wilder)
    "macd_fast":    12,   # EMA rapide MACD
    "macd_slow":    26,   # EMA lente MACD
    "macd_signal":   9,   # EMA signal MACD
    "rvol_window":  20,   # Fenêtre dénominateur RVOL
    "hv_window":    20,   # Fenêtre Volatilité Historique (écart-type log-return)
    "hv_annualise": 252,  # jours de trading par an pour annualisation
    # VWAP : cumulatif sur la plage de dates disponible (pas de réinitialisation intraday possible)
    # OBV : cumulatif (On-Balance Volume) ; pas de fenêtre au calcul, la tendance est évaluée au scoring
}

# Observations valides minimales requises avant qu'un indicateur puisse être calculé.
# Lignes en dessous du minimum → NaN (jamais rempli avec zéro ou forward-fill).
INDICATOR_MIN_OBS = {
    "SMA_20":          20,
    "SMA_50":          50,
    "SMA_200":        200,   # MM200 — dégrade gracieusement (NaN si historique insuffisant)
    "EMA_20":          20,   # fiable après 3× l'envergure
    "RSI_14":          15,   # 14 deltas + 1 seed
    "MACD":            26,   # fenêtre EMA lente
    "MACD_Signal":     35,   # fenêtres lente + signal
    "MACD_Histogram":  35,
    "RVOL":             1,   # dégrade gracieusement ; significatif à 20
    "VWAP":             1,   # cumulatif ; dégrade gracieusement
    "HV_20":           21,   # 20 différences de log-return
    "OBV":              2,   # cumulatif ; besoin ≥2 obs pour une variation ; tendance évaluée au scoring
}

# Calculé une fois à partir du tableau ci-dessus — importer ceci dans notebooks et src/
# MIN_USABLE_ROWS défini dans la section 1.5 ci-dessus (= MIN_CONSECUTIVE = 14)

# ─────────────────────────────────────────────────────────────────────────────
# 2.5  SCORE TECHNIQUE « FLASH MOMENTUM » (0–100) — SOURCE DE VÉRITÉ MÉTIER
# ─────────────────────────────────────────────────────────────────────────────
# Méthodologie fournie par l'encadrant. Score additif sur 100 points, 4 piliers :
#     • Pression des volumes ...... 20 points
#     • RSI (momentum) ............ 25 points
#     • Moyennes mobiles .......... 35 points
#     • MACD ...................... 20 points
#     TOTAL ....................... 100 points
#
# ⚠️ Ce score est DISTINCT :
#   - de la couche de signaux individuels {-1,0,+1} (section 3) réservée à
#     l'analyse valeur-par-valeur ;
#   - du Data Coverage (qualité/complétude des données), qui reste indépendant.
#
# NOTES SUR DEUX ZONES NON EXPLICITEMENT DÉFINIES PAR LA MÉTHODOLOGIE (signalées) :
#   (1) RSI dans [30, 45) : la grille encadrant définit <30=0, [45,55)=15,
#       [55,70]=25, >70=10, mais laisse [30,45) implicite. Valeur par défaut
#       configurable ci-dessous (rsi_weak_recovery_points), volontairement faible.
#   (2) Position du cours « mixte » (ex : > MM20 mais < MM50) : non couverte par
#       les 3 cas de la méthodologie. Valeur intermédiaire configurable
#       (position_mixed_points), volontairement modérée.
# Ces deux valeurs sont isolées ici pour être ajustées par l'encadrant sans toucher au code.

FLASH_MOMENTUM_CONFIG = {
    # Points maximum par pilier (somme = 100)
    "pillar_max": {
        "volume":  20,
        "rsi":     25,
        "ma":      35,
        "macd":    20,
    },

    # ── Pilier VOLUME (20 pts) : 10 (Volume vs MA20 via RVOL) + 10 (tendance OBV) ──
    "volume": {
        # Sous-règle A — Volume du jour vs moyenne 20j (RVOL = Volume / MA20(Volume))
        "rvol_strong": 1.5,   # RVOL > 1.5  → pression acheteuse forte → +10
        "rvol_weak":   0.5,   # RVOL < 0.5  → volume très faible / pression vendeuse → 0
        # 0.5 ≤ RVOL ≤ 1.5 → « dans la moyenne » → +5
        "points_strong": 10,
        "points_average": 5,
        "points_weak": 0,

        # Sous-règle B — Tendance de l'OBV (flux) sur une fenêtre
        "obv_trend_window": 10,       # observations pour juger la tendance OBV (10j)
        "obv_neutral_band": 0.05,     # bande neutre : |variation OBV normalisée| < 5% → neutre
        "obv_points_rising": 10,      # OBV en hausse nette → +10
        "obv_points_neutral": 5,      # OBV neutre → +5
        "obv_points_falling": 0,      # OBV en baisse → 0
    },

    # ── Pilier RSI (25 pts) — grille encadrant ──
    "rsi": {
        "sweet_low": 55, "sweet_high": 70, "sweet_points": 25,   # 55 ≤ RSI ≤ 70 → 25
        "mid_low": 45,   "mid_points": 15,                       # 45 ≤ RSI < 55 → 15
        "overbought": 70, "overbought_points": 10,               # RSI > 70 → 10
        "oversold": 30,   "oversold_points": 0,                  # RSI < 30 → 0
        # [30, 45) : zone non définie par la méthodologie → valeur faible configurable (SIGNALÉE)
        "rsi_weak_recovery_points": 5,
    },

    # ── Pilier MOYENNES MOBILES (35 pts) = position (15) + alignement (15) + golden cross (5) ──
    "ma": {
        # Position du cours
        "position_all_points": 15,     # Cours > MM20, MM50 ET MM200 → +15
        "position_20_50_points": 10,   # Cours > MM20 ET MM50 seulement → +10
        "position_below_points": 0,    # Cours < MM20 ET MM50 → 0
        "position_mixed_points": 5,    # cas mixte non défini par la méthodologie (SIGNALÉ)

        # Alignement des moyennes
        "alignment_full_points": 15,   # MM20 > MM50 > MM200 → +15
        "alignment_partial_points": 8, # alignement partiel → +8
        "alignment_bearish_points": 0, # MM20 < MM50 < MM200 → 0

        # Golden Cross : MM50 croise MM200 vers le haut récemment
        "golden_cross_points": 5,
        "golden_cross_window": 5,      # « récent » = sur les 5 dernières séances (configurable)
    },

    # ── Pilier MACD (20 pts) — 4 états (croisement ET signe) ──
    "macd": {
        "above_positive_points": 20,   # MACD > Signal ET MACD > 0 → 20
        "above_negative_points": 12,   # MACD > Signal ET MACD < 0 → 12
        "below_positive_points": 5,    # MACD < Signal ET MACD > 0 → 5
        "below_negative_points": 0,    # MACD < Signal ET MACD < 0 → 0
    },

    # ── Classification du score (0–100) ──
    "classification": [
        # (borne_min_incluse, libellé)
        (80, "Très Fort"),
        (60, "Modéré à Positif"),
        (40, "Neutre"),
        (0,  "Faible / Baissier"),
    ],

    # ── Symboles de classe (un symbole par tranche, aligné sur la classification) ──
    #   80–100 Très Fort ......... +++
    #   60–79  Modéré à Positif ... ++
    #   40–59  Neutre ............. + / -
    #   0–39   Faible / Baissier .. --
    # (borne_min_incluse, symbole)
    "class_symbol_scale": [
        (80, "+++"),
        (60, "++"),
        (40, "+ / -"),
        (0,  "--"),
    ],

    # ── Inputs requis pour la couverture du Technical Score (Data Coverage dédié) ──
    # Chaque input pèse également ; l'absence (NaN) fait baisser la couverture.
    # SMA_200 y figure → son absence baisse mécaniquement la couverture (décision encadrant).
    "coverage_inputs": [
        "RVOL", "OBV", "RSI_14", "SMA_20", "SMA_50", "SMA_200", "MACD", "MACD_Signal",
    ],
}

# Mapping Technical Score → décision BUY/HOLD/SELL.
# ⚠️ La méthodologie encadrant définit la CLASSIFICATION (grille ci-dessus) mais pas
# de coupes explicites BUY/SELL. Ce mapping en découle directement (Neutre = HOLD,
# Modéré+/Très Fort = BUY, Faible/Baissier = SELL) et reste configurable (SIGNALÉ).
FLASH_DECISION_THRESHOLDS = {
    "buy_min_score":  60,   # score ≥ 60 (Modéré à Positif et au-dessus) → BUY
    "sell_max_score": 40,   # score < 40 (Faible / Baissier) → SELL
    # entre 40 et 60 (Neutre) → HOLD
    # couverture < MIN_COVERAGE_FOR_DECISION → INSUFFICIENT_DATA (voir section 5)
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. MAPPAGE DES SIGNAUX INDIVIDUELS
# ─────────────────────────────────────────────────────────────────────────────
# Chaque indicateur correspond à : HAUSSIER (+1), BAISSIER (−1), ou NEUTRE (0).
# Les seuils sont des hypothèses initiales — seront évalués via backtesting.

SIGNAL_RULES = {
    # ── Tendance ─────────────────────────────────────────────────────────
    "SMA_20": {
        # Prix au-dessus de SMA_20 : tendance haussière court terme
        "rule": "price_vs_indicator",
        "bullish_if": "Cours > SMA_20",
        "bearish_if": "Cours < SMA_20",
    },
    "SMA_50": {
        # Prix au-dessus de SMA_50 : tendance haussière moyen terme
        "rule": "price_vs_indicator",
        "bullish_if": "Cours > SMA_50",
        "bearish_if": "Cours < SMA_50",
    },
    "EMA_20": {
        # Proxy Golden/death cross : SMA_20 croisant EMA_20
        "rule": "price_vs_indicator",
        "bullish_if": "Cours > EMA_20",
        "bearish_if": "Cours < EMA_20",
    },

    # ── Momentum ─────────────────────────────────────────────────────────
    "RSI_14": {
        # Classique survendu/suracheté — seuils configurables
        "rule": "threshold",
        "bullish_if_below": 30,    # survendu
        "bearish_if_above": 70,    # suracheté
        # entre 30–70 → NEUTRE
    },
    "MACD": {
        # Ligne MACD croisant ligne Signal
        "rule": "macd_crossover",
        "bullish_if": "MACD > MACD_Signal",
        "bearish_if": "MACD < MACD_Signal",
        # L'histogramme confirme la direction mais est corrélé — compté une fois
        # (l'histogramme entre comme modificateur de force du signal MACD, pas signal séparé)
    },

    # ── Volume / Confirmation Prix-Volume ────────────────────────────────
    "RVOL": {
        # Le Volume Relatif confirme si un mouvement de prix a un soutien en volume
        # RVOL > 1.5 : activité inhabituellement élevée — confirme le signal de tendance
        # RVOL < 0.5 : activité très faible — affaiblit le signal de tendance
        # Utilisé comme modificateur de CONFIRMATION, pas comme signal directionnel autonome
        "rule": "volume_confirmation",
        "confirm_threshold": 1.5,  # volume fort
        "weak_threshold":    0.5,  # volume faible
    },
    "VWAP": {
        # Prix au-dessus du VWAP : acheteurs dominant intraday
        "rule": "price_vs_indicator",
        "bullish_if": "Cours > VWAP",
        "bearish_if": "Cours < VWAP",
    },

    # ── Risque / Volatilité ──────────────────────────────────────────────
    "HV_20": {
        # La Volatilité Historique N'EST PAS un signal directionnel.
        # Vol élevée → pénalise Confiance, pas Score.
        # Les seuils référencent la distribution de HV à travers l'univers.
        "rule": "volatility_context",
        "high_vol_percentile": 75,   # au-dessus de p75 de l'univers → pénalité de confiance
        "low_vol_percentile":  25,   # en dessous de p25 → bonus de confiance
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. FAMILLES DE SIGNAUX & POIDS DES SCORES
# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  CRITIQUE : HYPOTHÈSE DE BASE — PAS ENCORE VALIDÉE SCIENTIFIQUEMENT  ⚠️
#
# Les poids ci-dessous sont des ESTIMATIONS INITIALES D'EXPERT utilisées pour valider que
# le pipeline fonctionne de bout en bout. Ils NE SONT PAS prouvés pour produire des
# décisions de trading rentables.
#
# Statut : HYPOTHÈSE NÉCESSITANT BACKTESTING
# ───────────────────────────────────────────
# Ces poids seront évalués via backtesting historique à travers les
# configurations A–E. La configuration finale est sélectionnée après :
#
#   1. Observation des performances sur période de développement
#   2. Confirmation de stabilité sur période de validation
#   3. Évaluation de multiples critères (pas seulement le rendement) :
#        • Taux de réussite (% de décisions BUY avec forward_return > 0)
#        • Ratio de Sharpe (rendement ajusté au risque)
#        • Drawdown maximum (pire perte pic-à-creux)
#        • Stabilité des décisions (rotation, faux signaux)
#
# La méthodologie est considérée validée SEULEMENT après que le backtesting montre
# une robustesse à travers différentes configurations de poids et périodes temporelles.
#
# NE PAS présenter ces poids comme "optimaux" ou "scientifiquement prouvés"
# jusqu'à ce que le notebook 12 (backtesting) soit complet.
#
# Justification de l'hypothèse de base :
#   Tendance 35 %  — capture le régime directionnel dominant
#   Momentum 35 %  — capture le timing d'entrée dans ce régime
#   Volume 20 %    — couche de confirmation ; secondaire par rapport à prix/momentum
#   Risque 10 %    — couche de contexte/pénalité ; pas un vote directionnel

SCORE_WEIGHTS = {
    "Trend":     0.35,   # SMA_20, SMA_50, EMA_20
    "Momentum":  0.35,   # RSI_14, MACD
    "Volume":    0.20,   # RVOL (confirmation), VWAP
    "Risk":      0.10,   # HV_20 (contexte/pénalité)
}

# Marquer comme baseline pour éviter utilisation accidentelle comme "validé"
WEIGHTS_STATUS = "BASELINE_HYPOTHESIS"  # Changer en "VALIDATED" après backtesting

# Configurations de poids alternatives pour analyse de sensibilité :
SCORE_WEIGHT_CONFIGS = {
    "A_baseline":    {"Trend": 0.35, "Momentum": 0.35, "Volume": 0.20, "Risk": 0.10},
    "B_more_mom":    {"Trend": 0.30, "Momentum": 0.40, "Volume": 0.20, "Risk": 0.10},
    "C_more_trend":  {"Trend": 0.40, "Momentum": 0.30, "Volume": 0.20, "Risk": 0.10},
    "D_more_vol":    {"Trend": 0.30, "Momentum": 0.30, "Volume": 0.30, "Risk": 0.10},
    "E_less_risk":   {"Trend": 0.40, "Momentum": 0.35, "Volume": 0.20, "Risk": 0.05},
}

# Normalisation des scores : le score global final (OverallScore) est sur [0, 100].
# Un signal purement haussier dans une famille score 100 ; purement baissier score 0 ; neutre 50.
SCORE_NEUTRAL = 50.0
SCORE_MAX     = 100.0
SCORE_MIN     = 0.0

# ─────────────────────────────────────────────────────────────────────────────
# 5. SCORE DE CONFIANCE — INDÉPENDANT DU SCORE GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  DISTINCTION CRITIQUE  ⚠️
#
# Score Global    → mesure la DIRECTION & FORCE des signaux de marché
#                   (0 = fortement baissier, 50 = neutre, 100 = fortement haussier)
#
# Confiance       → mesure la QUALITÉ & FIABILITÉ de ces signaux
#                   (0% = données peu fiables, 100% = signaux unanimes de haute qualité)
#
# Ce sont des dimensions INDÉPENDANTES. Les combinaisons valides incluent :
#
#   Score=82, Confiance=42%
#     → Les signaux disponibles sont fortement haussiers, mais les données sont éparses ou
#        les familles sont en désaccord ou la volatilité est anormalement élevée.
#        Interprétation : "signal haussier avec faible conviction"
#
#   Score=48, Confiance=91%
#     → Signal directionnel faible (proche de neutre), mais avec excellente couverture
#        de données, accord unanime des familles, et volatilité stable.
#        Interprétation : "aucun mouvement fort attendu, haute confiance"
#
# La Confiance ne regarde JAMAIS si le score est extrême ou modéré —
# elle évalue uniquement la QUALITÉ DES DONNÉES derrière ce score.
#
# Trois composantes :
#   A. Couverture des Données (40%) — fraction d'indicateurs requis qui sont calculables
#   B. Accord des Familles (40%)    — les familles Tendance/Momentum/Volume sont-elles d'accord sur la direction ?
#   C. Pénalité de Risque (20%)     — réduire la confiance quand HV est anormalement élevée

CONFIDENCE_WEIGHTS = {
    "data_coverage":    0.40,   # pénalise les indicateurs manquants
    "family_agreement": 0.40,   # pénalise le désaccord entre familles
    "risk_penalty":     0.20,   # pénalise volatilité élevée / données faibles
}

# Couverture minimale des données pour produire une décision (en dessous → INSUFFICIENT_DATA)
MIN_COVERAGE_FOR_DECISION = 0.50   # au moins 50% des indicateurs doivent être valides

# ─────────────────────────────────────────────────────────────────────────────
# 6. SEUILS DE DÉCISION
# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  HYPOTHÈSE DE BASE — NÉCESSITE VALIDATION PAR BACKTESTING  ⚠️
#
# Ces seuils sont des estimations initiales. Ils n'ont PAS été prouvés pour
# produire des décisions de trading rentables. Le notebook de backtesting (12) va
# évaluer ces seuils contre des données historiques et peut recommander des
# ajustements basés sur :
#   • Taux de réussite (% de décisions BUY/SELL qui étaient correctes)
#   • Rendements ajustés au risque (ratio de Sharpe)
#   • Contrôle du drawdown (perte maximale)
#
# Politique actuelle :
#   BUY  → Score ≥ 60 ET Confiance ≥ 60%
#   SELL → Score ≤ 40 ET Confiance ≥ 60%
#   HOLD → tout le reste (sauf si couverture des données < 50%)

DECISION_THRESHOLDS = {
    "buy":           {"min_score": 60, "min_confidence": 60},
    "sell":          {"max_score": 40, "min_confidence": 60},
    # Tout le reste → HOLD
    # En dessous de MIN_COVERAGE_FOR_DECISION → INSUFFICIENT_DATA
}

THRESHOLDS_STATUS = "BASELINE_HYPOTHESIS"  # Changer en "VALIDATED" après backtesting

# Grille d'analyse de sensibilité (appliquée lors de l'évaluation du backtesting) :
DECISION_THRESHOLD_GRID = {
    "buy_score":        [55, 60, 65, 70],
    "sell_score":       [30, 35, 40, 45],
    "min_confidence":   [50, 60, 70, 80],
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. PROTOCOLE DE BACKTESTING
# ─────────────────────────────────────────────────────────────────────────────
# Horizons de rendement forward pour évaluer les décisions.
# Choisis avant de regarder les résultats — pas ajustés post-hoc.

BACKTEST_CONFIG = {
    # Horizons de rendement forward (séances de trading, pas jours calendaires)
    "horizons": [5, 10, 20],          # ~1 semaine, 2 semaines, 1 mois

    # Division temporelle — strictement chronologique, PAS de mélange aléatoire.
    # Étant donné notre fenêtre d'échantillon de 28 séances, nous utilisons :
    #   Développement : premiers 60% des dates (séances 1–17)
    #   Validation :    20% suivants         (séances 18–22)
    #   Test :          20% finaux           (séances 23–28)
    # La période de test n'est évaluée qu'après que la méthodologie soit figée.
    "split": {
        "development": 0.60,
        "validation":  0.20,
        "test":        0.20,
    },

    # Séances minimales requises dans une période pour être significative
    "min_sessions_per_period": 5,

    # Métriques à calculer par configuration
    "metrics": [
        "avg_forward_return_BUY",    # rendement forward moyen pour décisions BUY
        "avg_forward_return_SELL",   # rendement forward moyen pour décisions SELL
        "avg_forward_return_HOLD",   # rendement forward moyen pour décisions HOLD
        "hit_rate",                  # fraction de décisions BUY où forward_return > 0
        "sharpe_ratio",              # rendement annualisé / vol annualisée des décisions
        "max_drawdown",              # pire pic-à-creux sur période d'évaluation
        "n_decisions",               # nombre total de décisions BUY/SELL
    ],

    # Protection contre le biais look-ahead : à la date t, utiliser SEULEMENT les données disponibles à t.
    # Le rendement forward est calculé APRÈS que la décision soit générée.
    # Ceci est imposé dans le code en décalant les séries de prix.
    "lookahead_guard": True,
}
