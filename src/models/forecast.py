import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

from src.data_loader import load_enriched_data
from src.models.metrics import summarize_errors

OUT_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_observations(df):
    obs = df[df['record_type']=='observation'].copy()
    obs['year'] = pd.DatetimeIndex(obs['observation_date']).year
    return obs


def prepare_features(obs):
    # pivot indicators into columns
    pivot = obs.pivot_table(index='year', columns='indicator_code', values='value_numeric', aggfunc='mean')
    pivot = pivot.sort_index()
    return pivot


def fit_model(pivot):
    # Use year, mobile_subscribers, 4g_coverage to predict account_ownership
    df = pivot.reset_index()
    X = df[['year']].copy()
    if 'mobile_subscribers' in df.columns:
        X['mobile_subscribers'] = df['mobile_subscribers']
    else:
        X['mobile_subscribers'] = np.nan
    if '4g_coverage' in df.columns:
        X['g4'] = df['4g_coverage']
    else:
        X['g4'] = np.nan
    y = df['account_ownership'] if 'account_ownership' in df.columns else None
    # drop rows with NaN in y
    train = pd.concat([X,y], axis=1).dropna()
    # If there are not enough rows with full predictors, fall back to year-only model
    if train.shape[0] >= 2 and train[['mobile_subscribers','g4']].notna().all(axis=1).sum() >= 2:
        X_train = train[['year','mobile_subscribers','g4']]
        y_train = train['account_ownership']
        model = LinearRegression()
        model.fit(X_train.fillna(0), y_train)
        return model, X_train, y_train
    # Prefer year-only when covariates are mostly missing (avoids degenerate zero-filled fit)
    train2 = pd.concat([X[['year']], y], axis=1).dropna()
    if train2.shape[0] >= 2:
        X_train = train2[['year']]
        y_train = train2['account_ownership']
        model = LinearRegression()
        model.fit(X_train, y_train)
        return model, X_train, y_train
    if train.shape[0] >= 2:
        X_train = train[['year','mobile_subscribers','g4']]
        y_train = train['account_ownership']
        model = LinearRegression()
        model.fit(X_train.fillna(0), y_train)
        return model, X_train, y_train
    raise ValueError('Not enough data to fit any model')


def validate_model(model, X_train, y_train):
    """Compute in-sample MAE/RMSE/MAPE for the fitted regression."""
    preds = model.predict(X_train.fillna(0) if hasattr(X_train, 'fillna') else X_train)
    stats = summarize_errors(y_train, preds)
    stats['r2'] = float(model.score(X_train.fillna(0) if hasattr(X_train, 'fillna') else X_train, y_train))
    stats['n_features'] = int(getattr(model, 'n_features_in_', X_train.shape[1]))
    return stats


def forecast(model, pivot, years=[2025,2026,2027], mobile_growth_rate=0.03, g4_increase_pp=3.0):
    last_year = pivot.index.max()
    last_mobile = pivot['mobile_subscribers'].loc[last_year] if 'mobile_subscribers' in pivot.columns else np.nan
    last_g4 = pivot['4g_coverage'].loc[last_year] if '4g_coverage' in pivot.columns else np.nan
    rows = []
    mobile = last_mobile
    g4 = last_g4
    for y in years:
        years_ahead = y - last_year
        if not np.isnan(mobile):
            mobile = last_mobile * ((1+mobile_growth_rate)**years_ahead)
        if not np.isnan(g4):
            g4 = last_g4 + g4_increase_pp * years_ahead
        rows.append({'year': y, 'mobile_subscribers': mobile, 'g4': g4})
    Xf_all = pd.DataFrame(rows)
    # build Xf with same columns used for training
    if hasattr(model, 'n_features_in_') and model.n_features_in_ == 1:
        Xf = Xf_all[['year']]
    else:
        # default to year, mobile_subscribers, g4 (fill missing with 0)
        Xf = Xf_all[['year','mobile_subscribers','g4']].fillna(0)
    preds = model.predict(Xf)
    Xf['account_ownership_pred'] = preds
    return Xf


def main():
    df = load_enriched_data()
    obs = load_observations(df)
    pivot = prepare_features(obs)
    model, X_train, y_train = fit_model(pivot)
    metrics = validate_model(model, X_train, y_train)
    print('Model validation (in-sample):', metrics)
    pd.DataFrame([metrics]).to_csv(OUT_DIR / 'account_ownership_model_metrics.csv', index=False)
    forecast_df = forecast(model, pivot)
    out_csv = OUT_DIR / 'account_ownership_forecast_2025_2027.csv'
    forecast_df.to_csv(out_csv, index=False)
    print('Saved forecast to', out_csv)
    # plot
    fig, ax = plt.subplots(figsize=(8,4))
    if 'account_ownership' in pivot.columns:
        ax.plot(pivot.index, pivot['account_ownership'], marker='o', label='Observed')
    ax.plot(forecast_df['year'], forecast_df['account_ownership_pred'], marker='o', label='Forecast')
    ax.set_ylabel('Account ownership (%)')
    ax.set_xlabel('Year')
    ax.legend()
    fig.savefig(OUT_DIR / 'account_ownership_forecast.png')
    plt.close(fig)

if __name__ == '__main__':
    main()
