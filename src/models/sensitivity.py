"""One-at-a-time (OAT) sensitivity analysis for scenario forecasts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'
FIG_DIR = Path(__file__).resolve().parents[2] / 'reports' / 'figures'
REPORT_DIR = Path(__file__).resolve().parents[2] / 'reports'


# Default parameter ranges as relative multipliers around baseline
DEFAULT_SENSITIVITY_GRID = {
    'growth_scale': [0.5, 0.75, 1.0, 1.25, 1.5],
    'event_scale': [0.0, 0.5, 1.0, 1.5, 2.0],
    'decay_factor': [0.7, 0.8, 0.9, 0.95, 1.0],
    'lag_years': [0, 1, 2],
    'residual_scale': [0.5, 1.0, 1.5, 2.0],
}


def _last_observed(ts) -> float | None:
    if ts is None or len(ts) == 0:
        return None
    return float(ts['value'].iloc[-1])


def forecast_with_params(
    slope,
    intercept,
    residual_std,
    years_ahead,
    last_value,
    *,
    growth_scale=1.0,
    event_effect=0.0,
    event_scale=1.0,
    lag_years=0,
    decay_factor=0.9,
    residual_scale=1.0,
    n_samples=100,
    seed=42,
):
    """Generate mean/CI forecast under explicit sensitivity parameters.

    Scenario logic: level = last + growth_scale * (trend - last) + event_scale * boost.
    """
    rng = np.random.default_rng(seed)
    years_ahead = np.asarray(years_ahead, dtype=float)
    trend = slope * years_ahead + intercept
    if last_value is None:
        last_value = float(trend[0])

    baseline_change = trend - last_value
    level = last_value + growth_scale * baseline_change

    boost = np.zeros_like(years_ahead, dtype=float)
    for i, _ in enumerate(years_ahead):
        if i >= lag_years:
            years_since = i - lag_years
            boost[i] = event_effect * (decay_factor ** years_since)
    level = level + event_scale * boost

    noise_std = (residual_std if residual_std else 0.1) * residual_scale
    samples = []
    for _ in range(n_samples):
        noise = rng.normal(0, noise_std, size=len(years_ahead))
        samples.append(level + noise)
    samples = np.asarray(samples)
    return {
        'mean': samples.mean(axis=0),
        'lower': np.percentile(samples, 5, axis=0),
        'upper': np.percentile(samples, 95, axis=0),
    }


def oat_sensitivity(
    slope,
    intercept,
    residual_std,
    years_ahead,
    last_value,
    event_effect,
    base_params=None,
    grid=None,
    target_year_index=-1,
):
    """Vary one parameter at a time; record target-year mean forecast."""
    base_params = base_params or {
        'growth_scale': 1.0,
        'event_scale': 1.0,
        'decay_factor': 0.9,
        'lag_years': 1,
        'residual_scale': 1.0,
    }
    grid = grid or DEFAULT_SENSITIVITY_GRID

    base_fc = forecast_with_params(
        slope, intercept, residual_std, years_ahead, last_value,
        event_effect=event_effect, **base_params, seed=42,
    )
    base_value = float(base_fc['mean'][target_year_index])

    rows = []
    for param, values in grid.items():
        for val in values:
            params = dict(base_params)
            # cast lag_years to int
            if param == 'lag_years':
                params[param] = int(val)
            else:
                params[param] = float(val)
            fc = forecast_with_params(
                slope, intercept, residual_std, years_ahead, last_value,
                event_effect=event_effect, **params, seed=42,
            )
            target = float(fc['mean'][target_year_index])
            rows.append({
                'parameter': param,
                'parameter_value': val,
                'forecast_mean': target,
                'delta_vs_base': target - base_value,
                'base_forecast': base_value,
            })
    return pd.DataFrame(rows)


def run_sensitivity_analysis(obs_df, years_ahead=None, event_effects=None):
    """Run OAT sensitivity for access and usage indicators."""
    from src.models.forecast_advanced import (
        fit_baseline_model,
        get_indicator_timeseries,
        DEFAULT_EVENT_EFFECTS,
    )

    years_ahead = np.asarray(years_ahead if years_ahead is not None else [2025, 2026, 2027])
    event_effects = event_effects or DEFAULT_EVENT_EFFECTS

    frames = []
    for label, code in [('access', 'account_ownership'), ('usage', 'digital_payments')]:
        ts = get_indicator_timeseries(obs_df, code)
        slope, intercept, resid = fit_baseline_model(ts)
        if slope is None and ts is not None and len(ts) >= 1:
            last_val = ts['value'].iloc[-1]
            last_year = ts['year'].iloc[-1]
            slope = 1.0 if label == 'access' else 3.0
            intercept = last_val - slope * last_year
            resid = 0.5
        if slope is None:
            continue
        last_value = _last_observed(ts)
        effect = event_effects.get(label, 0.02)
        sens = oat_sensitivity(
            slope, intercept, resid, years_ahead, last_value, effect,
        )
        sens['indicator'] = label
        sens['target_year'] = int(years_ahead[-1])
        frames.append(sens)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def tornado_summary(sens_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize min/max swing per parameter for tornado-style ranking."""
    if sens_df is None or sens_df.empty:
        return pd.DataFrame()
    rows = []
    for (indicator, parameter), g in sens_df.groupby(['indicator', 'parameter']):
        rows.append({
            'indicator': indicator,
            'parameter': parameter,
            'min_forecast': g['forecast_mean'].min(),
            'max_forecast': g['forecast_mean'].max(),
            'range': g['forecast_mean'].max() - g['forecast_mean'].min(),
            'base_forecast': g['base_forecast'].iloc[0],
            'target_year': g['target_year'].iloc[0],
        })
    out = pd.DataFrame(rows).sort_values(['indicator', 'range'], ascending=[True, False])
    return out.reset_index(drop=True)


def plot_sensitivity_tornado(tornado_df: pd.DataFrame):
    """Save tornado charts for each indicator."""
    import matplotlib.pyplot as plt

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    if tornado_df is None or tornado_df.empty:
        return paths

    for indicator, g in tornado_df.groupby('indicator'):
        g = g.sort_values('range')
        fig, ax = plt.subplots(figsize=(8, 4))
        y = np.arange(len(g))
        left = g['min_forecast']
        width = g['max_forecast'] - g['min_forecast']
        ax.barh(y, width, left=left, color='steelblue', alpha=0.8)
        ax.axvline(g['base_forecast'].iloc[0], color='black', linestyle='--', label='Base')
        ax.set_yticks(y)
        ax.set_yticklabels(g['parameter'])
        ax.set_xlabel(f'{indicator.capitalize()} forecast ({int(g["target_year"].iloc[0])})')
        ax.set_title(f'Sensitivity tornado — {indicator}')
        ax.legend()
        ax.grid(True, axis='x', alpha=0.3)
        fig.tight_layout()
        out = FIG_DIR / f'sensitivity_tornado_{indicator}.png'
        fig.savefig(out, dpi=150)
        plt.close(fig)
        paths.append(out)
    return paths


def save_sensitivity_results(sens_df: pd.DataFrame, tornado_df: pd.DataFrame):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    detail_path = OUT_DIR / 'sensitivity_oat.csv'
    tornado_path = OUT_DIR / 'sensitivity_tornado.csv'
    sens_df.to_csv(detail_path, index=False)
    tornado_df.to_csv(tornado_path, index=False)

    md_path = REPORT_DIR / 'sensitivity_analysis.md'
    lines = [
        '# Sensitivity Analysis',
        '',
        'One-at-a-time (OAT) sweeps around the base scenario for 2027 forecasts.',
        '',
        '## Tornado ranking (parameter influence)',
        '',
        tornado_df.to_string(index=False),
        '',
        '## Interpretation',
        '',
        '- Larger `range` means the 2027 point forecast is more sensitive to that assumption.',
        '- `growth_scale` scales the trend change relative to the last observation.',
        '- `event_scale` scales additive event boosts; `lag_years` and `decay_factor` control timing.',
        '',
    ]
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    return detail_path, tornado_path, md_path


def main():
    from src.data_loader import load_enriched_data
    from src.models.forecast_advanced import load_observations

    df = load_enriched_data()
    obs_df = load_observations(df)
    sens_df = run_sensitivity_analysis(obs_df)
    tornado_df = tornado_summary(sens_df)
    plot_sensitivity_tornado(tornado_df)
    paths = save_sensitivity_results(sens_df, tornado_df)
    print('Saved sensitivity detail:', paths[0])
    print('Saved tornado summary:', paths[1])
    print('Saved sensitivity report:', paths[2])
    print(tornado_df.to_string(index=False))


if __name__ == '__main__':
    main()
