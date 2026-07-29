# Ethiopia Financial Inclusion Forecast Dashboard

Interactive Streamlit dashboard for Ethiopia financial inclusion scenarios (2025–2027), model validation, and sensitivity analysis.

## Features

- **Scenario Comparison:** Base, optimistic, and pessimistic forecasts with 90% CI bands
- **Key Indicators:** Account Ownership (Access), Digital Payment Adoption (Usage)
- **Model Validation:** Backtest MAE / RMSE / MAPE and in-sample diagnostics
- **Sensitivity Analysis:** OAT tornado rankings and charts
- **Event Impact Matrix:** Heatmap and table of event → indicator effects
- **Downloads:** Forecast, backtest, and sensitivity CSVs
- **Methodology:** Embedded forecast summary and validation notes

## Setup

```bash
pip install -r requirements.txt
python -m src.run_pipeline          # generate artefacts
streamlit run dashboard/app.py
```

Dashboard URL: `http://localhost:8501`

## Data Inputs

| File | Role |
|------|------|
| `data/processed/forecasts_access_usage_2025_2027.csv` | Scenario forecasts |
| `data/processed/ethiopia_fi_unified_data_enriched.csv` | Observations / events / links |
| `data/processed/backtest_metrics.csv` | Backtest MAE/RMSE/MAPE |
| `data/processed/sensitivity_tornado.csv` | Sensitivity ranking |
| `data/processed/model_validation_metrics.csv` | In-sample validation |
| `data/processed/event_indicator_matrix.csv` | Event association matrix |
| `reports/figures/*.png` | Heatmap and tornado plots |
| `reports/forecast_summary.md` | Methodology text |

## Troubleshooting

- **Missing forecast data:** run `python -m src.run_pipeline` from the project root
- **ModuleNotFoundError: streamlit:** `pip install -r requirements.txt`
- **Port in use:** `streamlit run dashboard/app.py --server.port 8502`

## Version

**1.1** — 2026-07-29 — validation, sensitivity, and improved event-impact views added
