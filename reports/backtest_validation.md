# Forecast Backtesting & Validation

Expanding-window and leave-one-out linear-trend backtests with MAE / RMSE / MAPE.

## Metric summary

|   n |       mae |      rmse |      mape | indicator   | method           | status            |     slope |   intercept |         r2 |
|----:|----------:|----------:|----------:|:------------|:-----------------|:------------------|----------:|------------:|-----------:|
|   2 |   7.13964 |   7.18502 |  14.9922  | access      | expanding_window | ok                | nan       |      nan    | nan        |
|   4 |   5.75436 |   6.12106 |  17.4333  | access      | leave_one_out    | ok                | nan       |      nan    | nan        |
|   4 |   2.5     |   2.50086 |   7.22451 | access      | in_sample_fit    | ok                |   2.7069  |    -5427.22 |   0.944406 |
|   0 | nan       | nan       | nan       | usage       | expanding_window | insufficient_data | nan       |      nan    | nan        |
|   0 | nan       | nan       | nan       | usage       | leave_one_out    | insufficient_data | nan       |      nan    | nan        |
|   2 |   0       |   0       |   0       | usage       | in_sample_fit    | ok                |   5.33333 |   -10759.7  |   1        |

## Notes

- Sparse survey cadence (Findex) limits fold count; metrics should be interpreted cautiously.
- `in_sample_fit` is diagnostic only and is not an out-of-sample score.
