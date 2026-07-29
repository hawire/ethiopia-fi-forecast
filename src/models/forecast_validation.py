"""Forecast validation entrypoints (MAE / RMSE / MAPE + backtesting).

This module was introduced as a remote stub; it now delegates to the fuller
``metrics`` and ``backtesting`` implementations so callers have a stable API.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.models.backtesting import (
    expanding_window_backtest,
    leave_one_out_backtest,
    run_indicator_backtests,
    save_backtest_results,
)
from src.models.metrics import mae, mape, rmse, summarize_errors

OUT_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'


def validate_series(y_true, y_pred) -> dict:
    """Return MAE, RMSE, MAPE for a prediction pair."""
    return summarize_errors(y_true, y_pred)


def validate_baseline_trend(ts: pd.DataFrame, label: str = 'series') -> dict:
    """In-sample linear-trend diagnostics for a year/value series."""
    from src.models.forecast_advanced import validate_baseline_model

    return validate_baseline_model(ts, label=label)


def run_validation_suite(obs_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run expanding-window / LOO / in-sample validation for access & usage."""
    detail_df, summary_df = run_indicator_backtests(obs_df)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_backtest_results(detail_df, summary_df)
    summary_df.to_csv(OUT_DIR / 'forecast_validation_summary.csv', index=False)
    return detail_df, summary_df


def main():
    from src.data_loader import load_enriched_data
    from src.models.forecast_advanced import load_observations

    df = load_enriched_data()
    obs_df = load_observations(df)
    detail_df, summary_df = run_validation_suite(obs_df)
    print(summary_df.to_string(index=False))
    print(f'Detail folds: {len(detail_df)}')


if __name__ == '__main__':
    main()
