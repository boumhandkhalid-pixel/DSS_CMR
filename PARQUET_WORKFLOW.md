# Parquet Workflow — Unified Dataset Persistence

## Overview

The project now uses **Parquet** as the persistent storage format for the unified dataset after filtering. This creates a clean separation between raw data ingestion and downstream analysis.

## Architecture

```
┌──────────────────────┐
│  BVC Excel Workbook  │  (Raw Input)
│  Multiple sheets     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    Python/Pandas     │  (Parsing + Cleaning)
│    Ingestion Logic   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Unified Dataset      │  (In-Memory DataFrame)
│ 182 rows, 8 columns  │  Before filtering
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Data Validation      │  (Quality checks)
│ (Notebook 06)        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Data Filtering       │  (Remove bad companies)
│ (Notebook 05)        │  Removes AKDITAL
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ Parquet File: data/unified_dataset.parquet│  ◄── NEW
│ 168 rows, 8 columns                       │  Persistent storage
│ Compressed, Schema-preserved              │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴──────┬──────────────┬──────────────┐
    │             │              │              │
    ▼             ▼              ▼              ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│Metrics │  │Filters │  │Technical│  │Business│
│ (07)   │  │ (08)   │  │Indicator│  │ Rules  │
│        │  │        │  │  (09)  │  │ (10)   │
└────────┘  └────────┘  └────────┘  └────────┘
    │             │              │              │
    └──────┬──────┴──────────────┴──────────────┘
           │
           ▼
┌──────────────────────┐
│ Decision Engine      │  BUY / HOLD / SELL
│ (Notebook 11)        │  + Confidence Score
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Streamlit UI        │  Results Display
└──────────────────────┘
```

## Why Parquet?

### ✓ Advantages

1. **Columnar Format**
   - Fast queries on specific columns
   - Better compression
   - Efficient for analytical workloads

2. **Schema Preservation**
   - Automatic type inference
   - No need to redefine column types
   - Type safety guarantees

3. **Compression**
   - Snappy: Fast compression, ~50% reduction
   - Gzip: Better compression, slightly slower
   - Much smaller than CSV (0.01 MB vs CSV would be ~0.05 MB)

4. **Interoperability**
   - Readable by multiple languages (Python, R, Julia, Scala)
   - Standard format for data exchange
   - Industry standard for data pipelines

5. **Performance**
   - Faster read than CSV
   - Lazy loading capabilities
   - Efficient memory usage

## Files Involved

### New Parquet Location
```
project/
├── data/
│   └── unified_dataset.parquet    ◄── Persistent storage (NEW)
├── notebooks/
│   ├── 05_data_filtering.ipynb    ◄── Updated: Saves to Parquet
│   ├── 07_market_metrics.ipynb    ◄── Load from Parquet (optional)
│   ├── 08_dynamic_filters.ipynb   ◄── Load from Parquet (optional)
│   └── 09_technical_indicators.ipynb ◄── Load from Parquet (optional)
└── src/
    └── validation.py              ◄── Updated: Parquet functions
```

## API Reference

### Save to Parquet

```python
from src.validation import save_unified_dataset

save_report = save_unified_dataset(
    df=unified_filtered_dataset,
    output_path='data/unified_dataset.parquet',
    compression='snappy'  # or 'gzip', 'brotli', 'lz4', 'zstd'
)

# Returns:
{
    'success': True,
    'path': 'data/unified_dataset.parquet',
    'file_size_bytes': 15234,
    'file_size_mb': 0.01,
    'rows': 168,
    'columns': 8,
    'compression': 'snappy',
    'error': None
}
```

### Load from Parquet

```python
from src.validation import load_unified_dataset

df, load_report = load_unified_dataset('data/unified_dataset.parquet')

# Returns:
{
    'success': True,
    'path': 'data/unified_dataset.parquet',
    'rows': 168,
    'columns': 8,
    'columns_list': ['Date', 'CODE_ISIN', 'Company', 'Ask', 'Bid', 'Cours', 'Quantité MC', 'Volume MC'],
    'dtypes': {
        'Date': 'datetime64[ns]',
        'CODE_ISIN': 'object',
        'Company': 'object',
        'Ask': 'float64',
        'Bid': 'float64',
        'Cours': 'float64',
        'Quantité MC': 'float64',
        'Volume MC': 'float64'
    },
    'error': None
}
```

## Workflow by Notebook

### Notebook 05: Data Filtering (Source)
```python
# Step 1: Load from Excel
unified, _ = ingest_workbook(wb_path)

# Step 2: Filter
unified_filtered, removal_report = filter_companies_by_usable_data(unified)

# Step 3: Save to Parquet
save_report = save_unified_dataset(unified_filtered, 'data/unified_dataset.parquet')

# Step 4: Verify by loading
df_loaded, load_report = load_unified_dataset('data/unified_dataset.parquet')
```

### Notebooks 07, 08, 09 (Consumers)
```python
# Option A: Direct from Excel (original way)
from src.ingestion import ingest_workbook
from src.validation import filter_companies_by_usable_data

unified, _ = ingest_workbook(wb_path, required_variables=vars)
unified_filtered, _ = filter_companies_by_usable_data(unified)
# ... use unified_filtered


# Option B: Load from Parquet (new, faster)
from src.validation import load_unified_dataset

unified_filtered, load_report = load_unified_dataset('data/unified_dataset.parquet')
# ... use unified_filtered
```

## Current File Status

```
data/
└── unified_dataset.parquet
    Size:       0.01 MB
    Rows:       168 (6 companies, 28 sessions)
    Columns:    8 (Date, CODE_ISIN, Company, Ask, Bid, Cours, Quantité MC, Volume MC)
    Compression: Snappy
    Status:     ✓ Verified (save + load test passed)
```

## Data Integrity

After save/load cycle:
- ✓ Shape matches: (168, 8)
- ✓ Content matches: Byte-for-byte identical
- ✓ Companies match: All 6 companies present
- ✓ Date ranges match: 2018-12-31 to 2024-01-19
- ✓ Data types preserved: All columns maintain original types

## Usage Recommendations

### When to Use Excel Ingestion (Current)
- First time ingesting raw workbook
- Need to apply validation checks
- Need detailed ingestion report
- Excel workbook structure changes

### When to Use Parquet (New)
- Repeated analysis runs
- Multiple notebooks accessing same data
- Performance-sensitive workloads
- Data exchange with other teams/languages

## Compression Options

```
Format     Speed   Compression   Typical Use
─────────────────────────────────────────────
snappy     Fast    ~50%          Default (balanced)
gzip       Slow    ~70%          Long-term storage
brotli     Fast    ~65%          Modern systems
lz4        Fastest ~30%          Real-time workloads
zstd       Fast    ~75%          High compression
```

**Current Setting:** Snappy (default, good balance)

## Future Enhancements

1. **Partitioning:** Partition by DATE or CODE_ISIN for faster queries
2. **Statistics:** Enable column statistics for query optimization
3. **Schema Evolution:** Handle schema changes in future data
4. **Incremental Writes:** Append new data without rewriting entire file
5. **Data Catalog:** Metadata tracking for versioning

## Troubleshooting

### File Not Found
```python
# Solution: Ensure data directory exists
from pathlib import Path
Path('data').mkdir(exist_ok=True)
```

### Corrupted Parquet File
```python
# Solution: Regenerate from source
from src.validation import save_unified_dataset, load_unified_dataset

# Delete: data/unified_dataset.parquet
# Re-run: Notebook 05 (Data Filtering)
```

### Memory Issues with Large Datasets
```python
# Solution: Read in chunks (future enhancement)
import pyarrow.parquet as pq

parquet_file = pq.ParquetFile('data/unified_dataset.parquet')
for batch in parquet_file.iter_batches(batch_size=1000):
    df_chunk = batch.to_pandas()
    # Process chunk
```

## Summary

**Parquet provides:**
- ✓ Efficient persistent storage
- ✓ Schema preservation
- ✓ Type safety
- ✓ Fast loading for downstream analysis
- ✓ Better compression than CSV
- ✓ Industry-standard format

**Implementation status:**
- ✓ Save function: `save_unified_dataset()`
- ✓ Load function: `load_unified_dataset()`
- ✓ Notebook 05: Saves after filtering
- ✓ File created: `data/unified_dataset.parquet`
- ✓ Verified: Save/load test passed

**Ready to use in:**
- Notebooks 07, 08, 09 (optional switch to Parquet)
- Production pipeline (fast data loading)
- Data exchange with other teams
