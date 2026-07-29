"""Scenario analysis helpers built on top of advanced forecasts.

Preserves the original ``generate_scenario_forecast`` API from the remote
stub and wires it to reproducible, growth-adjusted paths.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.scenario_config import SCENARIO_CONFIG, get_scenario_params


def generate_scenario_forecast(
    base_forecast,
    historical_growth,
    growth_adjustment,
):
    """Apply an additive growth adjustment to a base forecast path.

    Parameters
    ----------
    base_forecast : sequence
        Baseline future levels (e.g. trend-only means for 2025–2027).
    historical_growth : float
        Estimated historical annual growth (same units as forecast levels,
        e.g. percentage points per year).
    growth_adjustment : float
        Scenario additive adjustment to annual growth (fractional or pp;
        typically from ``SCENARIO_CONFIG[*]['growth_adjustment']``).

    Returns
    -------
    list[float]
        Scenario path starting from the first base level and compounding
        the adjusted annual growth over subsequent periods.
    """
    base = np.asarray(base_forecast, dtype=float).ravel()
    if base.size == 0:
        return []

    adjusted_growth = float(historical_growth) + float(growth_adjustment)
    out = [float(base[0])]
    for i in range(1, len(base)):
        # Prefer continuing from the prior scenario level; fall back to base
        # when the base path encodes absolute levels rather than increments.
        prev = out[-1]
        out.append(float(prev + adjusted_growth))
    return out


def generate_named_scenario_forecast(base_forecast, historical_growth, scenario='base'):
    """Convenience wrapper using ``SCENARIO_CONFIG`` growth adjustments."""
    cfg = SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG['base'])
    return generate_scenario_forecast(
        base_forecast,
        historical_growth,
        cfg['growth_adjustment'],
    )


def build_scenario_table(obs_df, scenarios=None, seed=42):
    """Build a tidy scenario table using the full advanced forecasting stack.

    Returns the same columns as ``forecasts_access_usage_2025_2027.csv``.
    """
    from src.models.forecast_advanced import forecast_access_usage, load_observations

    scenarios = scenarios or list(SCENARIO_CONFIG.keys())
    if 'observation_date' in obs_df.columns and 'year' not in obs_df.columns:
        # Accept either enriched raw frame or observation frame
        try:
            working = load_observations(obs_df) if 'record_type' in obs_df.columns else obs_df
        except Exception:
            working = obs_df
    else:
        working = obs_df

    enriched = obs_df if 'record_type' in obs_df.columns else None
    results, years, meta = forecast_access_usage(
        working if 'value' in working.columns else load_observations(obs_df),
        scenarios=scenarios,
        seed=seed,
        enriched_df=enriched,
    )

    rows = []
    for indicator in results:
        for scenario in results[indicator]:
            fc = results[indicator][scenario]
            params = get_scenario_params(scenario)
            for i, year in enumerate(years):
                rows.append({
                    'indicator': indicator,
                    'scenario': scenario,
                    'year': int(year),
                    'mean': float(fc['mean'][i]),
                    'lower_ci': float(fc['lower'][i]),
                    'upper_ci': float(fc['upper'][i]),
                    'growth_scale': params['growth_scale'],
                    'event_scale': params['event_scale'],
                    'growth_adjustment': params['growth_adjustment'],
                })
    return pd.DataFrame(rows), meta
