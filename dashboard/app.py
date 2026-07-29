import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Configuration
DATA_DIR = Path(__file__).resolve().parents[1] / 'data' / 'processed'
FIGURES_DIR = Path(__file__).resolve().parents[1] / 'reports' / 'figures'
REPORTS_DIR = Path(__file__).resolve().parents[1] / 'reports'

st.set_page_config(page_title='Ethiopia Financial Inclusion Forecast', layout='wide')

st.title('Ethiopia Financial Inclusion Forecast Dashboard')
st.markdown('### 2025-2027 Scenario Analysis, Validation & Sensitivity')

# Load data
@st.cache_data
def load_forecast_data():
    try:
        df = pd.read_csv(DATA_DIR / 'forecasts_access_usage_2025_2027.csv')
        return df
    except FileNotFoundError:
        st.error('Forecast data not found. Please run the forecast script.')
        return None

@st.cache_data
def load_enriched_data():
    try:
        df = pd.read_csv(DATA_DIR / 'ethiopia_fi_unified_data_enriched.csv')
        return df
    except FileNotFoundError:
        st.warning('Enriched data not found.')
        return None

@st.cache_data
def load_optional_csv(name):
    path = DATA_DIR / name
    if path.exists():
        return pd.read_csv(path)
    alt = REPORTS_DIR / name
    if alt.exists():
        return pd.read_csv(alt)
    return None

forecast_df = load_forecast_data()
enriched_df = load_enriched_data()
backtest_df = load_optional_csv('backtest_metrics.csv')
sensitivity_df = load_optional_csv('sensitivity_tornado.csv')
validation_df = load_optional_csv('model_validation_metrics.csv')
event_matrix_df = load_optional_csv('event_indicator_matrix.csv')

if forecast_df is not None:
    # Sidebar controls
    st.sidebar.header('Scenario Selector')
    selected_scenarios = st.sidebar.multiselect(
        'Select scenarios to compare:',
        options=['base', 'optimistic', 'pessimistic'],
        default=['base', 'optimistic']
    )

    st.sidebar.header('Views')
    show_validation = st.sidebar.checkbox('Show model validation', value=True)
    show_sensitivity = st.sidebar.checkbox('Show sensitivity analysis', value=True)
    show_events = st.sidebar.checkbox('Show event impact', value=True)

    # Main metrics overview
    col1, col2, col3 = st.columns(3)

    access_2027 = forecast_df[
        (forecast_df['indicator'] == 'access') &
        (forecast_df['scenario'] == 'base') &
        (forecast_df['year'] == 2027)
    ]['mean'].values

    with col1:
        st.metric('Account Ownership 2027 (Base)',
                 f"{access_2027[0]:.1f}%" if len(access_2027) > 0 else 'N/A')

    usage_2027 = forecast_df[
        (forecast_df['indicator'] == 'usage') &
        (forecast_df['scenario'] == 'base') &
        (forecast_df['year'] == 2027)
    ]['mean'].values

    with col2:
        st.metric('Digital Payments 2027 (Base)',
                 f"{usage_2027[0]:.1f}%" if len(usage_2027) > 0 else 'N/A')

    with col3:
        st.metric('Scenario Range (2027)',
                 f"{forecast_df[forecast_df['year']==2027]['mean'].min():.1f}% - {forecast_df[forecast_df['year']==2027]['mean'].max():.1f}%")

    st.divider()

    # Scenario comparison charts
    st.subheader('Forecast Scenarios 2025-2027')

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('#### Account Ownership (Access)')
        access_forecast = forecast_df[forecast_df['indicator'] == 'access']
        fig, ax = plt.subplots(figsize=(8, 4))
        for scenario in selected_scenarios:
            scenario_data = access_forecast[access_forecast['scenario'] == scenario]
            scenario_data = scenario_data.sort_values('year')
            ax.plot(scenario_data['year'], scenario_data['mean'],
                   marker='o', label=scenario.capitalize(), linewidth=2)
            ax.fill_between(scenario_data['year'],
                           scenario_data['lower_ci'],
                           scenario_data['upper_ci'],
                           alpha=0.2)
        ax.set_xlabel('Year')
        ax.set_ylabel('Account Ownership (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)

    with col_b:
        st.markdown('#### Digital Payment Adoption (Usage)')
        usage_forecast = forecast_df[forecast_df['indicator'] == 'usage']
        fig, ax = plt.subplots(figsize=(8, 4))
        for scenario in selected_scenarios:
            scenario_data = usage_forecast[usage_forecast['scenario'] == scenario]
            scenario_data = scenario_data.sort_values('year')
            ax.plot(scenario_data['year'], scenario_data['mean'],
                   marker='o', label=scenario.capitalize(), linewidth=2)
            ax.fill_between(scenario_data['year'],
                           scenario_data['lower_ci'],
                           scenario_data['upper_ci'],
                           alpha=0.2)
        ax.set_xlabel('Year')
        ax.set_ylabel('Digital Payment Adoption (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)

    # Forecast table
    with st.expander('View forecast table'):
        filtered = forecast_df[forecast_df['scenario'].isin(selected_scenarios)].sort_values(
            ['indicator', 'scenario', 'year']
        )
        st.dataframe(filtered, use_container_width=True)

    st.divider()

    # Validation / backtesting
    if show_validation:
        st.subheader('Model Validation & Backtesting')
        st.markdown(
            'Time-series backtests (expanding-window / leave-one-out) and in-sample fit diagnostics '
            'report **MAE**, **RMSE**, and **MAPE**.'
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('#### Backtest metrics')
            if backtest_df is not None:
                st.dataframe(backtest_df, use_container_width=True)
            else:
                st.info('Run `python -m src.models.backtesting` to generate backtest metrics.')
        with c2:
            st.markdown('#### In-sample validation')
            if validation_df is not None:
                st.dataframe(validation_df, use_container_width=True)
            else:
                st.info('Run `python -m src.models.forecast_advanced` to generate validation metrics.')

        if (REPORTS_DIR / 'backtest_validation.md').exists():
            with st.expander('Backtest notes'):
                st.markdown((REPORTS_DIR / 'backtest_validation.md').read_text(encoding='utf-8'))

    # Sensitivity
    if show_sensitivity:
        st.divider()
        st.subheader('Sensitivity Analysis')
        st.markdown(
            'One-at-a-time (OAT) sweeps of growth scale, event scale, lag, decay, and residual scale. '
            'Tornado ranking shows which assumptions move the 2027 forecast most.'
        )
        if sensitivity_df is not None:
            st.dataframe(sensitivity_df, use_container_width=True)
        else:
            st.info('Run `python -m src.models.sensitivity` to generate sensitivity results.')

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            p = FIGURES_DIR / 'sensitivity_tornado_access.png'
            if p.exists():
                st.image(str(p), caption='Access sensitivity tornado')
        with col_s2:
            p = FIGURES_DIR / 'sensitivity_tornado_usage.png'
            if p.exists():
                st.image(str(p), caption='Usage sensitivity tornado')

        if (REPORTS_DIR / 'sensitivity_analysis.md').exists():
            with st.expander('Sensitivity methodology'):
                st.markdown((REPORTS_DIR / 'sensitivity_analysis.md').read_text(encoding='utf-8'))

    # Event Impact Matrix
    if show_events:
        st.divider()
        st.subheader('Event Impact Matrix')
        st.markdown(
            'Association between events and financial inclusion indicators, using confidence- and '
            'magnitude-weighted effects with documented lags.'
        )
        if (FIGURES_DIR / 'event_indicator_matrix.png').exists():
            st.image(str(FIGURES_DIR / 'event_indicator_matrix.png'))
        if event_matrix_df is not None:
            st.dataframe(event_matrix_df, use_container_width=True)

    # Data download
    st.divider()
    st.subheader('Download Data')
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button(
            label='Download Forecast CSV',
            data=forecast_df.to_csv(index=False),
            file_name='forecasts_access_usage_2025_2027.csv',
            mime='text/csv'
        )
    with dl2:
        if backtest_df is not None:
            st.download_button(
                label='Download Backtest Metrics',
                data=backtest_df.to_csv(index=False),
                file_name='backtest_metrics.csv',
                mime='text/csv'
            )
    with dl3:
        if sensitivity_df is not None:
            st.download_button(
                label='Download Sensitivity Tornado',
                data=sensitivity_df.to_csv(index=False),
                file_name='sensitivity_tornado.csv',
                mime='text/csv'
            )

    # Forecast summary
    st.divider()
    st.subheader('Forecast Methodology & Assumptions')

    with st.expander('View Methodology'):
        try:
            with open(REPORTS_DIR / 'forecast_summary.md', 'r', encoding='utf-8') as f:
                st.markdown(f.read())
        except FileNotFoundError:
            st.info('Forecast summary document not found.')

    # Data quality indicator
    st.divider()
    st.markdown('### Data Quality & Coverage')

    if enriched_df is not None:
        obs_count = len(enriched_df[enriched_df['record_type'] == 'observation'])
        event_count = len(enriched_df[enriched_df['record_type'] == 'event'])
        link_count = len(enriched_df[enriched_df['record_type'] == 'impact_link'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Total Observations', obs_count)
        with col2:
            st.metric('Events in Impact Model', event_count)
        with col3:
            st.metric('Impact Links', link_count)

    st.markdown(
        """
        ---
        **Dashboard Version:** 1.1  
        **Last Updated:** 2026-07-29  
        **Data Source:** Ethiopia Financial Inclusion Forecast Project
        """
    )
else:
    st.warning('No forecast data available. From the project root run: `python -m src.run_pipeline`')
