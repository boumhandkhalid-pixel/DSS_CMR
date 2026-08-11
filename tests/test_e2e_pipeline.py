"""End-to-end integration tests for the complete DSS pipeline."""

import sys
from pathlib import Path
import pandas as pd
import pytest

# Add src to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.ingestion import ingest_workbook
from src.validation import validate_dataset


class TestEndToEndPipeline:
    """End-to-end tests for parse → normalize → validate pipeline."""
    
    @pytest.fixture
    def sample_workbook(self):
        """Path to sample workbook."""
        return ROOT / 'samples' / 'Données Marché Boursier_Projet_IA_copy.xlsx'
    
    @pytest.fixture
    def required_variables(self):
        """Required variables for market dataset."""
        return {'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
    
    def test_ingestion_produces_dataframe(self, sample_workbook, required_variables):
        """Test that ingestion returns a DataFrame."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        
        assert isinstance(unified, pd.DataFrame), "Ingestion should return a DataFrame"
        assert len(unified) > 0, "Unified dataset should not be empty"
    
    def test_ingestion_report_completeness(self, sample_workbook, required_variables):
        """Test that ingestion report contains all required fields."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        
        required_keys = {
            'total_sheets', 'sheets_included', 'sheets_excluded',
            'unified_records', 'unified_companies', 'unified_sessions', 'unified_variables'
        }
        
        assert all(k in report for k in required_keys), f"Report missing keys: {required_keys - set(report.keys())}"
        assert report['total_sheets'] > 0, "Should detect sheets"
        assert len(report['sheets_included']) > 0, "Should include market sheets"
    
    def test_parser_detects_family_a_sheets(self, sample_workbook, required_variables):
        """Test that parser correctly identifies Family A sheets."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        
        # Should include all 5 market sheets
        included_names = [s['canonical_variable'] for s in report['sheets_included']]
        
        assert 'Cours' in included_names, "Cours sheet should be included"
        assert 'Bid' in included_names, "Bid sheet should be included"
        assert 'Ask' in included_names, "Ask sheet should be included"
        assert 'Volume MC' in included_names, "Volume MC sheet should be included"
        assert 'Quantité MC' in included_names, "Quantité MC sheet should be included"
    
    def test_parser_excludes_family_b_sheets(self, sample_workbook, required_variables):
        """Test that parser correctly excludes Family B sheets."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        
        excluded_names = [s['name'] for s in report['sheets_excluded']]
        
        assert 'Data' in excluded_names, "Data (Family B) sheet should be excluded"
    
    def test_normalization_grain_correctness(self, sample_workbook, required_variables):
        """Test that normalized dataset has correct grain (Date × CODE_ISIN)."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        
        grain = ['Date', 'CODE_ISIN']
        total_rows = len(unified)
        unique_grain = len(unified[grain].drop_duplicates())
        
        assert total_rows == unique_grain, f"Grain violation: {total_rows} rows vs {unique_grain} unique combinations"
    
    def test_normalization_produces_wide_format(self, sample_workbook, required_variables):
        """Test that normalized dataset has expected columns."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        
        required_cols = {'Date', 'CODE_ISIN', 'Company', 'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
        actual_cols = set(unified.columns)
        
        assert required_cols.issubset(actual_cols), f"Missing columns: {required_cols - actual_cols}"
    
    def test_validation_passes_for_valid_dataset(self, sample_workbook, required_variables):
        """Test that validation passes (no critical issues) for valid dataset."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        all_passed, validation_report = validate_dataset(unified)
        
        assert validation_report['critical'] == 0, f"Should have no critical issues, got {validation_report['critical']}"
    
    def test_validation_identifies_all_checks(self, sample_workbook, required_variables):
        """Test that validation runs all check categories."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        all_passed, validation_report = validate_dataset(unified)
        
        required_categories = {
            'Schema', 'Grain', 'Identifiers', 'Dates', 'Prices', 'Volumes', 'Consistency'
        }
        
        actual_categories = set(validation_report['by_category'].keys())
        assert required_categories == actual_categories, f"Missing validation categories: {required_categories - actual_categories}"
    
    def test_unified_dataset_has_expected_size(self, sample_workbook, required_variables):
        """Test that unified dataset has expected dimensions."""
        unified, report = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        
        # Sample has 7 companies and 14 sessions
        # 5 sheets with varying data coverage
        # Expecting ~182 records (7 companies × 28 date-company combinations)
        
        assert len(unified) >= 100, f"Dataset too small: {len(unified)} rows"
        assert unified['CODE_ISIN'].nunique() == 7, "Should have 7 unique companies"
        assert unified['Date'].nunique() >= 10, "Should have at least 10 unique dates"
    
    def test_roundtrip_consistency(self, sample_workbook, required_variables):
        """Test that data survives ingestion → validation roundtrip consistently."""
        # First pass
        unified1, report1 = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        all_passed1, validation1 = validate_dataset(unified1)
        
        # Second pass (should be identical)
        unified2, report2 = ingest_workbook(str(sample_workbook), required_variables=required_variables)
        all_passed2, validation2 = validate_dataset(unified2)
        
        assert len(unified1) == len(unified2), "Roundtrip produced different row counts"
        assert report1['unified_records'] == report2['unified_records'], "Roundtrip produced different record counts"
        assert validation1['critical'] == validation2['critical'], "Roundtrip produced different validation results"


class TestRobustParserVariations:
    """Test parser robustness with sheet name variations."""
    
    @pytest.fixture
    def messy_workbook(self):
        """Create temporary workbook with messy sheet names."""
        import tempfile
        from openpyxl import Workbook
        
        source_path = ROOT / 'samples' / 'Données Marché Boursier_Projet_IA_copy.xlsx'
        source_xl = pd.ExcelFile(source_path, engine='openpyxl')
        
        # Create new workbook with renamed sheets
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
                sheet_renames = {
                    'Cours': 'cours',
                    'Bid': 'BID',
                    'Ask': 'offre',
                    'Volume MC': 'volume',
                    'Quantité MC': 'QUANTITE_MC'
                }
                
                for old_name, new_name in sheet_renames.items():
                    if old_name in source_xl.sheet_names:
                        df = pd.read_excel(source_path, sheet_name=old_name, header=None)
                        df.to_excel(writer, sheet_name=new_name, index=False, header=False)
            
            temp_path = tmp.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_parser_handles_lowercase_names(self, messy_workbook):
        """Test that parser correctly normalizes lowercase sheet names."""
        required_vars = {'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
        unified, report = ingest_workbook(messy_workbook, required_variables=required_vars)
        
        canonical_vars = set(report['unified_variables'])
        expected_vars = required_vars
        
        assert canonical_vars == expected_vars, f"Variables mismatch: got {canonical_vars}, expected {expected_vars}"
    
    def test_parser_handles_uppercase_names(self, messy_workbook):
        """Test that parser correctly normalizes uppercase sheet names."""
        required_vars = {'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
        unified, report = ingest_workbook(messy_workbook, required_variables=required_vars)
        
        assert len(report['sheets_included']) == 5, "Should include all 5 market sheets despite messy names"
    
    def test_parser_handles_french_alternatives(self, messy_workbook):
        """Test that parser recognizes French alternative terms."""
        required_vars = {'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
        unified, report = ingest_workbook(messy_workbook, required_variables=required_vars)
        
        # 'offre' should be normalized to 'Ask'
        canonical_vars = [s['canonical_variable'] for s in report['sheets_included']]
        assert 'Ask' in canonical_vars, "French 'offre' should be normalized to 'Ask'"


class TestDataQualityValidation:
    """Test data quality validation functionality."""
    
    @pytest.fixture
    def valid_dataset(self):
        """Load valid dataset."""
        sample_path = ROOT / 'samples' / 'Données Marché Boursier_Projet_IA_copy.xlsx'
        required_vars = {'Cours', 'Bid', 'Ask', 'Volume MC', 'Quantité MC'}
        unified, _ = ingest_workbook(str(sample_path), required_variables=required_vars)
        return unified
    
    def test_validation_detects_null_dates(self, valid_dataset):
        """Test that validation detects null dates."""
        # Create corrupted dataset
        corrupted = valid_dataset.copy()
        corrupted.loc[0, 'Date'] = pd.NaT
        
        all_passed, report = validate_dataset(corrupted)
        
        # Should have critical issues
        critical_tests = [r for r in report['results'] if r.severity == 'critical' and not r.passed]
        assert len(critical_tests) > 0, "Validation should detect null dates"
    
    def test_validation_detects_duplicate_grain(self, valid_dataset):
        """Test that validation detects duplicate (Date, CODE_ISIN) combinations."""
        # Create dataset with duplicates
        corrupted = pd.concat([valid_dataset, valid_dataset.iloc[0:1]])
        
        all_passed, report = validate_dataset(corrupted)
        
        # Should have critical issues
        critical_tests = [r for r in report['results'] if r.severity == 'critical' and not r.passed]
        assert len(critical_tests) > 0, "Validation should detect grain duplicates"
    
    def test_validation_warns_on_high_null_percentage(self, valid_dataset):
        """Test that validation warns on high null percentage."""
        # Create dataset with many nulls
        corrupted = valid_dataset.copy()
        corrupted.loc[corrupted.index[:-10], 'Cours'] = pd.NA
        
        all_passed, report = validate_dataset(corrupted)
        
        # Should have warnings
        warnings = [r for r in report['results'] if r.severity == 'warning' and not r.passed]
        assert len(warnings) > 0, "Validation should warn on high null percentage"
    
    def test_validation_checks_bid_ask_relationship(self, valid_dataset):
        """Test that validation checks Bid <= Ask."""
        # Create dataset with inverted bid/ask
        corrupted = valid_dataset.copy()
        mask = (corrupted['Bid'].notna()) & (corrupted['Ask'].notna())
        corrupted.loc[mask, 'Bid'] = 999999
        
        all_passed, report = validate_dataset(corrupted)
        
        # Should have warnings about inverted spreads
        spread_warnings = [r for r in report['results'] if 'Bid-Ask' in r.name and not r.passed]
        assert len(spread_warnings) > 0, "Validation should warn on inverted bid-ask spread"


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == '__main__':
    run_tests()
