"""Naive persistence (random-walk) baseline forecaster."""
import numpy as np
import pandas as pd

from .base import BaseForecaster

SUPPORTED_HORIZONS = (1, 5, 21)


class NaiveForecaster(BaseForecaster):
    """Repeats the last observed value for all forecast steps.

    This is the random-walk forecast: the best guess for any future value
    is the most recent observation. It is the floor every other model must
    beat to be worth deploying.

    Supports horizons 1, 5, and 21 trading days.
    """

    def __init__(self) -> None:
        self._last_value: float | None = None

    def fit(self, series: pd.Series) -> None:
        if len(series) == 0:
            raise ValueError("Cannot fit on an empty series.")
        self._last_value = float(series.iloc[-1])

    def predict(self, horizon: int) -> np.ndarray:
        if self._last_value is None:
            raise RuntimeError("Model has not been fitted yet.")
        if horizon not in SUPPORTED_HORIZONS:
            raise ValueError(f"horizon must be one of {SUPPORTED_HORIZONS}, got {horizon}.")
        return np.full(horizon, self._last_value)
