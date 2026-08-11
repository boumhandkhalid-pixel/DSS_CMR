# DSS Pipeline — Quick Start Guide 🚀

## Prerequisites

```bash
cd /home/yass/Desktop/DSS_CMR
source .venv/bin/activate
```

## Start the Application

```bash
streamlit run ui/app.py
```

The UI will open in your browser at `http://localhost:8501`

---

## Step-by-Step Workflow

### 1. Upload Market Data 📊

1. Click **"Market Data"** in the sidebar
2. Click **"Browse files"** and select your Excel file
   - Example: `Données Marché Boursier_Projet_IA.xlsx`
3. Click **"🔄 Parse & Convert to Parquet"**
4. Review the ingestion report:
   - Sheets included/excluded
   - Data quality checks
   - Preview table
5. ✅ Confirmation: `Excel converted to Parquet: data/market_data_raw.parquet`

---

### 2. Upload Index Composition 🏢

1. Click **"Index Composition"** in the sidebar
2. Click **"Browse files"** and select your Excel file
   - Example: `Compo_All_Indices_20260731.xlsx`
3. Click **"🔄 Parse & Convert to Parquet"**
4. Review the composition:
   - Number of securities
   - Summary statistics (FF, FF Market Cap)
   - Top 10 by weight
5. ✅ Confirmation: `Excel converted to Parquet: data/index_composition.parquet`

---

### 3. Run Complete Pipeline 🔧

After both files are uploaded:

1. Look for the green success message:
   > ✅ Both market data and index composition are ready!

2. Click the large **"🚀 Run Complete Pipeline"** button

3. Wait for processing (typically 5-30 seconds):
   ```
   🔄 Running DSS Pipeline...
     1/5 Applying quality filter...
     2/5 Applying dynamic investability filter...
     3/5 Computing technical indicators...
     4/5 Computing signals and scores...
     5/5 Generating investment decisions...
   ✅ Pipeline complete!
   ```

4. Review the summary metrics:
   - **BUY** signals
   - **HOLD** signals
   - **SELL** signals
   - **Insufficient Data**

---

### 4. View Recommendations 📋

1. Click **"Recommendations"** in the sidebar

2. Review the decision table:
   - Color-coded decisions (green=BUY, yellow=HOLD, red=SELL)
   - Overall Score (0-100)
   - Confidence (0-100%)
   - Latest price
   - Signals summary

3. **Filter recommendations** (optional):
   - Click "🔍 Filter Recommendations"
   - Select decision types (BUY, SELL, etc.)
   - Set minimum confidence %
   - Set minimum score
   - Click "Apply Filters"

4. **View evidence panel**:
   - Select a company from the dropdown
   - See detailed signals (EMA_20↑, RSI_14↓, etc.)
   - View data coverage percentage
   - Check latest date and price

---

### 5. Export Decisions 📥

Three export formats available:

1. **CSV** → Spreadsheet-compatible
2. **JSON** → API-compatible
3. **Parquet** → For data science tools

Click any export button to download immediately.

---

## Understanding the Output

### Decision Types

| Decision | Meaning | Criteria |
|---|---|---|
| **BUY** | Strong bullish signal | Score ≥60 AND Confidence ≥60% |
| **HOLD** | Neutral or uncertain | Score between 40-60 OR Confidence <60% |
| **SELL** | Strong bearish signal | Score ≤40 AND Confidence ≥60% |
| **INSUFFICIENT_DATA** | Not enough data | Data coverage <50% |

### Scores Explained

**Overall Score (0-100)**
- **0-40**: Bearish (sell signal)
- **40-60**: Neutral (hold)
- **60-100**: Bullish (buy signal)

**Confidence (0-100%)**
- **0-50%**: Low confidence (sparse data, families disagree, high volatility)
- **50-70%**: Moderate confidence
- **70-100%**: High confidence (complete data, families agree, stable volatility)

### Signal Arrows

- **↑** Bullish signal
- **↓** Bearish signal
- **=** Neutral signal

---

## Sample Data Results

With the provided sample data (28 sessions, 5 companies):

**Expected output:**
```
BUY                    0
HOLD                   3
SELL                   0
INSUFFICIENT_DATA    137
```

**Why mostly INSUFFICIENT_DATA?**
- Sample has only 14 consecutive Cours per company
- Many indicators need 20-50 observations
- Confidence scores remain low

**In production with 6+ months:**
- Most indicators will be VALID
- Confidence scores 60-90%
- BUY/SELL decisions will trigger appropriately

---

## Troubleshooting

### "Pipeline not ready" error
- Make sure you uploaded **both** market data and index composition
- Check that both files parsed successfully (green checkmarks)

### "INSUFFICIENT_DATA" for all companies
- Normal with sample data (only 14-28 sessions)
- Need 6-12 months of daily data for meaningful decisions

### Excel file not recognized
- File must be `.xlsx` format
- Old `.xls` format not supported
- CSV files not supported (must be Excel)

### Processing takes too long
- For large files (1+ years of data), processing may take 1-2 minutes
- Don't refresh the page while "Running DSS Pipeline..." is displayed

---

## File Locations

All generated files are in `data/`:

```
data/
├── market_data_raw.parquet          ← Market data (after upload)
├── index_composition.parquet        ← Composition (after upload)
├── unified_dataset.parquet          ← After quality filter
├── investable_universe.parquet      ← After dynamic filter
├── indicators.parquet               ← With 10 indicators
├── signals.parquet                  ← With signals & scores
├── decisions.parquet                ← Full decision history
└── decisions_summary.parquet        ← One row per company
```

These files can be:
- Opened in Python/Pandas
- Imported into data science tools
- Used for further analysis

---

## Next Steps

### Today:
1. ✅ Upload sample data
2. ✅ Run pipeline
3. ✅ Review recommendations
4. ✅ Export decisions

### Tomorrow:
1. 📊 Implement Notebook 12 (Historical Backtesting)
2. 🔬 Validate weights & thresholds
3. ✅ Update methodology status to "VALIDATED"

---

## Important Warnings

⚠️ **Current Status**

The pipeline uses **BASELINE_HYPOTHESIS** weights and thresholds:
- **Code validated** ✅ (all notebooks pass)
- **Methodology NOT validated** ❌ (requires backtesting)

**Do NOT use these decisions for actual trading until:**
1. Notebook 12 (Historical Backtesting) is complete
2. Results show positive risk-adjusted returns
3. WEIGHTS_STATUS and THRESHOLDS_STATUS updated to "VALIDATED"

---

## Support

For issues or questions:
1. Check `MIGRATION_COMPLETE.md` for technical details
2. Review `DECISION_ENGINE_PHILOSOPHY.md` for methodology
3. Check notebooks 09-11 for implementation details

---

## Quick Test (Without UI)

```python
from src.pipeline import DSS_Pipeline

pipeline = DSS_Pipeline()

# Ingest data
market_df, _ = pipeline.ingest_market_data('data/Données Marché Boursier_Projet_IA.xlsx')
comp_df, _ = pipeline.ingest_index_composition('data/Compo_All_Indices_20260731.xlsx')

# Run pipeline
results = pipeline.run_pipeline(market_df, comp_df)

# View summary
print(results['decisions_summary'])
```

---

**🎉 You're ready to use the DSS Pipeline!**
