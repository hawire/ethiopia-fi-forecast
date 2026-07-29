"""Run the full forecasting / validation / sensitivity pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_all(seed: int = 42):
    from src.data_loader import load_enriched_data
    from src.models import backtesting, event_impact, forecast, forecast_advanced, sensitivity

    print('=== Loading data ===')
    df = load_enriched_data()
    print(f'Loaded {len(df)} records')

    print('=== Event impact model ===')
    matrix, records, lag_matrix = event_impact.build_association_matrix(df)
    event_impact.save_results(matrix, records=records, lag_matrix=lag_matrix)
    print(f'Association matrix shape: {matrix.shape}; links: {len(records)}')

    print('=== Baseline regression forecast ===')
    forecast.main()

    print('=== Advanced scenario forecasts ===')
    obs_df = forecast_advanced.load_observations(df)
    results, years, meta = forecast_advanced.forecast_access_usage(
        obs_df, enriched_df=df, seed=seed,
    )
    forecast_advanced.save_forecast_csv(results, years, meta=meta)
    forecast_advanced.plot_forecasts(results, years, obs_df)
    print('Validation:', meta['validation'])

    print('=== Backtesting ===')
    detail_df, summary_df = backtesting.run_indicator_backtests(obs_df)
    backtesting.save_backtest_results(detail_df, summary_df)
    print(summary_df.to_string(index=False))

    print('=== Sensitivity analysis ===')
    sens_df = sensitivity.run_sensitivity_analysis(obs_df)
    tornado_df = sensitivity.tornado_summary(sens_df)
    sensitivity.plot_sensitivity_tornado(tornado_df)
    sensitivity.save_sensitivity_results(sens_df, tornado_df)
    print(tornado_df.to_string(index=False))

    print('=== Pipeline complete ===')
    return {
        'forecast_meta': meta,
        'backtest_summary': summary_df,
        'sensitivity_tornado': tornado_df,
    }


if __name__ == '__main__':
    run_all()
