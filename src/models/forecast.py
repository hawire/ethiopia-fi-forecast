import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

DATA_PATH = Path(__file__).resolve().parents[2] / 'data' / 'processed' / 'ethiopia_fi_unified_data_enriched.csv'
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
    if train.shape[0] < 2:
        raise ValueError('Not enough data to fit model')
    X_train = train[['year','mobile_subscribers','g4']]
    y_train = train['account_ownership']
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model, X_train, y_train


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
    Xf = pd.DataFrame(rows)[['year','mobile_subscribers','g4']]
    preds = model.predict(Xf.fillna(0))
    Xf['account_ownership_pred'] = preds
    return Xf


def main():
    df = pd.read_csv(DATA_PATH)
    df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')
    df['value_numeric'] = pd.to_numeric(df['value_numeric'], errors='coerce')
    obs = load_observations(df)
    pivot = prepare_features(obs)
    model, X_train, y_train = fit_model(pivot)
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

if __name__ == '__main__':
    main()
