# Ethiopia Financial Inclusion Forecast

Forecast Ethiopia's financial inclusion indicators (**Access** = account ownership, **Usage** = digital payment adoption) for 2025–2027 using an enriched observation/event dataset, scenario modelling, event-impact links, backtesting, and sensitivity analysis.

## Key folders

| Path | Purpose |
|------|---------|
| `data/processed/` | Enriched dataset, forecast CSVs, backtest & sensitivity outputs |
| `src/` | Data loader, forecasting models, validation, pipeline runner |
| `src/models/` | Baseline regression, advanced scenarios, event impact, metrics, backtesting, sensitivity |
| `dashboard/` | Streamlit interactive dashboard |
| `notebooks/` | EDA and modelling notebooks |
| `reports/` | Interim reports, methodology, validation notes, figures |
| `tests/` | Pytest suite (metrics, reproducibility, integration) |

## Features

- **Baseline regression** (`src/models/forecast.py`) — account ownership with optional mobile/4G covariates
- **Scenario forecasts** (`src/models/forecast_advanced.py`) — base / optimistic / pessimistic paths with CI bands; scenarios scale **growth and event effects**, not absolute levels
- **Event impact** (`src/models/event_impact.py`) — confidence- and magnitude-weighted association matrix with lag metadata
- **Backtesting** (`src/models/backtesting.py`) — expanding-window and leave-one-out tests with **MAE / RMSE / MAPE**
- **Sensitivity** (`src/models/sensitivity.py`) — one-at-a-time sweeps and tornado rankings
- **Reproducibility** — seeded RNG; covered by `tests/test_forecasting.py`
- **Dashboard** — scenarios, validation metrics, sensitivity charts, event matrix, downloads

## Setup

```bash
python -m pip install -r requirements.txt
```

Use a virtual environment if preferred:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

## Run the full pipeline

From the project root (`ethiopia-fi-forecast-task-1/`):

```bash
python -m src.run_pipeline
```

Or run modules individually:

```bash
python -m src.models.event_impact
python -m src.models.forecast
python -m src.models.forecast_advanced
python -m src.models.backtesting
python -m src.models.sensitivity
```

## Tests

```bash
python -m pytest -q
```

## Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at [http://localhost:8501](http://localhost:8501).

Generate forecast/validation artefacts with the pipeline before launching the dashboard.

## Data notes

- Enrichment provenance: `data/data_enrichment_log.md`
- Primary modelling file: `data/processed/ethiopia_fi_unified_data_enriched.csv`
- Optional wider unified export: `data/processed/ethiopia_fi_unified_data.xlsx - ethiopia_fi_unified_data.csv`
- Reference codes (if available): `data/raw/reference_codes.csv`

## Methodology (short)

1. Fit a linear trend on historical survey observations (Findex and related series).
2. Apply additive event boosts using impact-link magnitude, confidence, lag, and decay.
3. Build scenarios by scaling trend **change** (vs last observation) and event pass-through.
4. Validate with in-sample diagnostics and time-series backtests (MAE/RMSE/MAPE).
5. Stress-test assumptions with OAT sensitivity / tornado plots.

See `reports/forecast_summary.md`, `reports/backtest_validation.md`, and `reports/sensitivity_analysis.md` for detail.

## Notebooks

```bash
jupyter lab   # or: jupyter notebook
```

- `notebooks/eda_eth_fi.ipynb` — exploratory analysis
- `notebooks/forecasting_scenarios.ipynb` — scenario forecasts
- `notebooks/event_impact_modeling.ipynb` — event associations
- `notebooks/modeling_forecast.ipynb` — baseline modelling

## License

MIT
