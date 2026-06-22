"""Unit tests for evaluation metrics."""
import numpy as np
import pytest

from src.vix_forecasting.evaluation.metrics import (
    rmse, mae, mape, directional_accuracy, compute_all,
)


def test_rmse_perfect():
    a = np.array([1.0, 2.0, 3.0])
    assert rmse(a, a) == 0.0


def test_rmse_known():
    actual    = np.array([2.0, 4.0])
    predicted = np.array([1.0, 3.0])
    assert rmse(actual, predicted) == pytest.approx(1.0)


def test_mae_known():
    actual    = np.array([1.0, 2.0, 3.0])
    predicted = np.array([2.0, 3.0, 4.0])
    assert mae(actual, predicted) == pytest.approx(1.0)


def test_mae_perfect():
    a = np.array([10.0, 20.0])
    assert mae(a, a) == 0.0


def test_mape_known():
    actual    = np.array([100.0, 200.0])
    predicted = np.array([110.0, 180.0])
    # |100-110|/100 = 0.10, |200-180|/200 = 0.10 → MAPE = 10%
    assert mape(actual, predicted) == pytest.approx(10.0)


def test_mape_perfect():
    a = np.array([15.0, 20.0])
    assert mape(a, a) == pytest.approx(0.0)


def test_directional_accuracy_all_correct():
    # Both go up: actual [10→12→14], predicted [10→11→13]
    actual    = np.array([12.0, 14.0])
    predicted = np.array([11.0, 13.0])
    assert directional_accuracy(actual, predicted, last_obs=10.0) == pytest.approx(1.0)


def test_directional_accuracy_all_wrong():
    # Actual goes up, predicted goes down every step
    actual    = np.array([12.0, 14.0])
    predicted = np.array([9.0,  8.0])
    assert directional_accuracy(actual, predicted, last_obs=10.0) == pytest.approx(0.0)


def test_directional_accuracy_half():
    # Step 1: actual up (10→12), predicted up (10→11) → correct
    # Step 2: actual up (12→14), predicted down (11→9) → wrong
    actual    = np.array([12.0, 14.0])
    predicted = np.array([11.0,  9.0])
    assert directional_accuracy(actual, predicted, last_obs=10.0) == pytest.approx(0.5)


def test_directional_accuracy_skips_flat_actual():
    # Step 1: actual flat (excluded), step 2: actual up → correct
    actual    = np.array([10.0, 12.0])  # flat then up
    predicted = np.array([11.0, 13.0])  # up then up
    # Only step 2 counts: actual 10→12 up, predicted 11→13 up → correct
    assert directional_accuracy(actual, predicted, last_obs=10.0) == pytest.approx(1.0)


def test_compute_all_keys():
    a = np.array([20.0, 21.0, 22.0])
    p = np.array([19.5, 20.5, 21.5])
    result = compute_all(a, p, last_obs=19.0)
    assert set(result.keys()) == {"rmse", "mae", "mape", "dir_acc"}
    assert all(isinstance(v, float) for v in result.values())
