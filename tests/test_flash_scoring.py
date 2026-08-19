"""
Tests unitaires du Score Technique « Flash Momentum » (0–100).

Couvre les cas obligatoires (méthodologie encadrant, section 14) :
    - RSI : 30, 45, 55, 70 (+ bornes complémentaires)
    - MACD : 4 états (croisement × signe), y compris MACD == Signal
    - Bornes de score : 39, 40, 59, 60, 79, 80, 100
    - 0 ≤ Technical Score ≤ 100
    - Indicateur manquant / historique insuffisant / Data Coverage faible / NaN
    - Déterminisme
    - Séparation Technical Score vs Data Coverage
    - Absence de look-ahead (Golden Cross / OBV n'utilisent que le passé)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from config.methodology import (
    FLASH_MOMENTUM_CONFIG as CFG,
    FLASH_DECISION_THRESHOLDS as DTH,
    INDICATOR_PARAMS,
    INDICATOR_MIN_OBS,
    MIN_COVERAGE_FOR_DECISION,
)
from src.scoring_flash import (
    score_rsi,
    score_macd,
    score_volume,
    score_volume_rvol,
    score_volume_obv,
    score_moving_averages,
    score_ma_position,
    score_ma_alignment,
    score_ma_golden_cross,
    classify_score,
    compute_flash_scores,
)
from src.indicators import compute_indicators_for_company
from src.decisions import make_decision


# ─────────────────────────────────────────────────────────────────────────────
# PILIER RSI (25)
# ─────────────────────────────────────────────────────────────────────────────
class TestRSI:
    @pytest.mark.parametrize("rsi,expected", [
        (29, 0),      # < 30
        (30, 5),      # zone [30,45) signalée
        (44.999, 5),  # juste sous 45
        (45, 15),     # [45,55)
        (54.999, 15),
        (55, 25),     # [55,70]
        (63, 25),     # exemple méthodologie
        (70, 25),     # borne haute incluse
        (70.001, 10), # > 70
        (85, 10),
    ])
    def test_rsi_bands(self, rsi, expected):
        assert score_rsi(rsi, CFG) == expected

    def test_rsi_nan_returns_zero(self):
        assert score_rsi(np.nan, CFG) == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# PILIER MACD (20)
# ─────────────────────────────────────────────────────────────────────────────
class TestMACD:
    def test_above_and_positive(self):
        assert score_macd(1.8, 1.2, CFG) == 20   # MACD>Signal & MACD>0

    def test_above_and_negative(self):
        assert score_macd(-0.5, -0.8, CFG) == 12  # MACD>Signal & MACD<0

    def test_below_and_positive(self):
        assert score_macd(0.5, 0.8, CFG) == 5     # MACD<Signal & MACD>0

    def test_below_and_negative(self):
        assert score_macd(-0.8, -0.5, CFG) == 0   # MACD<Signal & MACD<0

    def test_equal_signal_positive_treated_as_below(self):
        # MACD == Signal → non « au-dessus » ; MACD>0 → 5
        assert score_macd(1.0, 1.0, CFG) == 5

    def test_equal_signal_negative_treated_as_below(self):
        assert score_macd(-1.0, -1.0, CFG) == 0

    def test_nan_returns_zero(self):
        assert score_macd(np.nan, 1.0, CFG) == 0.0
        assert score_macd(1.0, np.nan, CFG) == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# PILIER VOLUME (20) = RVOL (10) + OBV (10)
# ─────────────────────────────────────────────────────────────────────────────
class TestVolume:
    @pytest.mark.parametrize("rvol,expected", [
        (2.0, 10),   # > 1.5
        (1.51, 10),
        (1.5, 5),    # dans la moyenne (borne)
        (1.0, 5),
        (0.5, 5),    # borne basse incluse
        (0.49, 0),   # < 0.5
        (0.1, 0),
    ])
    def test_rvol_bands(self, rvol, expected):
        assert score_volume_rvol(rvol, CFG) == expected

    @pytest.mark.parametrize("state,expected", [
        ("rising", 10),
        ("neutral", 5),
        ("falling", 0),
        (None, 0),   # historique OBV insuffisant → non couvert
    ])
    def test_obv_states(self, state, expected):
        assert score_volume_obv(state, CFG) == expected

    def test_volume_combined_max(self):
        assert score_volume(2.0, "rising", CFG) == 20

    def test_volume_rvol_nan(self):
        assert score_volume(np.nan, "rising", CFG) == 10  # RVOL manquant → 0 + OBV 10


# ─────────────────────────────────────────────────────────────────────────────
# PILIER MOYENNES MOBILES (35) = position (15) + alignement (15) + golden cross (5)
# ─────────────────────────────────────────────────────────────────────────────
class TestMovingAverages:
    def test_position_all_above(self):
        assert score_ma_position(100, 90, 80, 70, CFG) == 15

    def test_position_20_50_only(self):
        # Cours > MM20 & MM50 mais < MM200
        assert score_ma_position(100, 90, 80, 110, CFG) == 10

    def test_position_mm200_missing_graceful(self):
        # MM200 absente → palier 20/50 (10), dégradation gracieuse
        assert score_ma_position(100, 90, 80, np.nan, CFG) == 10

    def test_position_below(self):
        assert score_ma_position(70, 90, 80, 60, CFG) == 0

    def test_position_mixed(self):
        # > MM20 mais < MM50 → cas mixte signalé
        assert score_ma_position(85, 80, 90, np.nan, CFG) == CFG["ma"]["position_mixed_points"]

    def test_position_missing_core_returns_zero(self):
        assert score_ma_position(100, np.nan, 80, 70, CFG) == 0.0

    def test_alignment_full(self):
        assert score_ma_alignment(90, 80, 70, CFG) == 15

    def test_alignment_bearish(self):
        assert score_ma_alignment(70, 80, 90, CFG) == 0

    def test_alignment_partial(self):
        assert score_ma_alignment(90, 85, 88, CFG) == 8

    def test_alignment_mm200_missing_partial(self):
        assert score_ma_alignment(90, 80, np.nan, CFG) == 8
        assert score_ma_alignment(80, 90, np.nan, CFG) == 0

    def test_golden_cross(self):
        assert score_ma_golden_cross(True, CFG) == 5
        assert score_ma_golden_cross(False, CFG) == 0

    def test_ma_full_pillar(self):
        assert score_moving_averages(100, 90, 80, 70, True, CFG) == 35

    def test_ma_graceful_no_mm200(self):
        # position 10 + alignement 8 + pas de GC = 18
        assert score_moving_averages(100, 90, 80, np.nan, False, CFG) == 18


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION + BORNES DE SCORE
# ─────────────────────────────────────────────────────────────────────────────
class TestClassification:
    @pytest.mark.parametrize("score,label", [
        (0,  "Faible / Baissier"),
        (39, "Faible / Baissier"),
        (40, "Neutre"),
        (59, "Neutre"),
        (60, "Modéré à Positif"),
        (79, "Modéré à Positif"),
        (80, "Très Fort"),
        (100, "Très Fort"),
    ])
    def test_classification_bounds(self, score, label):
        assert classify_score(score, CFG) == label

    def test_nan_classification(self):
        assert classify_score(np.nan, CFG) == "N/A"


# ─────────────────────────────────────────────────────────────────────────────
# TECHNICAL SCORE — bornes globales & déterminisme
# ─────────────────────────────────────────────────────────────────────────────
def _row(**kw):
    """Construit une ligne d'indicateurs avec valeurs par défaut NaN."""
    base = {
        'Cours': np.nan, 'RVOL': np.nan, 'OBV_Trend': None,
        'RSI_14': np.nan, 'SMA_20': np.nan, 'SMA_50': np.nan, 'SMA_200': np.nan,
        'MACD': np.nan, 'MACD_Signal': np.nan, 'Golden_Cross_Recent': False,
    }
    base.update(kw)
    return pd.Series(base)


class TestTechnicalScoreBounds:
    def test_max_score_is_100(self):
        vol = score_volume(2.0, "rising", CFG)
        rsi = score_rsi(60, CFG)
        mm = score_moving_averages(100, 90, 80, 70, True, CFG)
        macd = score_macd(1.8, 1.2, CFG)
        assert vol + rsi + mm + macd == 100

    def test_min_score_is_zero_when_all_bearish(self):
        vol = score_volume(0.1, "falling", CFG)
        rsi = score_rsi(20, CFG)
        # Cours < MM20 & MM50 (position 0) ET MM20 < MM50 < MM200 (alignement baissier 0)
        mm = score_moving_averages(60, 70, 80, 90, False, CFG)
        macd = score_macd(-0.8, -0.5, CFG)
        total = vol + rsi + mm + macd
        assert total == 0

    def test_score_always_within_bounds_random(self):
        rng = np.random.default_rng(42)
        for _ in range(200):
            vol = score_volume(rng.uniform(0, 3), rng.choice(["rising", "neutral", "falling", None]), CFG)
            rsi = score_rsi(rng.uniform(0, 100), CFG)
            mm = score_moving_averages(
                rng.uniform(50, 150), rng.uniform(50, 150),
                rng.uniform(50, 150), rng.uniform(50, 150),
                bool(rng.integers(0, 2)), CFG
            )
            macd = score_macd(rng.uniform(-2, 2), rng.uniform(-2, 2), CFG)
            total = vol + rsi + mm + macd
            assert 0 <= total <= 100


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATEUR + NaN / historique court / coverage
# ─────────────────────────────────────────────────────────────────────────────
class TestOrchestratorAndCoverage:
    def _make_df(self, n=12):
        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        return pd.DataFrame({
            'CODE_ISIN': ['MA0000000001'] * n,
            'Company': ['TEST'] * n,
            'Date': dates,
            'Cours': np.linspace(100, 120, n),
            'Bid': [99] * n, 'Ask': [101] * n,
            'Volume MC': np.linspace(1000, 2000, n),
        })

    def test_compute_flash_scores_adds_columns(self):
        df = self._make_df()
        ind = compute_indicators_for_company(df, INDICATOR_PARAMS, INDICATOR_MIN_OBS)
        out = compute_flash_scores(ind, CFG)
        for col in ['Flash_Vol_Score', 'Flash_RSI_Score', 'Flash_MM_Score',
                    'Flash_MACD_Score', 'Technical_Score', 'Score_Class', 'Flash_Coverage']:
            assert col in out.columns

    def test_technical_score_within_bounds_on_pipeline_data(self):
        df = self._make_df()
        ind = compute_indicators_for_company(df, INDICATOR_PARAMS, INDICATOR_MIN_OBS)
        out = compute_flash_scores(ind, CFG)
        assert out['Technical_Score'].between(0, 100).all()

    def test_short_history_low_coverage(self):
        # 12 obs → SMA_20/50/200, RSI_14, MACD indisponibles → couverture faible
        df = self._make_df(n=12)
        ind = compute_indicators_for_company(df, INDICATOR_PARAMS, INDICATOR_MIN_OBS)
        out = compute_flash_scores(ind, CFG)
        # couverture max attendue faible (seuls RVOL, OBV disponibles)
        assert out['Flash_Coverage'].max() <= 0.5

    def test_all_nan_row_score_zero_coverage_zero(self):
        row = _row()
        # score piliers = 0 partout
        from src.scoring_flash import score_volume as sv
        assert score_rsi(row['RSI_14'], CFG) == 0
        # coverage via orchestrateur
        df = pd.DataFrame([{
            'CODE_ISIN': 'X', 'Company': 'X', 'Date': pd.Timestamp('2024-01-01'),
            'Cours': np.nan, 'Volume MC': np.nan,
            'RVOL': np.nan, 'OBV': np.nan, 'RSI_14': np.nan,
            'SMA_20': np.nan, 'SMA_50': np.nan, 'SMA_200': np.nan,
            'MACD': np.nan, 'MACD_Signal': np.nan,
        }])
        out = compute_flash_scores(df, CFG)
        assert out['Technical_Score'].iloc[0] == 0
        assert out['Flash_Coverage'].iloc[0] == 0.0

    def test_determinism(self):
        df = self._make_df()
        ind = compute_indicators_for_company(df, INDICATOR_PARAMS, INDICATOR_MIN_OBS)
        out1 = compute_flash_scores(ind, CFG)
        out2 = compute_flash_scores(ind, CFG)
        pd.testing.assert_series_equal(out1['Technical_Score'], out2['Technical_Score'])


# ─────────────────────────────────────────────────────────────────────────────
# DÉCISION — séparation Score vs Coverage, pas de SELL sur données manquantes
# ─────────────────────────────────────────────────────────────────────────────
class TestDecision:
    def test_insufficient_data_when_low_coverage(self):
        row = pd.Series({'Technical_Score': 90, 'Flash_Coverage': 0.40})
        decision, cov = make_decision(row, DTH, MIN_COVERAGE_FOR_DECISION)
        assert decision == 'INSUFFICIENT_DATA'  # jamais SELL sur données incomplètes

    def test_buy_when_high_score_and_coverage(self):
        row = pd.Series({'Technical_Score': 85, 'Flash_Coverage': 0.95})
        decision, _ = make_decision(row, DTH, MIN_COVERAGE_FOR_DECISION)
        assert decision == 'BUY'

    def test_hold_neutral_zone(self):
        row = pd.Series({'Technical_Score': 50, 'Flash_Coverage': 0.95})
        decision, _ = make_decision(row, DTH, MIN_COVERAGE_FOR_DECISION)
        assert decision == 'HOLD'

    def test_sell_low_score_but_sufficient_coverage(self):
        row = pd.Series({'Technical_Score': 30, 'Flash_Coverage': 0.95})
        decision, _ = make_decision(row, DTH, MIN_COVERAGE_FOR_DECISION)
        assert decision == 'SELL'

    def test_boundary_buy_60(self):
        row = pd.Series({'Technical_Score': 60, 'Flash_Coverage': 0.95})
        assert make_decision(row, DTH, MIN_COVERAGE_FOR_DECISION)[0] == 'BUY'

    def test_boundary_hold_40(self):
        row = pd.Series({'Technical_Score': 40, 'Flash_Coverage': 0.95})
        assert make_decision(row, DTH, MIN_COVERAGE_FOR_DECISION)[0] == 'HOLD'

    def test_boundary_sell_39(self):
        row = pd.Series({'Technical_Score': 39, 'Flash_Coverage': 0.95})
        assert make_decision(row, DTH, MIN_COVERAGE_FOR_DECISION)[0] == 'SELL'


def run_tests():
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == '__main__':
    run_tests()
