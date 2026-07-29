"""Unit tests for forecast error metrics."""

import math

import numpy as np
import pytest

from src.models.metrics import mae, mape, rmse, summarize_errors


def test_mae_perfect():
    assert mae([1, 2, 3], [1, 2, 3]) == 0.0


def test_rmse_known():
    assert rmse([0, 0], [3, 4]) == pytest.approx(math.sqrt((9 + 16) / 2))


def test_mape_known():
    # mean(|10-11|/10, |20-18|/20) = mean(0.1, 0.1) = 0.1 -> 10%
    assert mape([10, 20], [11, 18]) == pytest.approx(10.0)


def test_mape_skips_zeros():
    assert mape([0, 10], [1, 12]) == pytest.approx(20.0)


def test_summarize_errors():
    stats = summarize_errors(np.array([10.0, 20.0]), np.array([12.0, 18.0]))
    assert stats['n'] == 2
    assert stats['mae'] == pytest.approx(2.0)
    assert stats['rmse'] == pytest.approx(math.sqrt(4.0))
    # mean(0.2, 0.1) * 100 = 15%
    assert stats['mape'] == pytest.approx(15.0)


def test_shape_mismatch():
    with pytest.raises(ValueError):
        mae([1, 2], [1])
