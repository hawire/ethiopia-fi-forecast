# Ethiopia Financial Inclusion Forecast

This repository contains work-in-progress for forecasting Ethiopia's financial inclusion indicators (Access and Usage) using a unified dataset, exploratory analysis, and modeling.

Key folders:
- `data/processed/` — enriched dataset used for EDA and modeling
- `notebooks/` — EDA notebook
- `reports/` — interim reports for Task 1 and Task 2

Notes and how to run:
- Enrichment provenance: see `data/data_enrichment_log.md` for sources and notes on added records.
- Reference codes (if available) should be placed at `data/raw/reference_codes.csv` and will be read by the EDA notebook.
- To run notebooks locally: install requirements and start Jupyter:

```bash
python -m pip install -r requirements.txt --user
jupyter lab  # or jupyter notebook
```

Run `notebooks/eda_eth_fi.ipynb` to reproduce EDA figures (saved to `reports/figures/`).

