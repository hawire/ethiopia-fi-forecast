from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'


def _read_csv(path, parse_dates=None, numeric_cols=None):
    """Read a CSV file with optional parsing and numeric conversion."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f'CSV file not found: {path}')
    df = pd.read_csv(path, on_bad_lines='warn')
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
    """Load the base unified data file from the raw directory.

    Falls back to the processed copy of the Excel-export CSV when raw is absent.
    """
    raw_dir = Path(raw_dir or DEFAULT_RAW_DIR)
    path = raw_dir / 'ethiopia_fi_unified_data.csv'
    if not path.exists():
        alt = DEFAULT_PROCESSED_DIR / 'ethiopia_fi_unified_data.xlsx - ethiopia_fi_unified_data.csv'
        if alt.exists():
            return _read_csv(alt, parse_dates=['observation_date'], numeric_cols=['value_numeric'])
        raise FileNotFoundError(f'CSV file not found: {path}')
    return _read_csv(path, parse_dates=['observation_date'], numeric_cols=['value_numeric'])


def load_reference_codes(raw_dir=None):
    """Load reference codes from the raw directory."""
    raw_dir = Path(raw_dir or DEFAULT_RAW_DIR)
    path = raw_dir / 'reference_codes.csv'
    return _read_csv(path)


def load_enriched_data(processed_dir=None):
    """Load the enriched processed dataset for analysis."""
    processed_dir = Path(processed_dir or DEFAULT_PROCESSED_DIR)
    path = processed_dir / 'ethiopia_fi_unified_data_enriched.csv'
    return _read_csv(path, parse_dates=['observation_date'], numeric_cols=['value_numeric'])


def load_enrichment_log(root_dir=None):
    """Load the data enrichment log markdown file content."""
    root_dir = Path(root_dir or PROJECT_ROOT / 'data')
    path = root_dir / 'data_enrichment_log.md'
    if not path.exists():
        raise FileNotFoundError(f'Enrichment log not found: {path}')
    return path.read_text(encoding='utf-8')


def load_forecast_results(processed_dir=None):
    """Load saved access/usage scenario forecasts if present."""
    processed_dir = Path(processed_dir or DEFAULT_PROCESSED_DIR)
    path = processed_dir / 'forecasts_access_usage_2025_2027.csv'
    return _read_csv(path, numeric_cols=['mean', 'lower_ci', 'upper_ci', 'year'])


def observation_timeseries(df, indicator_code):
    """Return a clean year/value series for one indicator_code from observations."""
    obs = df[df['record_type'] == 'observation'].copy()
    obs = obs[obs['indicator_code'] == indicator_code]
    if obs.empty:
        return pd.DataFrame(columns=['year', 'value'])
    obs['year'] = pd.to_datetime(obs['observation_date'], errors='coerce').dt.year
    obs['value'] = pd.to_numeric(obs['value_numeric'], errors='coerce')
    ts = (
        obs.dropna(subset=['year', 'value'])
        .sort_values('year')
        .drop_duplicates(subset=['year'], keep='last')[['year', 'value']]
        .reset_index(drop=True)
    )
    ts['year'] = ts['year'].astype(int)
    return ts
