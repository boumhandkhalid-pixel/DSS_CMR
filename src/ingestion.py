from pathlib import Path
import pandas as pd
from typing import List

from src.parsers.parser_factory import get_parser_for_sheet
from src.normalization.normalizer import merge_long_tables


def ingest_workbook(path: str) -> pd.DataFrame:
    """Ingest Excel workbook and return unified normalized DataFrame.

    This function reads every sheet, selects the appropriate parser and merges results.
    """
    pathp = Path(path)
    xls = pd.ExcelFile(pathp)
    long_tables: List[pd.DataFrame] = []

    for sheet in xls.sheet_names:
        # load sheet quickly to let factory detect family
        df = pd.read_excel(pathp, sheet_name=sheet, nrows=20, header=None)
        parser = get_parser_for_sheet(df)
        try:
            parsed = parser(pathp, sheet)
            long_tables.append(parsed)
            print(f'Parsed sheet {sheet} -> {len(parsed)} rows')
        except Exception as e:
            print(f'Warning: failed to parse sheet {sheet}: {e}')

    unified = merge_long_tables(long_tables)
    return unified


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python -m src.ingestion <workbook.xlsx>')
        sys.exit(1)
    df = ingest_workbook(sys.argv[1])
    out = Path('data/processed/unified_sample.parquet')
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out)
    print('Wrote', out)
