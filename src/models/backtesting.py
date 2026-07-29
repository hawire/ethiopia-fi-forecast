"""Time-series backtesting utilities for Ethiopia FI forecasts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from src.models.metrics import summarize_errors

OUT_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'
REPORT_DIR = Path(__file__).resolve().parents[2] / 'reports'


def expanding_window_backtest(ts: pd.DataFrame, min_train: int = 2, horizon: int = 1) -> pd.DataFrame:
    """Expanding-window one-step (or h-step) ahead linear-trend backtest.

    Parameters
    ----------
    ts : DataFrame with columns ``year`` and ``value``
    min_train : minimum training observations before first forecast
    horizon : steps ahead (in observation index space, not calendar years)
    """
    if ts is None or len(ts) < min_train + horizon:
        return pd.DataFrame(columns=['train_end_year', 'target_year', 'y_true', 'y_pred'])

    series = ts.sort_values('year').reset_index(drop=True)
    rows = []
    for i in range(min_train, len(series) - horizon + 1):
        train = series.iloc[:i]
        target = series.iloc[i + horizon - 1]
        model = LinearRegression()
        X_train = train['year'].to_numpy().reshape(-1, 1)
        y_train = train['value'].to_numpy()
        model.fit(X_train, y_train)
        y_pred = float(model.predict([[target['year']]])[0])
        rows.append({
            'train_end_year': int(train['year'].iloc[-1]),
            'target_year': int(target['year']),
            'y_true': float(target['value']),
            'y_pred': y_pred,
            'horizon': horizon,
        })
    return pd.DataFrame(rows)


def leave_one_out_backtest(ts: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-out trend backtest (fit on all but one year, predict that year)."""
    if ts is None or len(ts) < 3:
        return pd.DataFrame(columns=['held_out_year', 'y_true', 'y_pred'])

    series = ts.sort_values('year').reset_index(drop=True)
    rows = []
    for i in range(len(series)):
        train = series.drop(index=i)
        target = series.iloc[i]
        model = LinearRegression()
        X_train = train['year'].to_numpy().reshape(-1, 1)
        y_train = train['value'].to_numpy()
        model.fit(X_train, y_train)
        y_pred = float(model.predict(np.array([[target['year']]]))[0])
        rows.append({
            'held_out_year': int(target['year']),
            'y_true': float(target['value']),
            'y_pred': y_pred,
        })
    return pd.DataFrame(rows)


def evaluate_backtest(bt: pd.DataFrame, indicator: str, method: str) -> dict:
    """Compute MAE/RMSE/MAPE for a backtest result frame."""
    if bt is None or bt.empty:
        return {
            'indicator': indicator,
            'method': method,
            'n': 0,
            'mae': float('nan'),
            'rmse': float('nan'),
            'mape': float('nan'),
            'status': 'insufficient_data',
        }
    stats = summarize_errors(bt['y_true'], bt['y_pred'])
    stats.update({'indicator': indicator, 'method': method, 'status': 'ok'})
    return stats


def run_indicator_backtests(obs_df: pd.DataFrame, indicator_map: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run expanding-window and LOO backtests for configured indicators.

    Returns
    -------
    detail_df : fold-level predictions
    summary_df : metric summary by indicator/method
    """
    from src.models.forecast_advanced import get_indicator_timeseries

    indicator_map = indicator_map or {
        'access': 'account_ownership',
        'usage': 'digital_payments',
    }

    details = []
    summaries = []
    for label, code in indicator_map.items():
        ts = get_indicator_timeseries(obs_df, code)
        exp = expanding_window_backtest(ts, min_train=2, horizon=1)
        loo = leave_one_out_backtest(ts)

        if not exp.empty:
            exp = exp.assign(indicator=label, indicator_code=code, method='expanding_window')
            details.append(exp)
        if not loo.empty:
            loo = loo.assign(indicator=label, indicator_code=code, method='leave_one_out')
            details.append(loo)

        summaries.append(evaluate_backtest(exp, label, 'expanding_window'))
        summaries.append(evaluate_backtest(loo, label, 'leave_one_out'))

        # In-sample fit diagnostics (validation, not true out-of-sample)
        if ts is not None and len(ts) >= 2:
            model = LinearRegression()
            model.fit(ts[['year']], ts['value'])
            in_sample = model.predict(ts[['year']])
            stats = summarize_errors(ts['value'], in_sample)
            stats.update({
                'indicator': label,
                'method': 'in_sample_fit',
                'status': 'ok',
                'slope': float(model.coef_[0]),
                'intercept': float(model.intercept_),
                'r2': float(model.score(ts[['year']], ts['value'])),
            })
            summaries.append(stats)

    detail_df = pd.concat(details, ignore_index=True) if details else pd.DataFrame()
    summary_df = pd.DataFrame(summaries)
    return detail_df, summary_df


def save_backtest_results(detail_df: pd.DataFrame, summary_df: pd.DataFrame):
    """Persist backtest detail and summary CSVs."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    detail_path = OUT_DIR / 'backtest_detail.csv'
    summary_path = OUT_DIR / 'backtest_metrics.csv'
    detail_df.to_csv(detail_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    # Markdown summary for reports
    md_path = REPORT_DIR / 'backtest_validation.md'
    lines = [
        '# Forecast Backtesting & Validation',
        '',
        'Expanding-window and leave-one-out linear-trend backtests with MAE / RMSE / MAPE.',
        '',
        '## Metric summary',
        '',
        summary_df.to_markdown(index=False) if hasattr(summary_df, 'to_markdown') else summary_df.to_string(index=False),
        '',
        '## Notes',
        '',
        '- Sparse survey cadence (Findex) limits fold count; metrics should be interpreted cautiously.',
        '- `in_sample_fit` is diagnostic only and is not an out-of-sample score.',
        '',
    ]
    try:
        md_path.write_text('\n'.join(lines), encoding='utf-8')
    except Exception:
        # Fallback without tabulate / to_markdown
        md_path.write_text(
            '# Forecast Backtesting & Validation\n\n'
            + summary_df.to_string(index=False)
            + '\n',
            encoding='utf-8',
        )
    return detail_path, summary_path, md_path


def main():
    from src.data_loader import load_enriched_data
    from src.models.forecast_advanced import load_observations

    df = load_enriched_data()
    obs_df = load_observations(df)
    detail_df, summary_df = run_indicator_backtests(obs_df)
    paths = save_backtest_results(detail_df, summary_df)
    print('Saved backtest detail:', paths[0])
    print('Saved backtest metrics:', paths[1])
    print('Saved backtest report:', paths[2])
    print(summary_df.to_string(index=False))


if __name__ == '__main__':
    main()
