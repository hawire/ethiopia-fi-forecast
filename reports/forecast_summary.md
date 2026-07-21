# Forecast Summary: Ethiopia Financial Inclusion 2025-2027

## Overview
This report presents scenario-based forecasts for Ethiopia's financial inclusion indicators: Account Ownership Rate (Access) and Digital Payment Adoption Rate (Usage), spanning 2025–2027.

## Methodology
- **Baseline model:** Linear trend fitted to historical observations (2010–2024) with confidence intervals derived from residual uncertainty.
- **Event augmentation:** Event-driven additive impulses (e.g., Telebirr rollout lag=1yr, effect=0.05) applied to baseline.
- **Scenarios:** Three demand scenarios (pessimistic, base, optimistic) applied via multiplicative scaling factors:
  - Pessimistic: 0.7× baseline + event effect (regulatory delays, limited investment)
  - Base: 1.0× baseline + event effect (current trajectory continuation)
  - Optimistic: 1.3× baseline + event effect (accelerated policy/tech adoption)

## Key Findings

### Account Ownership Rate (Access)
| Scenario | 2025 | 2026 | 2027 | Notes |
|----------|------|------|------|-------|
| Pessimistic | 24–28% | 26–30% | 28–32% | Macro headwinds, slow agent growth |
| Base | 34–38% | 36–40% | 38–42% | Continued telecom/digital ID integration |
| Optimistic | 44–48% | 46–50% | 48–52% | Accelerated fintech ecosystem, gov't support |

**Drivers:** Telecom subscriber expansion (agent density), digital ID adoption, regulatory reforms enabling agent banking, mobile money interoperability.

### Digital Payment Adoption Rate (Usage)
| Scenario | 2025 | 2026 | 2027 | Notes |
|----------|------|------|------|-------|
| Pessimistic | 7–9% | 8–10% | 9–11% | Slow merchant uptake, high transaction costs |
| Base | 10–12% | 12–14% | 14–16% | Telebirr/M-Pesa expansion, incremental merchant enablement |
| Optimistic | 13–16% | 16–19% | 19–22% | Rapid digital wallet adoption, gov't-backed incentives |

**Drivers:** Mobile money service expansion (Telebirr, M-Pesa), merchant acceptance infrastructure, interoperability standards, consumer confidence, transaction fee rationalization.

## Confidence Intervals
90% confidence bands (5th and 95th percentiles) reflect historical residual variance and are widened for scenarios reflecting policy/tech uncertainty.

## Limitations & Sensitivity
- **Sparse Findex data:** Limited direct observations; proxy indicators used (e.g., mobile money accounts as proxy for digital payment behavior).
- **Event lag uncertainty:** Impact timing and magnitude of Telebirr/M-Pesa estimated heuristically; validation ongoing.
- **Policy shocks:** Unforeseen regulatory changes (e.g., mobile money licensing restrictions) not modeled.
- **Macro dependencies:** Currency devaluation, inflation not explicitly modeled; assume baseline macro stability.

## Recommendations
1. **Monitor lagging indicators:** agent growth, merchant enablement, transaction volume trends; update event lags if observed outcomes diverge.
2. **Increase data collection:** annual Findex or alternative surveys to reduce forecast variance.
3. **Scenario stress-testing:** conduct sensitivity on event magnitudes and policy assumptions.

## Next Steps
- Integrate with Streamlit dashboard for interactive scenario exploration.
- Compare forecasts against National Bank of Ethiopia & telecoms industry reports for triangulation.
