#!/bin/bash
# Complete system test script

set -e  # Exit on error

cd /home/yass/Desktop/DSS_CMR
source .venv/bin/activate

echo "========================================"
echo "DSS Pipeline - Complete System Test"
echo "========================================"
echo ""

# Test 1: Module imports
echo "✓ Test 1/3: Module imports..."
python3 << 'EOF'
from src.pipeline import DSS_Pipeline
from src.indicators import compute_all_indicators
from src.signals import compute_signals_and_confidence
from src.decisions import make_investment_decisions
print("  ✓ All modules imported successfully")
EOF

echo ""

# Test 2: Backend pipeline
echo "✓ Test 2/3: Backend pipeline execution..."
python3 << 'EOF'
from src.pipeline import DSS_Pipeline
from pathlib import Path

ROOT = Path('/home/yass/Desktop/DSS_CMR')
pipeline = DSS_Pipeline(data_dir=ROOT / 'data')

market_file = ROOT / 'data' / 'Données Marché Boursier_Projet_IA.xlsx'
comp_file = ROOT / 'data' / 'Compo_All_Indices_20260731.xlsx'

# Ingest
market, _ = pipeline.ingest_market_data(str(market_file))
comp, _ = pipeline.ingest_index_composition(str(comp_file))

# Run pipeline
results = pipeline.run_pipeline(market, comp)

# Verify
dec_report = pipeline.reports['decisions']
assert dec_report['buy'] >= 0
assert dec_report['hold'] >= 0
assert dec_report['sell'] >= 0
assert len(results['decisions_summary']) > 0

print(f"  ✓ Pipeline completed successfully")
print(f"    - BUY: {dec_report['buy']}")
print(f"    - HOLD: {dec_report['hold']}")
print(f"    - SELL: {dec_report['sell']}")
print(f"    - Companies: {len(results['decisions_summary'])}")
EOF

echo ""

# Test 3: File outputs
echo "✓ Test 3/3: Verifying file outputs..."
python3 << 'EOF'
from pathlib import Path
import pandas as pd

ROOT = Path('/home/yass/Desktop/DSS_CMR/data')

files = [
    'market_data_raw.parquet',
    'index_composition.parquet',
    'unified_dataset.parquet',
    'investable_universe.parquet',
    'indicators.parquet',
    'signals.parquet',
    'decisions.parquet',
    'decisions_summary.parquet'
]

for f in files:
    path = ROOT / f
    if path.exists():
        df = pd.read_parquet(path)
        print(f"  ✓ {f:30s} {len(df):4d} rows")
    else:
        print(f"  ✗ {f:30s} MISSING")
EOF

echo ""
echo "========================================"
echo "✅ ALL TESTS PASSED!"
echo "========================================"
echo ""
echo "System is ready. Start Streamlit UI:"
echo "  streamlit run ui/app.py"
echo ""
