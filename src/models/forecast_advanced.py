import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import seaborn as sns

from src.data_loader import load_enriched_data

OUT_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'
FIG_DIR = Path(__file__).resolve().parents[2] / 'reports' / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

def load_observations(df):
    obs_df = df[df['record_type'] == 'observation'].copy()
    obs_df['year'] = pd.to_datetime(obs_df['observation_date']).dt.year
    obs_df['value'] = pd.to_numeric(obs_df['value_numeric'], errors='coerce')
    return obs_df

def get_indicator_timeseries(obs_df, indicator_code):
    """Extract sorted time series for given indicator"""
    ts = obs_df[obs_df['indicator_code'] == indicator_code][['year', 'value']].dropna()
    if ts.empty:
        return None
    ts = ts.sort_values('year')
    ts = ts.drop_duplicates(subset=['year'], keep='first')
    return ts

def fit_baseline_model(ts):
    """Fit linear trend to observations; return (slope, intercept, residual_std)"""
    if ts is None or len(ts) < 2:
        return None, None, None
    X = ts['year'].values.reshape(-1, 1)
    y = ts['value'].values
    model = LinearRegression()
    model.fit(X, y)
    residuals = y - model.predict(X)
    std = np.std(residuals) if np.std(residuals) > 0 else 0.1
    return model.coef_[0], model.intercept_, std

def forecast_baseline(slope, intercept, residual_std, years_ahead, n_samples=100):
    """Generate baseline forecasts with uncertainty (bootstrap-like)"""
    if slope is None:
        return None
    forecasts = []
    for _ in range(n_samples):
        noise = np.random.normal(0, residual_std if residual_std else 0.01, len(years_ahead))
        trend = slope * years_ahead + intercept
        forecast = trend + noise
        forecasts.append(forecast)
    forecasts = np.array(forecasts)
    return {
        'mean': forecasts.mean(axis=0),
        'lower': np.percentile(forecasts, 5, axis=0),
        'upper': np.percentile(forecasts, 95, axis=0),
        'samples': forecasts
    }

def apply_event_boost(forecast_dict, event_effect, lag_years=0, decay_factor=0.9):
    """Apply event-based additive boost to forecast"""
    if forecast_dict is None:
        return None
    years_ahead = np.arange(len(forecast_dict['mean']))
    boost = np.zeros_like(years_ahead, dtype=float)
    for i, y in enumerate(years_ahead):
        if y >= lag_years:
            years_since = y - lag_years
            boost[i] = event_effect * (decay_factor ** years_since)
    
    return {
        'mean': forecast_dict['mean'] + boost,
        'lower': forecast_dict['lower'] + boost,
        'upper': forecast_dict['upper'] + boost,
    }

def scenario_scaling(forecast_dict, scenario='base'):
    """Apply scenario-specific scaling: pessimistic (0.7x), base (1.0x), optimistic (1.3x)"""
    if forecast_dict is None:
        return None
    scale = {'pessimistic': 0.7, 'base': 1.0, 'optimistic': 1.3}.get(scenario, 1.0)
    return {k: v * scale for k, v in forecast_dict.items()}

def forecast_access_usage(obs_df, scenarios=['base', 'optimistic', 'pessimistic']):
    """Produce 2025-2027 forecasts for Account Ownership (Access) and Digital Payments (Usage)"""
    years_ahead = np.array([2025, 2026, 2027])
    
    # Access: Account Ownership Rate
    access_ts = get_indicator_timeseries(obs_df, 'account_ownership')
    slope_a, intercept_a, residual_a = fit_baseline_model(access_ts)
    # Fallback for sparse data: estimate from last 2 observations
    if slope_a is None and access_ts is not None and len(access_ts) >= 1:
        last_val = access_ts['value'].iloc[-1]
        last_year = access_ts['year'].iloc[-1]
        slope_a = 1.0  # assume 1% annual growth
        intercept_a = last_val - slope_a * last_year
        residual_a = 0.5
    
    # Usage: Digital Payment Adoption Rate
    usage_ts = get_indicator_timeseries(obs_df, 'digital_payments')
    slope_u, intercept_u, residual_u = fit_baseline_model(usage_ts)
    # Fallback for sparse data: assume 15% annual growth from last obs
    if slope_u is None and usage_ts is not None and len(usage_ts) >= 1:
        last_val = usage_ts['value'].iloc[-1]
        last_year = usage_ts['year'].iloc[-1]
        slope_u = 3.0  # assume 3% annual growth (digital payment catching up)
        intercept_u = last_val - slope_u * last_year
        residual_u = 0.5
    
    results = {'access': {}, 'usage': {}}
    
    for scenario in scenarios:
        # baseline forecasts
        access_base = forecast_baseline(slope_a, intercept_a, residual_a, years_ahead)
        usage_base = forecast_baseline(slope_u, intercept_u, residual_u, years_ahead)
        
        # apply event boost (example: telebirr/mpesa effect 0.05 effect size, 1-year lag)
        access_event = apply_event_boost(access_base, 0.02, lag_years=1)
        usage_event = apply_event_boost(usage_base, 0.05, lag_years=1)
        
        # apply scenario scaling
        access_scenario = scenario_scaling(access_event, scenario)
        usage_scenario = scenario_scaling(usage_event, scenario)
        
        results['access'][scenario] = access_scenario
        results['usage'][scenario] = usage_scenario
    
    return results, years_ahead

def save_forecast_csv(results, years_ahead):
    """Save forecast results to CSV"""
    records = []
    for indicator in ['access', 'usage']:
        for scenario in results[indicator]:
            forecast = results[indicator][scenario]
            for i, year in enumerate(years_ahead):
                records.append({
                    'indicator': indicator,
                    'scenario': scenario,
                    'year': year,
                    'mean': forecast['mean'][i],
                    'lower_ci': forecast['lower'][i],
                    'upper_ci': forecast['upper'][i]
                })
    df_out = pd.DataFrame(records)
    out_csv = OUT_DIR / 'forecasts_access_usage_2025_2027.csv'
    df_out.to_csv(out_csv, index=False)
    return out_csv

def plot_forecasts(results, years_ahead, obs_df):
    """Plot forecasts with CI bands for all scenarios"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    colors = {'base': 'blue', 'optimistic': 'green', 'pessimistic': 'red'}
    
    # Access forecast
    access_ts = get_indicator_timeseries(obs_df, 'account_ownership')
    if access_ts is not None:
        ax1.plot(access_ts['year'], access_ts['value'], 'ko', label='Historical', markersize=6)
    for scenario in results['access']:
        fc = results['access'][scenario]
        ax1.plot(years_ahead, fc['mean'], '-o', color=colors[scenario], label=scenario, linewidth=2)
        ax1.fill_between(years_ahead, fc['lower'], fc['upper'], alpha=0.2, color=colors[scenario])
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Account Ownership Rate (%)')
    ax1.set_title('Account Ownership Forecast (Access) 2025-2027')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Usage forecast
    usage_ts = get_indicator_timeseries(obs_df, 'digital_payments')
    if usage_ts is not None:
        ax2.plot(usage_ts['year'], usage_ts['value'], 'ko', label='Historical', markersize=6)
    for scenario in results['usage']:
        fc = results['usage'][scenario]
        ax2.plot(years_ahead, fc['mean'], '-o', color=colors[scenario], label=scenario, linewidth=2)
        ax2.fill_between(years_ahead, fc['lower'], fc['upper'], alpha=0.2, color=colors[scenario])
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Digital Payment Adoption Rate (%)')
    ax2.set_title('Digital Payment Forecast (Usage) 2025-2027')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out_png = FIG_DIR / 'forecast_scenarios_access_usage.png'
    plt.savefig(out_png, dpi=150)
    return out_png

def main():
    df = load_enriched_data()
    obs_df = load_observations(df)
    
    results, years_ahead = forecast_access_usage(obs_df)
    
    out_csv = save_forecast_csv(results, years_ahead)
    print(f'Saved forecast CSV: {out_csv}')
    
    out_png = plot_forecasts(results, years_ahead, obs_df)
    print(f'Saved forecast plot: {out_png}')

if __name__ == '__main__':
    main()
