"""Abstract base class that all forecasting models must implement."""
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class BaseForecaster(ABC):
    @abstractmethod
    def fit(self, series: pd.Series) -> None:
        """Fit the model on a training series."""

    @abstractmethod
    def predict(self, horizon: int) -> np.ndarray:
        """Return point forecasts for the next `horizon` steps."""
