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
st.markdown('### 2025-2027 Scenario Analysis')

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

forecast_df = load_forecast_data()
enriched_df = load_enriched_data()

if forecast_df is not None:
    # Sidebar controls
    st.sidebar.header('Scenario Selector')
    selected_scenarios = st.sidebar.multiselect(
        'Select scenarios to compare:',
        options=['base', 'optimistic', 'pessimistic'],
        default=['base', 'optimistic']
    )
    
    # Main metrics overview
    col1, col2, col3 = st.columns(3)
    
    # Access (Account Ownership) - Base scenario 2027
    access_2027 = forecast_df[
        (forecast_df['indicator'] == 'access') & 
        (forecast_df['scenario'] == 'base') & 
        (forecast_df['year'] == 2027)
    ]['mean'].values
    
    with col1:
        st.metric('Account Ownership 2027 (Base)', 
                 f"{access_2027[0]:.1f}%" if len(access_2027) > 0 else 'N/A')
    
    # Usage (Digital Payments) - Base scenario 2027
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
    
    st.divider()
    
    # Event Impact Matrix
    if (FIGURES_DIR / 'event_indicator_matrix.png').exists():
        st.subheader('Event Impact Matrix')
        st.markdown('Association between events and financial inclusion indicators')
        st.image(str(FIGURES_DIR / 'event_indicator_matrix.png'))
    
    # Data download
    st.divider()
    st.subheader('Download Data')
    csv = forecast_df.to_csv(index=False)
    st.download_button(
        label='Download Forecast CSV',
        data=csv,
        file_name='forecasts_access_usage_2025_2027.csv',
        mime='text/csv'
    )
    
    # Forecast summary
    st.divider()
    st.subheader('Forecast Methodology & Assumptions')
    
    with st.expander('View Methodology'):
        try:
            with open(REPORTS_DIR / 'forecast_summary.md', 'r') as f:
                st.markdown(f.read())
        except FileNotFoundError:
            st.info('Forecast summary document not found.')
    
    # Data quality indicator
    st.divider()
    st.markdown('### Data Quality & Coverage')
    
    if enriched_df is not None:
        obs_count = len(enriched_df[enriched_df['record_type'] == 'observation'])
        event_count = len(enriched_df[enriched_df['record_type'] == 'event'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric('Total Observations', obs_count)
        with col2:
            st.metric('Events in Impact Model', event_count)
    
    st.markdown(
        """
        ---
        **Dashboard Version:** 1.0  
        **Last Updated:** 2026-07-21  
        **Data Source:** Ethiopia Financial Inclusion Forecast Project
        """
    )
