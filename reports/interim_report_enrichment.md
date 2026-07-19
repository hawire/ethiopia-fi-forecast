# Interim Report — Data Enrichment

## Summary

This report summarizes additions to the Ethiopia financial inclusion dataset.

### Additions
- Added Findex observations for Account Ownership (2021, 2024) and Digital Payment Adoption (2024).
- Added infrastructure proxies: active mobile subscribers (GSMA), 4G coverage (ITU/GSMA), agent density (NBE).
- Cataloged events: Telebirr launch (May 2021), Safaricom entry (Aug 2022), M-Pesa launch (Aug 2023).
- Added impact_links connecting Telebirr and M-Pesa launches to usage/subscriber indicators.

### Rationale
- Infrastructure and operator events are strong proximate drivers of digital payment adoption.
- Agent networks and connectivity provide leading signals for inclusion changes.

### Data Limitations
- Many figures are national aggregates; regional and gender disaggregations missing.
- Some event dates are approximated from press coverage; primary sources should be confirmed.

### Files Added
- [data/processed/ethiopia_fi_unified_data_enriched.csv](data/processed/ethiopia_fi_unified_data_enriched.csv)
- [data/data_enrichment_log.md](data/data_enrichment_log.md)

