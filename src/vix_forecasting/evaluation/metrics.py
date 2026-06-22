"""Forecast evaluation metrics."""
import numpy as np


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean absolute percentage error. Assumes actual is strictly positive."""
    return float(np.mean(np.abs((actual - predicted) / actual)) * 100)


def directional_accuracy(
    actual: np.ndarray,
    predicted: np.ndarray,
    last_obs: float,
) -> float:
    """Fraction of steps where the predicted direction of change matches actual.

    Direction is measured step-by-step: at each step i, we compare whether
    actual[i] moved up/down vs the previous actual value (actual[i-1], with
    actual[-1] = last_obs), and whether predicted[i] moved in the same
    direction vs the previous predicted value (predicted[i-1] = last_obs).

    Steps where actual is exactly flat (zero change) are excluded from the
    denominator — they carry no directional information.
    """
    all_actual = np.concatenate([[last_obs], actual])
    all_pred   = np.concatenate([[last_obs], predicted])
    actual_dirs = np.sign(np.diff(all_actual))
    pred_dirs   = np.sign(np.diff(all_pred))
    mask = actual_dirs != 0
    if mask.sum() == 0:
        return float("nan")
    return float((actual_dirs[mask] == pred_dirs[mask]).mean())


def compute_all(
    actual: np.ndarray,
    predicted: np.ndarray,
    last_obs: float,
) -> dict:
    """Compute all four metrics and return as a dict."""
    return {
        "rmse":    rmse(actual, predicted),
        "mae":     mae(actual, predicted),
        "mape":    mape(actual, predicted),
        "dir_acc": directional_accuracy(actual, predicted, last_obs),
    }
