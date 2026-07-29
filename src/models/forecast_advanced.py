"""Advanced scenario forecasts for Access and Usage indicators.

Improvements over the original baseline:
- Reproducible RNG seeding
- Scenario scaling applied to growth and event effects (not absolute levels)
- Event effects drawn from structured impact-link metadata when available
- Optional integration with backtesting / sensitivity modules
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from src.data_loader import load_enriched_data

OUT_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'
FIG_DIR = Path(__file__).resolve().parents[2] / 'reports' / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SEED = 42

# Scenario parameters act on *changes* and event boosts, not raw levels.
SCENARIO_PARAMS = {
    'pessimistic': {
        'growth_scale': 0.6,
        'event_scale': 0.5,
        'residual_scale': 1.3,
        'description': 'Slower trend growth and weaker event transmission',
    },
    'base': {
        'growth_scale': 1.0,
        'event_scale': 1.0,
        'residual_scale': 1.0,
        'description': 'Continuation of estimated trend plus calibrated events',
    },
    'optimistic': {
        'growth_scale': 1.4,
        'event_scale': 1.5,
        'residual_scale': 1.2,
        'description': 'Faster adoption and stronger event pass-through',
    },
}

# Fallback additive effects (percentage points) if impact links are unavailable
DEFAULT_EVENT_EFFECTS = {
    'access': 0.02 * 100,   # kept small in pp terms after unit alignment
    'usage': 0.05 * 100,
}

# Prefer pp-scale effects consistent with indicator units (percent)
DEFAULT_EVENT_EFFECTS_PP = {
    'access': 0.5,   # +0.5 pp from events under base
    'usage': 2.0,    # +2.0 pp from events under base
}


def load_observations(df):
    obs_df = df[df['record_type'] == 'observation'].copy()
    obs_df['year'] = pd.to_datetime(obs_df['observation_date'], errors='coerce').dt.year
    obs_df['value'] = pd.to_numeric(obs_df['value_numeric'], errors='coerce')
    return obs_df


def get_indicator_timeseries(obs_df, indicator_code):
    """Extract sorted time series for given indicator."""
    ts = obs_df[obs_df['indicator_code'] == indicator_code][['year', 'value']].dropna()
    if ts.empty:
        return None
    ts = ts.sort_values('year')
    ts = ts.drop_duplicates(subset=['year'], keep='last')
    return ts.reset_index(drop=True)


def fit_baseline_model(ts):
    """Fit linear trend to observations; return (slope, intercept, residual_std)."""
    if ts is None or len(ts) < 2:
        return None, None, None
    X = ts['year'].values.reshape(-1, 1)
    y = ts['value'].values
    model = LinearRegression()
    model.fit(X, y)
    residuals = y - model.predict(X)
    std = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else float(np.std(residuals))
    if not np.isfinite(std) or std <= 0:
        std = 0.1
    return float(model.coef_[0]), float(model.intercept_), std


def validate_baseline_model(ts, label='series'):
    """Return in-sample validation diagnostics for a fitted trend."""
    from src.models.metrics import summarize_errors

    slope, intercept, resid = fit_baseline_model(ts)
    if slope is None:
        return {
            'indicator': label,
            'status': 'insufficient_data',
            'n': 0 if ts is None else len(ts),
        }
    y_hat = slope * ts['year'].values + intercept
    stats = summarize_errors(ts['value'].values, y_hat)
    ss_tot = np.sum((ts['value'].values - ts['value'].values.mean()) ** 2)
    ss_res = np.sum((ts['value'].values - y_hat) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    stats.update({
        'indicator': label,
        'status': 'ok',
        'slope': slope,
        'intercept': intercept,
        'residual_std': resid,
        'r2': float(r2),
    })
    return stats


def forecast_baseline(slope, intercept, residual_std, years_ahead, n_samples=100, seed=DEFAULT_SEED,
                      residual_scale=1.0, last_value=None, growth_scale=1.0):
    """Generate baseline forecasts with uncertainty (seeded sampling).

    If ``last_value`` is provided, growth_scale scales the change from last_value
    to the linear trend (scenario-aware growth), preserving level realism.
    """
    if slope is None:
        return None
    rng = np.random.default_rng(seed)
    years_ahead = np.asarray(years_ahead, dtype=float)
    trend = slope * years_ahead + intercept
    if last_value is None:
        mean_path = trend
    else:
        mean_path = last_value + growth_scale * (trend - last_value)

    noise_std = (residual_std if residual_std else 0.01) * residual_scale
    forecasts = []
    for _ in range(n_samples):
        noise = rng.normal(0, noise_std, len(years_ahead))
        forecasts.append(mean_path + noise)
    forecasts = np.array(forecasts)
    return {
        'mean': forecasts.mean(axis=0),
        'lower': np.percentile(forecasts, 5, axis=0),
        'upper': np.percentile(forecasts, 95, axis=0),
        'samples': forecasts,
    }


def apply_event_boost(forecast_dict, event_effect, lag_years=0, decay_factor=0.9, event_scale=1.0):
    """Apply event-based additive boost to forecast (scaled by scenario)."""
    if forecast_dict is None:
        return None
    years_ahead = np.arange(len(forecast_dict['mean']))
    boost = np.zeros_like(years_ahead, dtype=float)
    for i, y in enumerate(years_ahead):
        if y >= lag_years:
            years_since = y - lag_years
            boost[i] = event_effect * event_scale * (decay_factor ** years_since)

    out = {
        'mean': forecast_dict['mean'] + boost,
        'lower': forecast_dict['lower'] + boost,
        'upper': forecast_dict['upper'] + boost,
    }
    if 'samples' in forecast_dict:
        out['samples'] = forecast_dict['samples'] + boost
    return out


def scenario_scaling(forecast_dict, scenario='base'):
    """Backward-compatible absolute scaling (legacy API).

    Prefer growth/event scaling via ``SCENARIO_PARAMS`` in ``forecast_access_usage``.
    Kept so existing callers/notebooks continue to work.
    """
    if forecast_dict is None:
        return None
    scale = {'pessimistic': 0.7, 'base': 1.0, 'optimistic': 1.3}.get(scenario, 1.0)
    return {k: (v * scale if k != 'samples' else v * scale) for k, v in forecast_dict.items()}


def resolve_event_effects(df=None, fallback=None):
    """Derive per-indicator event effects from impact links when possible."""
    fallback = fallback or DEFAULT_EVENT_EFFECTS_PP
    effects = dict(fallback)
    lags = {'access': 1, 'usage': 1}
    decays = {'access': 0.9, 'usage': 0.9}

    if df is None:
        return effects, lags, decays

    try:
        from src.models.event_impact import build_association_matrix, parse_link_metadata
    except Exception:
        return effects, lags, decays

    links = df[df['record_type'] == 'impact_link']
    if links.empty:
        return effects, lags, decays

    # Map canonical indicators to access/usage labels
    code_to_label = {
        'account_ownership': 'access',
        'digital_payments': 'usage',
    }
    for _, link in links.iterrows():
        meta = parse_link_metadata(link)
        target = meta.get('target') or link.get('indicator_code')
        label = code_to_label.get(target)
        if label is None:
            continue
        # Impact-link effects are stored on a 0–1 fraction scale; forecasts use percentage points.
        raw_effect = float(meta.get('effect', 0.02))
        effects[label] = raw_effect * 100.0 if abs(raw_effect) < 1 else raw_effect
        if meta.get('lag_years') is not None:
            lags[label] = int(meta['lag_years'])
        if meta.get('decay') is not None:
            decays[label] = float(meta['decay'])

    # Also allow matrix-derived magnitudes as a cross-check
    try:
        matrix, *_ = build_association_matrix(df)
        for label, code in [('access', 'account_ownership'), ('usage', 'digital_payments')]:
            if code in matrix.columns and len(matrix):
                # convert fraction-scale matrix values to percentage points if small
                col_max = float(matrix[code].max())
                if col_max > 0:
                    pp = col_max * 100 if col_max < 1 else col_max
                    # blend with metadata-derived effect
                    effects[label] = 0.5 * effects[label] + 0.5 * pp
    except Exception:
        pass

    return effects, lags, decays


def forecast_access_usage(
    obs_df,
    scenarios=None,
    seed=DEFAULT_SEED,
    n_samples=100,
    enriched_df=None,
    use_legacy_level_scaling=False,
):
    """Produce 2025-2027 forecasts for Account Ownership (Access) and Digital Payments (Usage)."""
    scenarios = scenarios or ['base', 'optimistic', 'pessimistic']
    years_ahead = np.array([2025, 2026, 2027])

    event_effects, event_lags, event_decays = resolve_event_effects(enriched_df)

    # Access: Account Ownership Rate
    access_ts = get_indicator_timeseries(obs_df, 'account_ownership')
    slope_a, intercept_a, residual_a = fit_baseline_model(access_ts)
    if slope_a is None and access_ts is not None and len(access_ts) >= 1:
        last_val = access_ts['value'].iloc[-1]
        last_year = access_ts['year'].iloc[-1]
        slope_a = 1.0
        intercept_a = last_val - slope_a * last_year
        residual_a = 0.5

    # Usage: Digital Payment Adoption Rate
    usage_ts = get_indicator_timeseries(obs_df, 'digital_payments')
    slope_u, intercept_u, residual_u = fit_baseline_model(usage_ts)
    if slope_u is None and usage_ts is not None and len(usage_ts) >= 1:
        last_val = usage_ts['value'].iloc[-1]
        last_year = usage_ts['year'].iloc[-1]
        slope_u = 3.0
        intercept_u = last_val - slope_u * last_year
        residual_u = 0.5

    last_access = float(access_ts['value'].iloc[-1]) if access_ts is not None and len(access_ts) else None
    last_usage = float(usage_ts['value'].iloc[-1]) if usage_ts is not None and len(usage_ts) else None

    results = {'access': {}, 'usage': {}}
    validation = {
        'access': validate_baseline_model(access_ts, 'access'),
        'usage': validate_baseline_model(usage_ts, 'usage'),
    }

    for scenario in scenarios:
        params = SCENARIO_PARAMS.get(scenario, SCENARIO_PARAMS['base'])
        # Deterministic per-scenario seeds (avoid Python's randomized hash())
        scenario_seed_offset = {'base': 0, 'optimistic': 100, 'pessimistic': 200}.get(scenario, 50)
        scenario_seed = seed + scenario_seed_offset

        access_base = forecast_baseline(
            slope_a, intercept_a, residual_a, years_ahead,
            n_samples=n_samples, seed=scenario_seed,
            residual_scale=params['residual_scale'],
            last_value=last_access,
            growth_scale=params['growth_scale'],
        )
        usage_base = forecast_baseline(
            slope_u, intercept_u, residual_u, years_ahead,
            n_samples=n_samples, seed=scenario_seed + 17,
            residual_scale=params['residual_scale'],
            last_value=last_usage,
            growth_scale=params['growth_scale'],
        )

        access_event = apply_event_boost(
            access_base,
            event_effects.get('access', DEFAULT_EVENT_EFFECTS_PP['access']),
            lag_years=event_lags.get('access', 1),
            decay_factor=event_decays.get('access', 0.9),
            event_scale=params['event_scale'],
        )
        usage_event = apply_event_boost(
            usage_base,
            event_effects.get('usage', DEFAULT_EVENT_EFFECTS_PP['usage']),
            lag_years=event_lags.get('usage', 1),
            decay_factor=event_decays.get('usage', 0.9),
            event_scale=params['event_scale'],
        )

        if use_legacy_level_scaling:
            access_scenario = scenario_scaling(access_event, scenario)
            usage_scenario = scenario_scaling(usage_event, scenario)
        else:
            access_scenario = access_event
            usage_scenario = usage_event

        results['access'][scenario] = access_scenario
        results['usage'][scenario] = usage_scenario

    meta = {
        'event_effects': event_effects,
        'event_lags': event_lags,
        'event_decays': event_decays,
        'scenario_params': {k: {kk: vv for kk, vv in v.items() if kk != 'description'}
                           for k, v in SCENARIO_PARAMS.items()},
        'validation': validation,
        'seed': seed,
    }
    return results, years_ahead, meta


def save_forecast_csv(results, years_ahead, meta=None):
    """Save forecast results to CSV."""
    records = []
    for indicator in ['access', 'usage']:
        for scenario in results[indicator]:
            forecast = results[indicator][scenario]
            for i, year in enumerate(years_ahead):
                records.append({
                    'indicator': indicator,
                    'scenario': scenario,
                    'year': int(year),
                    'mean': forecast['mean'][i],
                    'lower_ci': forecast['lower'][i],
                    'upper_ci': forecast['upper'][i],
                })
    df_out = pd.DataFrame(records)
    out_csv = OUT_DIR / 'forecasts_access_usage_2025_2027.csv'
    df_out.to_csv(out_csv, index=False)

    if meta is not None:
        val_rows = []
        for ind, stats in meta.get('validation', {}).items():
            row = dict(stats)
            row['indicator'] = ind
            val_rows.append(row)
        if val_rows:
            pd.DataFrame(val_rows).to_csv(OUT_DIR / 'model_validation_metrics.csv', index=False)
    return out_csv


def plot_forecasts(results, years_ahead, obs_df):
    """Plot forecasts with CI bands for all scenarios."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    colors = {'base': 'blue', 'optimistic': 'green', 'pessimistic': 'red'}

    access_ts = get_indicator_timeseries(obs_df, 'account_ownership')
    if access_ts is not None:
        ax1.plot(access_ts['year'], access_ts['value'], 'ko', label='Historical', markersize=6)
    for scenario in results['access']:
        fc = results['access'][scenario]
        ax1.plot(years_ahead, fc['mean'], '-o', color=colors.get(scenario, 'gray'),
                 label=scenario, linewidth=2)
        ax1.fill_between(years_ahead, fc['lower'], fc['upper'], alpha=0.2,
                         color=colors.get(scenario, 'gray'))
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Account Ownership Rate (%)')
    ax1.set_title('Account Ownership Forecast (Access) 2025-2027')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    usage_ts = get_indicator_timeseries(obs_df, 'digital_payments')
    if usage_ts is not None:
        ax2.plot(usage_ts['year'], usage_ts['value'], 'ko', label='Historical', markersize=6)
    for scenario in results['usage']:
        fc = results['usage'][scenario]
        ax2.plot(years_ahead, fc['mean'], '-o', color=colors.get(scenario, 'gray'),
                 label=scenario, linewidth=2)
        ax2.fill_between(years_ahead, fc['lower'], fc['upper'], alpha=0.2,
                         color=colors.get(scenario, 'gray'))
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Digital Payment Adoption Rate (%)')
    ax2.set_title('Digital Payment Forecast (Usage) 2025-2027')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = FIG_DIR / 'forecast_scenarios_access_usage.png'
    plt.savefig(out_png, dpi=150)
    plt.close(fig)
    return out_png


def main():
    df = load_enriched_data()
    obs_df = load_observations(df)

    results, years_ahead, meta = forecast_access_usage(obs_df, enriched_df=df, seed=DEFAULT_SEED)

    out_csv = save_forecast_csv(results, years_ahead, meta=meta)
    print(f'Saved forecast CSV: {out_csv}')
    print('Validation:', meta['validation'])

    out_png = plot_forecasts(results, years_ahead, obs_df)
    print(f'Saved forecast plot: {out_png}')


if __name__ == '__main__':
    main()
