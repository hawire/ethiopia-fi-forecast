from pathlib import Path

import pandas as pd
from pathlib import Path


def _read_csv(path, parse_dates=None, numeric_cols=None):
    """Read a CSV file with optional parsing and numeric conversion."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f'CSV file not found: {path}')
    df = pd.read_csv(path)
    if parse_dates:
        for column in parse_dates:
            if column in df.columns:
                df[column] = pd.to_datetime(df[column], errors='coerce')
    if numeric_cols:
        for column in numeric_cols:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors='coerce')
    return df


def load_unified_data(raw_dir=None):
    """Load the base unified data file from the raw directory."""
    raw_dir = Path(raw_dir or Path(__file__).resolve().parents[1] / 'data' / 'raw')
    path = raw_dir / 'ethiopia_fi_unified_data.csv'
    return _read_csv(path, parse_dates=['observation_date'], numeric_cols=['value_numeric'])


def load_reference_codes(raw_dir=None):
    """Load reference codes from the raw directory."""
    raw_dir = Path(raw_dir or Path(__file__).resolve().parents[1] / 'data' / 'raw')
    path = raw_dir / 'reference_codes.csv'
    return _read_csv(path)


def load_enriched_data(processed_dir=None):
    """Load the enriched processed dataset for analysis."""
    processed_dir = Path(processed_dir or Path(__file__).resolve().parents[1] / 'data' / 'processed')
    path = processed_dir / 'ethiopia_fi_unified_data_enriched.csv'
    return _read_csv(path, parse_dates=['observation_date'], numeric_cols=['value_numeric'])


def load_enrichment_log(root_dir=None):
    """Load the data enrichment log markdown file content."""
    root_dir = Path(root_dir or Path(__file__).resolve().parents[1] / 'data')
    path = root_dir / 'data_enrichment_log.md'
    if not path.exists():
        raise FileNotFoundError(f'Enrichment log not found: {path}')
    return path.read_text()
