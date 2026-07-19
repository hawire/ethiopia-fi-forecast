# Data Enrichment Log

Collected by: Selam Analytics (analyst)
Collection date: 2026-07-19

## Summary of Additions

1. Observations added
- `Account ownership` (2021, 2024) — World Bank Global Findex (survey figures). Source: https://globalfindex.worldbank.org. Confidence: high.
- `Digital payment adoption` (2024) — Global Findex. Source: https://globalfindex.worldbank.org. Confidence: high.
- `Active mobile subscribers` (2024) — GSMA Intelligence estimate of active SIMs (65M). Source: https://www.gsmaintelligence.com. Confidence: medium.
- `4G population coverage` (2024) — ITU/GSMA coverage estimate (~45%). Source: https://www.itu.int. Confidence: medium.
- `Agent density` (2023) — National Bank of Ethiopia estimate (~8 agents per 100k). Source: https://nbe.gov.et. Confidence: medium.

2. Events added
- `Telebirr national launch` — May 15, 2021. Source: Telebirr/press release. Confidence: medium.
- `Safaricom market entry` — Aug 1, 2022. Source: press coverage. Confidence: medium.
- `M-Pesa Ethiopia launch` — Aug 15, 2023. Source: M-Pesa press releases. Confidence: medium.

3. Impact links added
- Telebirr -> Digital Payments: impact_magnitude=moderate, lag_months=6, evidence_basis="Operator reports; market analysis".
- M-Pesa -> Mobile Subscribers: impact_magnitude=high, lag_months=3, evidence_basis="Operator reports; press coverage".

## For each new record

- `Account ownership (2024)`
  - source_url: https://globalfindex.worldbank.org
  - original_text: "49% of adults reported having an account (2024 Global Findex)"
  - confidence: high
  - collected_by: Selam Analytics
  - collection_date: 2026-07-19
  - notes: Critical Findex baseline for Access forecasts.

- `Active mobile subscribers (2024)`
  - source_url: https://www.gsmaintelligence.com
  - original_text: "65 million active SIMs (GSMA 2024 estimate)"
  - confidence: medium
  - collected_by: Selam Analytics
  - collection_date: 2026-07-19
  - notes: Useful proxy for potential mobile-money reach.

## Next steps recommended
- Validate agent density and 4G coverage figures with NBE and GSMA detailed reports.
- (Task) Add regional and gender-disaggregated observations if Findex microdata accessible.
- Create `task-1` Git branch, commit `data/processed/ethiopia_fi_unified_data_enriched.csv`, and open PR merging into `main`.
