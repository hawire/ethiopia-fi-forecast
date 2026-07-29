"""Error metrics for forecast validation (MAE, RMSE, MAPE)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _as_arrays(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float).ravel()
    y_pred = np.asarray(y_pred, dtype=float).ravel()
    if y_true.shape != y_pred.shape:
        raise ValueError(f'Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}')
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    return y_true[mask], y_pred[mask]


def mae(y_true, y_pred) -> float:
    """Mean Absolute Error."""
    yt, yp = _as_arrays(y_true, y_pred)
    if len(yt) == 0:
        return float('nan')
    return float(np.mean(np.abs(yt - yp)))


def rmse(y_true, y_pred) -> float:
    """Root Mean Squared Error."""
    yt, yp = _as_arrays(y_true, y_pred)
    if len(yt) == 0:
        return float('nan')
    return float(np.sqrt(np.mean((yt - yp) ** 2)))


def mape(y_true, y_pred, epsilon: float = 1e-8) -> float:
    """Mean Absolute Percentage Error (percent units).

    Zero/near-zero actuals are skipped to avoid division blow-ups.
    """
    yt, yp = _as_arrays(y_true, y_pred)
    if len(yt) == 0:
        return float('nan')
    nonzero = np.abs(yt) > epsilon
    if not np.any(nonzero):
        return float('nan')
    return float(np.mean(np.abs((yt[nonzero] - yp[nonzero]) / yt[nonzero])) * 100.0)


def summarize_errors(y_true, y_pred) -> dict:
    """Return MAE, RMSE, MAPE and sample size for a prediction set."""
    yt, yp = _as_arrays(y_true, y_pred)
    return {
        'n': int(len(yt)),
        'mae': mae(yt, yp),
        'rmse': rmse(yt, yp),
        'mape': mape(yt, yp),
    }


def metrics_frame(rows: list[dict]) -> pd.DataFrame:
    """Build a tidy DataFrame from a list of metric dicts."""
    return pd.DataFrame(rows)
