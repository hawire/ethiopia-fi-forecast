# Ethiopia Financial Inclusion Forecast Dashboard

An interactive Streamlit dashboard for exploring financial inclusion scenarios in Ethiopia for 2025–2027.

## Features

- **Scenario Comparison:** View and compare base, optimistic, and pessimistic forecasts side-by-side.
- **Uncertainty Bands:** 90% confidence intervals (5th–95th percentile) shown for all forecasts.
- **Key Indicators:**
  - Account Ownership Rate (Access)
  - Digital Payment Adoption Rate (Usage)
- **Event Impact Matrix:** Visual heatmap showing relationship between events and indicators.
- **Data Download:** Export forecast CSV for further analysis.
- **Methodology:** View forecast assumptions, limitations, and data quality notes.

## Installation

### Prerequisites
- Python 3.8+
- Virtual environment (optional but recommended)

### Setup

1. **Clone and navigate to repository:**
   ```bash
   git clone https://github.com/hawire/ethiopia-fi-forecast.git
   cd ethiopia-fi-forecast
   ```

2. **Create virtual environment (optional):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Dashboard

### From project root:
```bash
streamlit run dashboard/app.py
```

The dashboard will open in your default browser at `http://localhost:8501`.

### Customize port (optional):
```bash
streamlit run dashboard/app.py --server.port 8502
```

## Data Inputs

The dashboard reads from:
- `data/processed/forecasts_access_usage_2025_2027.csv` — Forecast results
- `data/processed/ethiopia_fi_unified_data_enriched.csv` — Enriched observations and events
- `reports/figures/event_indicator_matrix.png` — Event impact heatmap
- `reports/forecast_summary.md` — Methodology documentation

## File Structure

```
dashboard/
├── app.py              # Main Streamlit application
└── README.md           # This file
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
- Ensure requirements.txt is installed: `pip install -r requirements.txt`

### "FileNotFoundError: Forecast data not found"
- Run the forecasting script first: `python -c "import sys; sys.path.insert(0, '.'); from src.models.forecast_advanced import main; main()"`

### Dashboard won't open
- Try explicitly specifying the port: `streamlit run dashboard/app.py --server.port 8501`
- Check firewall settings if running remotely.

## Usage Tips

1. **Select scenarios** in the left sidebar to focus on specific forecasts (e.g., just "base" and "optimistic").
2. **Hover over charts** for interactive tooltips showing exact values and confidence bands.
3. **Download data** for integration with external tools (Excel, Python, R, etc.).
4. **Read methodology** to understand assumptions, limitations, and data quality caveats.

## Future Enhancements

- Dynamic scenario weighting (allow users to assign probabilities to outcomes)
- Sensitivity analysis dashboard (vary key assumptions)
- Historical data comparison with international benchmarks
- Real-time data feeds from National Bank of Ethiopia / telecom operators

## Contact & Support

For issues, suggestions, or questions, please open an issue on GitHub.

---

**Version:** 1.0  
**Created:** 2026-07-21  
**License:** MIT
