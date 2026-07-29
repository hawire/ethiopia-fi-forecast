# Forecast Summary: Ethiopia Financial Inclusion 2025-2027

## Overview
Scenario-based forecasts for Ethiopia's financial inclusion indicators: Account Ownership Rate (Access) and Digital Payment Adoption Rate (Usage), spanning 2025–2027.

## Methodology
- **Baseline model:** Linear trend fitted to historical observations (Findex 2014–2024 where available) with confidence intervals from residual uncertainty (seeded sampling for reproducibility).
- **Event augmentation:** Additive impulses from structured impact links (magnitude × confidence blend, lag in months, decay by confidence). Example: Telebirr → digital payments (moderate, ~6 month lag).
- **Scenarios:** Three demand scenarios applied via **growth and event scaling** (not crude multiplication of absolute levels):

| Scenario | Growth scale | Event scale | Residual scale | Interpretation |
|----------|--------------|-------------|----------------|----------------|
| Pessimistic | 0.6× | 0.5× | 1.3× | Slower adoption, weaker event pass-through |
| Base | 1.0× | 1.0× | 1.0× | Estimated trend + calibrated events |
| Optimistic | 1.4× | 1.5× | 1.2× | Faster adoption, stronger event effects |

Level construction: `forecast = last_obs + growth_scale × (trend − last_obs) + event_scale × boost`.

A legacy absolute-level scaler (`scenario_scaling`) remains available for backward compatibility with earlier notebooks.

## Validation
- **In-sample diagnostics:** MAE, RMSE, MAPE, R² on fitted trends (`data/processed/model_validation_metrics.csv`).
- **Backtesting:** Expanding-window and leave-one-out linear-trend forecasts (`data/processed/backtest_metrics.csv`, `reports/backtest_validation.md`).
- **Sensitivity:** One-at-a-time sweeps of growth/event/lag/decay/residual assumptions with tornado rankings (`reports/sensitivity_analysis.md`).

Sparse Findex cadence means fold counts are small; treat backtest scores as directional, not definitive.

## Key Findings

### Account Ownership Rate (Access)
Historical path roughly 22% (2014) → 35% (2017) → 46% (2021) → 49% (2024). Base scenario continues modest growth with a small event contribution; optimistic/pessimistic bands widen via growth and event scales.

**Drivers:** Telecom expansion, digital ID, agent banking reforms, mobile money interoperability.

### Digital Payment Adoption Rate (Usage)
Observations around 19% (2021) → 35% (2024). Faster trend than account ownership; event boosts (e.g. Telebirr) matter more for near-term levels.

**Drivers:** Telebirr/M-Pesa expansion, merchant acceptance, interoperability, fee rationalization.

## Confidence Intervals
90% bands (5th–95th percentile) reflect residual variance scaled by scenario residual factors.

## Limitations & Sensitivity
- Sparse survey points limit out-of-sample folds.
- Event magnitudes remain partially heuristic even after magnitude/confidence weighting.
- Unmodelled macro shocks (FX, inflation) can dominate near-term outcomes.
- See tornado charts for which assumptions move 2027 point forecasts most.

## Recommendations
1. Refresh Findex/operator series annually and re-run `python -m src.run_pipeline`.
2. Re-estimate event lags when transaction/agent series diverge from forecasts.
3. Use sensitivity rankings to prioritise assumption research (growth vs events).

## How to reproduce
```bash
pip install -r requirements.txt
python -m src.run_pipeline
python -m pytest -q
streamlit run dashboard/app.py
```
