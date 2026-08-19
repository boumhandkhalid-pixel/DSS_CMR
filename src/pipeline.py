"""
Production pipeline orchestrator for DSS (Decision Support System).

This module provides the complete end-to-end pipeline from raw Excel files
to final BUY/HOLD/SELL decisions, ready for Streamlit UI integration.

Architecture:
    Raw Excel → Parse → Quality Filter → Dynamic Filter → Indicators → 
    Signals → Scoring → Confidence → Decisions → Parquet output

All business logic is in config/methodology.py.
All I/O uses Parquet for performance (Excel → Parquet on upload).
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Import existing modules
from src.ingestion import ingest_workbook
from src.validation import (
    load_unified_dataset,
    save_unified_dataset,
    validate_dataset,
    filter_companies_by_usable_data
)
from config.methodology import (
    FILTER_CONFIG,
    compute_filter_thresholds,
    MIN_CONSECUTIVE,
    MAX_GAP_DAYS,
    INDICATOR_PARAMS,
    INDICATOR_MIN_OBS,
    SIGNAL_RULES,
    SCORE_WEIGHTS,
    CONFIDENCE_WEIGHTS,
    DECISION_THRESHOLDS,
    MIN_COVERAGE_FOR_DECISION,
    FLASH_MOMENTUM_CONFIG,
    FLASH_DECISION_THRESHOLDS,
)


class DSS_Pipeline:
    """
    Complete DSS pipeline orchestrator.
    
    Usage:
        pipeline = DSS_Pipeline()
        
        # Step 1: Upload and parse market data
        unified_df = pipeline.ingest_market_data('path/to/market.xlsx')
        
        # Step 2: Upload and parse index composition
        composition_df = pipeline.ingest_index_composition('path/to/composition.xlsx')
        
        # Step 3: Run complete pipeline
        results = pipeline.run_pipeline(unified_df, composition_df)
        
        # Step 4: Get final recommendations
        recommendations = results['decisions_summary']
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize pipeline with optional data directory.
        
        Args:
            data_dir: Directory to save intermediate Parquet files.
                     Defaults to ./data/
        """
        if data_dir is None:
            data_dir = Path.cwd() / 'data'
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.reports = {}  # Store all pipeline reports
    
    def excel_to_parquet(self, excel_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert Excel file to Parquet for fast processing.
        
        Args:
            excel_path: Path to Excel file
            output_path: Optional output path. If None, auto-generated.
        
        Returns:
            Path to generated Parquet file
        """
        df = pd.read_excel(excel_path)
        
        if output_path is None:
            stem = Path(excel_path).stem
            output_path = str(self.data_dir / f'{stem}.parquet')
        
        df.to_parquet(output_path, compression='snappy', index=False)
        return output_path
    
    def ingest_market_data(
        self, 
        excel_path: str,
        required_vars: Optional[set] = None
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Ingest market data Excel workbook.
        
        Args:
            excel_path: Path to market data Excel file
            required_vars: Set of required variable names
        
        Returns:
            (unified_df, ingest_report)
        """
        if required_vars is None:
            required_vars = {'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
        
        unified, report = ingest_workbook(excel_path, required_variables=required_vars)
        self.reports['ingestion'] = report
        
        # Convert object columns to string to avoid Parquet datetime errors (skip Date column)
        for col in unified.select_dtypes(include=['object']).columns:
            if col not in ['Date']:  # Keep Date as datetime
                unified[col] = unified[col].astype(str)
        
        # Save to Parquet
        out_path = str(self.data_dir / 'market_data_raw.parquet')
        save_unified_dataset(unified, out_path)
        
        return unified, report
    
    def ingest_index_composition(
        self,
        excel_path: str,
        index_name: Optional[str] = None
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Ingest index composition Excel file (version robuste multi-feuilles).
        
        Args:
            excel_path: Path to composition Excel file
            index_name: Index to filter (e.g., 'MASI 20'). If None, uses config.
        
        Returns:
            (composition_df, parse_report)
        """
        from src.parsers.composition_parser import parse_composition_file
        
        if index_name is None:
            index_name = FILTER_CONFIG['index']
        
        print(f"\n[INFO] Import composition d'indice : '{index_name}'")
        print("=" * 70)
        
        # Utiliser le parser robuste multi-feuilles
        df, report = parse_composition_file(
            excel_path,
            index_name=index_name,
            validate=True
        )
        
        print("=" * 70)
        print(f"[INFO] ✓ Composition chargée : {len(df)} titres pour l'indice '{index_name}'")
        print(f"[INFO] ✓ Colonnes disponibles : {list(df.columns)}\n")
        
        # Rapport pour UI
        ui_report = {
            'index': index_name,
            'total_securities': len(df),
            'columns': list(df.columns),
            'indices_available': report.get('indices_found', []),
            'sheets_processed': report.get('sheets_processed', []),
        }
        
        self.reports['composition'] = ui_report
        
        # Convert object columns to string to avoid Parquet datetime errors
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str)
        
        # Save to Parquet
        out_path = str(self.data_dir / 'index_composition.parquet')
        df.to_parquet(out_path, compression='snappy', index=False)
        
        return df, ui_report
    
    def apply_quality_filter(self, unified_df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """
        Apply NEW temporal quality filter (Coverage Graceful approach).
        
        DOES NOT reject based on number of observations.
        ONLY rejects if temporal quality is poor (gaps > 7 days).
        
        Each indicator will manage its own minimum observations.
        """
        from src.validation import filter_companies_by_temporal_quality, drop_empty_companies
        
        # Étape 0 : nettoyage — retirer les sociétés à Cours/Volume entièrement vides ou nuls
        cleaned, clean_report = drop_empty_companies(unified_df)
        n_removed = clean_report.get('companies_removed', 0)
        if n_removed:
            print(f"[INFO] Nettoyage pré-analyse : {n_removed} société(s) vide(s)/nulle(s) retirée(s) "
                  f"({clean_report['companies_before']} → {clean_report['companies_after']})")
        
        # Contrôle qualité temporelle (continuité, gap ≤ MAX_GAP_DAYS)
        filtered, report = filter_companies_by_temporal_quality(
            cleaned,
            max_gap_days=MAX_GAP_DAYS  # 7 days
        )
        report['cleanup'] = clean_report
        
        self.reports['quality_filter'] = report
        
        # Save to Parquet
        out_path = str(self.data_dir / 'unified_dataset.parquet')
        save_unified_dataset(filtered, out_path)
        
        return filtered, report
    
    def apply_dynamic_filter(
        self,
        unified_df: pd.DataFrame,
        composition_df: pd.DataFrame,
        index_name: Optional[str] = None,
        top_n: Optional[int] = None
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Filtrage dynamique de l'univers investissable (règles encadrant).

        Deux indices supportés :
          - MASI    : on retient les N PREMIÈRES sociétés par POIDS FLOTTANT (top-N).
          - MASI 20 : on retient TOUS les titres de l'indice.

        La capitalisation flottante n'est PLUS une porte de filtrage.

        Args:
            unified_df: données marché après contrôle qualité
            composition_df: composition déjà filtrée sur l'indice sélectionné
            index_name: indice de référence (défaut = FILTER_CONFIG['index'])
            top_n: override du nombre de sociétés pour le MASI (défaut = config)

        Returns:
            (investable_df, filter_report)
        """
        from src.parsers.composition_parser import normalize_index_name

        if index_name is None:
            index_name = FILTER_CONFIG['index']

        norm_target = normalize_index_name(index_name)
        norm_masi = normalize_index_name('MASI')
        norm_masi20 = normalize_index_name('MASI 20')

        print(f"[INFO] Filtrage dynamique — indice cible : '{index_name}'")
        print(f"[INFO] Composition reçue : {len(composition_df)} titres, "
              f"colonnes={list(composition_df.columns)}")

        comp = composition_df.copy()

        # ── Règle de sélection selon l'indice ──
        if norm_target == norm_masi20:
            # MASI 20 : tous les titres de l'indice
            selected = comp
            rule = f"MASI 20 : tous les titres de l'indice ({len(selected)})"
        elif norm_target == norm_masi:
            # MASI : top-N par poids flottant
            n = int(top_n) if top_n else int(FILTER_CONFIG.get('masi_top_n_by_weight', 40))
            if 'Weight' in comp.columns:
                selected = comp.sort_values('Weight', ascending=False).head(n)
            else:
                selected = comp.head(n)
            rule = f"MASI : {len(selected)} premières sociétés par poids flottant (top {n})"
        else:
            # Indice non supporté → on retient tout par sécurité, mais on le signale
            selected = comp
            rule = f"{index_name} : indice non supporté officiellement — tous les titres retenus"
            print(f"[WARN] Indice '{index_name}' non supporté (attendus : MASI, MASI 20).")

        print(f"[INFO] Règle appliquée : {rule}")

        selected_isins = set(selected['CODE_ISIN'].dropna().unique())

        # Gate 1 : jointure par ISIN (le titre doit exister dans le marché)
        before = len(unified_df)
        filtered = unified_df[unified_df['CODE_ISIN'].isin(selected_isins)].copy()
        after = len(filtered)
        print(f"[INFO] Jointure marché ∩ sélection : {before} → {after} lignes "
              f"({filtered['CODE_ISIN'].nunique()} sociétés retenues)")

        # Fusion des colonnes de composition (analyse : poids, facteur/cap flottants)
        comp_cols = [c for c in ['CODE_ISIN', 'FF', 'FF_MarketCap', 'Weight'] if c in selected.columns]
        filtered = filtered.merge(selected[comp_cols], on='CODE_ISIN', how='left')

        # Seuils de contexte (reporting uniquement, aucune porte)
        try:
            thresholds = compute_filter_thresholds(selected)
        except Exception:
            thresholds = {}

        report = {
            'index': index_name,
            'selection_rule': rule,
            'input_rows': len(unified_df),
            'output_rows': len(filtered),
            'input_companies': unified_df['CODE_ISIN'].nunique(),
            'selected_companies': len(selected_isins),
            'output_companies': filtered['CODE_ISIN'].nunique(),
            'thresholds': thresholds,
        }

        self.reports['dynamic_filter'] = report

        # Save to Parquet
        out_path = str(self.data_dir / 'investable_universe.parquet')
        save_unified_dataset(filtered, out_path)

        return filtered, report
    
    def compute_indicators(self, investable_df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """
        Compute technical indicators with validity tracking.
        
        Args:
            investable_df: Investable universe data
        
        Returns:
            (indicators_df, compute_report)
        """
        from src.indicators import compute_all_indicators
        
        indicators_df = compute_all_indicators(
            investable_df,
            params=INDICATOR_PARAMS,
            min_obs=INDICATOR_MIN_OBS
        )
        
        report = {
            'input_rows': len(investable_df),
            'output_rows': len(indicators_df),
            'indicators_added': 10,
            'validity_columns_added': 10,
        }
        
        self.reports['indicators'] = report
        
        # Save to Parquet
        out_path = str(self.data_dir / 'indicators.parquet')
        save_unified_dataset(indicators_df, out_path)
        
        return indicators_df, report
    
    def compute_signals_and_scores(
        self,
        indicators_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Compute signals, family scores, overall score, and confidence.
        
        Args:
            indicators_df: Data with indicators
        
        Returns:
            (signals_df, compute_report)
        """
        from src.signals import compute_signals_and_confidence
        from src.scoring_flash import compute_flash_scores
        
        # Vue analytique : signaux individuels {-1,0,+1}, familles, confiance (conservés)
        signals_df = compute_signals_and_confidence(
            indicators_df,
            signal_rules=SIGNAL_RULES,
            score_weights=SCORE_WEIGHTS,
            confidence_weights=CONFIDENCE_WEIGHTS
        )
        
        # Score technique officiel « Flash Momentum » (0–100) — source de vérité métier
        signals_df = compute_flash_scores(signals_df, FLASH_MOMENTUM_CONFIG)
        
        report = {
            'input_rows': len(indicators_df),
            'output_rows': len(signals_df),
            'signals_computed': 8,
            'family_scores_computed': 3,
            'overall_score_rows': signals_df['Overall_Score'].notna().sum(),
            'confidence_rows': signals_df['Confidence'].notna().sum(),
            'technical_score_rows': signals_df['Technical_Score'].notna().sum(),
        }
        
        self.reports['signals'] = report
        
        # Save to Parquet
        out_path = str(self.data_dir / 'signals.parquet')
        save_unified_dataset(signals_df, out_path)
        
        return signals_df, report
    
    def make_decisions(self, signals_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
        """
        Generate BUY/HOLD/SELL decisions.
        
        Args:
            signals_df: Data with signals and scores
        
        Returns:
            (decisions_df, decisions_summary_df, report)
        """
        from src.decisions import make_investment_decisions, generate_summary
        
        decisions_df = make_investment_decisions(
            signals_df,
            flash_thresholds=FLASH_DECISION_THRESHOLDS,
            min_coverage=MIN_COVERAGE_FOR_DECISION
        )
        
        decisions_summary_df = generate_summary(decisions_df)
        
        report = {
            'total_rows': len(decisions_df),
            'buy': (decisions_df['Decision'] == 'BUY').sum(),
            'hold': (decisions_df['Decision'] == 'HOLD').sum(),
            'sell': (decisions_df['Decision'] == 'SELL').sum(),
            'insufficient_data': (decisions_df['Decision'] == 'INSUFFICIENT_DATA').sum(),
            'companies': len(decisions_summary_df),
        }
        
        self.reports['decisions'] = report
        
        # Save to Parquet
        save_unified_dataset(decisions_df, str(self.data_dir / 'decisions.parquet'))
        decisions_summary_df.to_parquet(
            str(self.data_dir / 'decisions_summary.parquet'),
            compression='snappy',
            index=False
        )
        
        return decisions_df, decisions_summary_df, report
    
    def run_pipeline(
        self,
        market_df: pd.DataFrame,
        composition_df: pd.DataFrame
    ) -> dict:
        """
        Run complete pipeline from parsed data to decisions.
        
        Args:
            market_df: Parsed market data (from ingest_market_data)
            composition_df: Parsed composition (from ingest_index_composition)
        
        Returns:
            dict with all outputs and reports
        """
        print("🔄 Running DSS Pipeline...")
        
        # Step 1: Quality filter
        print("  1/5 Applying quality filter...")
        unified, quality_report = self.apply_quality_filter(market_df)
        
        # Step 2: Dynamic filter
        print("  2/5 Applying dynamic investability filter...")
        investable, filter_report = self.apply_dynamic_filter(unified, composition_df)
        
        # Step 3: Indicators
        print("  3/5 Computing technical indicators...")
        indicators, ind_report = self.compute_indicators(investable)
        
        # Step 4: Signals & Scores
        print("  4/5 Computing signals and scores...")
        signals, sig_report = self.compute_signals_and_scores(indicators)
        
        # Step 5: Decisions
        print("  5/5 Generating investment decisions...")
        decisions, decisions_summary, dec_report = self.make_decisions(signals)
        
        print("✅ Pipeline complete!")
        
        return {
            'unified_dataset': unified,
            'investable_universe': investable,
            'indicators': indicators,
            'signals': signals,
            'decisions': decisions,
            'decisions_summary': decisions_summary,
            'reports': self.reports,
        }
    
    def get_pipeline_status(self) -> dict:
        """
        Get current pipeline execution status.
        
        Returns:
            dict with status of each stage
        """
        status = {}
        
        files = {
            'market_data_raw': 'Market data ingested',
            'index_composition': 'Index composition loaded',
            'unified_dataset': 'Quality filter applied',
            'investable_universe': 'Dynamic filter applied',
            'indicators': 'Indicators computed',
            'signals': 'Signals & scores computed',
            'decisions': 'Decisions generated',
            'decisions_summary': 'Summary ready',
        }
        
        for key, desc in files.items():
            path = self.data_dir / f'{key}.parquet'
            status[key] = {
                'description': desc,
                'exists': path.exists(),
                'path': str(path) if path.exists() else None,
            }
        
        return status
