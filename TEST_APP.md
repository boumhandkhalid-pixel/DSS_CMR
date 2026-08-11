# Streamlit App Testing Guide

## Issue Fixed ✅

**Problem:** "File is not a zip file" error when uploading Excel files

**Root Cause:** 
- Original data file was corrupted
- Pandas wasn't using explicit openpyxl engine
- File upload used `.getbuffer()` instead of `.getvalue()`

**Solution:**
1. ✅ Fixed file upload to use `.getvalue()` instead of `.getbuffer()`
2. ✅ Added explicit `engine='openpyxl'` to all Excel operations
3. ✅ Replaced corrupted file with working copy from samples/
4. ✅ Added proper error handling and temp file cleanup
5. ✅ Added `st.rerun()` after successful processing

---

## Start the App

```bash
cd /home/yass/Desktop/DSS_CMR
source .venv/bin/activate
streamlit run ui/app.py
```

The app will open at: `http://localhost:8501`

---

## Testing Workflow

### 1. Test Market Data Upload ✅

1. Go to **"Market Data"** page
2. Click "Browse files"
3. Upload: `data/Données Marché Boursier_Projet_IA.xlsx`
4. Click **"🔄 Parse & Validate"**

**Expected Result:**
```
✅ Excel processed successfully → data/market_data_raw.parquet

Metrics:
- Sheets Included: 5
- Total Records: 182
- Companies: 7
- Sessions: 28
- Variables: 5
```

### 2. Test Index Composition Upload ✅

1. Go to **"Index Composition"** page
2. Click "Browse files"
3. Upload: `data/Compo_All_Indices_20260731.xlsx`
4. Click **"🔄 Parse & Validate"**

**Expected Result:**
```
✅ Excel processed successfully → data/index_composition.parquet

Metrics:
- Index: MASI
- Total Securities: 79
- Columns: 8
```

### 3. Test Complete Pipeline ✅

After both files are uploaded:

1. Look for green message: "✅ Both market data and index composition are ready!"
2. Click **"🚀 Run Complete Pipeline"** (large primary button)

**Expected Result:**
```
✅ Pipeline complete! Go to Recommendations page to view decisions.

Decisions: BUY=0, HOLD=3, SELL=0, INSUFFICIENT_DATA=137
```

### 4. Test Recommendations View ✅

1. Go to **"Recommendations"** page
2. Review the decisions table
3. Test filters
4. Test exports (CSV/JSON/Parquet)
5. View evidence panel

**Expected Result:**
- Table with 5 companies
- 3 HOLD decisions
- 137 INSUFFICIENT_DATA (expected with sample data)
- Color-coded decisions
- Working filters and exports

---

## Expected Output (Sample Data)

### Decisions Distribution
```
BUY:               0  ← Need 60+ score AND 60+ confidence
HOLD:              3  ← Default for unclear signals
SELL:              0  ← Need <40 score AND 60+ confidence
INSUFFICIENT_DATA: 137 ← Only 14 Cours per company
```

### Companies with Decisions
```
Company             Decision          Score  Confidence  Coverage
ALUMINIUM DU MAROC  HOLD               30.6     56.2%       57%
AGMA                INSUFFICIENT_DATA   N/A     20.0%        0%
AFRIQUIA GAZ        INSUFFICIENT_DATA   N/A     20.0%        0%
ALLIANCES           HOLD               44.4     69.5%       57%
AFMA                HOLD               30.6     56.2%       57%
```

**Why mostly INSUFFICIENT_DATA?**
- Sample has only 14 consecutive Cours per company
- Most indicators need 20-50 observations
- Confidence scores remain low (<60%)

**In production with 6-12 months of data:**
- Most indicators will be VALID
- Confidence scores 60-90%
- BUY/SELL decisions will trigger

---

## Testing Checklist

### Market Data Page
- [ ] File upload works
- [ ] Excel → Parquet conversion succeeds
- [ ] Ingestion report displays correctly
- [ ] Data quality checks show
- [ ] Preview table populates
- [ ] Summary statistics accurate

### Index Composition Page
- [ ] File upload works
- [ ] Composition parses correctly
- [ ] Top 10 by weight displays
- [ ] Summary statistics show
- [ ] "Run Pipeline" button appears after both uploads

### Pipeline Execution
- [ ] "Run Pipeline" button visible
- [ ] Processing spinner shows
- [ ] All 5 stages complete
- [ ] Success message displays
- [ ] Decision metrics show

### Recommendations Page
- [ ] Decisions table populates
- [ ] Color coding works (green/yellow/red/gray)
- [ ] Filters work correctly
- [ ] Evidence panel shows details
- [ ] CSV export downloads
- [ ] JSON export downloads
- [ ] Parquet export downloads
- [ ] Methodology warning displays

---

## Troubleshooting

### "File is not a zip file" Error

**If this still occurs:**

1. Check file integrity:
   ```bash
   file data/Données*.xlsx
   # Should show: Microsoft Excel 2007+
   ```

2. Try with sample file:
   ```bash
   cp samples/"Données Marché Boursier_Projet_IA_copy.xlsx" data/"test.xlsx"
   # Upload test.xlsx instead
   ```

3. Check pandas/openpyxl:
   ```bash
   pip list | grep -E "pandas|openpyxl"
   ```

### Page Doesn't Update

- Click browser refresh (Ctrl+R)
- Or use Streamlit menu: ⋮ → "Rerun"

### Pipeline Stuck

- Check terminal for error messages
- Stop with Ctrl+C
- Restart: `streamlit run ui/app.py`

### No Decisions Showing

- Verify both files uploaded successfully
- Check pipeline ran (green success message)
- Go to Recommendations page
- Refresh if needed

---

## File Locations After Test

```
data/
├── Données Marché Boursier_Projet_IA.xlsx  (uploaded)
├── Compo_All_Indices_20260731.xlsx          (uploaded)
├── market_data_raw.parquet                  (auto-generated)
├── index_composition.parquet                (auto-generated)
├── unified_dataset.parquet                  (pipeline stage 1)
├── investable_universe.parquet              (pipeline stage 2)
├── indicators.parquet                       (pipeline stage 3)
├── signals.parquet                          (pipeline stage 4)
├── decisions.parquet                        (pipeline stage 5)
└── decisions_summary.parquet                (pipeline stage 5)
```

All files can be opened in Python for further analysis.

---

## Performance Notes

### Expected Processing Times
- Market data ingestion: 2-5 seconds
- Index composition: <1 second
- Complete pipeline: 5-15 seconds
- Export operations: <1 second

### File Sizes
- Market data (sample): ~32 KB Excel → ~15 KB Parquet
- Index composition: ~35 KB Excel → ~10 KB Parquet
- Final decisions: ~20 KB Parquet

**Parquet is 50-70% smaller than Excel!**

---

## Success Criteria

✅ Market data uploads without errors  
✅ Index composition uploads without errors  
✅ Pipeline completes all 5 stages  
✅ Decisions table displays  
✅ Filters work  
✅ Exports download  
✅ No Python errors in terminal  

**If all checked → System is production-ready!**

---

## Next Steps After Testing

1. ✅ Verify app works end-to-end
2. 📊 Upload production data (6-12 months)
3. 🔬 Implement Notebook 12 (Backtesting)
4. ✅ Validate methodology
5. 🚀 Deploy to production

---

## Quick Test Command

```bash
# Full integration test (no UI)
cd /home/yass/Desktop/DSS_CMR
source .venv/bin/activate

python3 << 'EOF'
from src.pipeline import DSS_Pipeline

pipeline = DSS_Pipeline()
market, _ = pipeline.ingest_market_data('data/Données Marché Boursier_Projet_IA.xlsx')
comp, _ = pipeline.ingest_index_composition('data/Compo_All_Indices_20260731.xlsx')
results = pipeline.run_pipeline(market, comp)

print("✅ Pipeline test passed!")
print(f"Decisions: {pipeline.reports['decisions']}")
print(results['decisions_summary'][['Company', 'Decision', 'Confidence']])
EOF
```

This should complete in <30 seconds with no errors.
