"""Prophet forecaster."""
import warnings

import numpy as np
import pandas as pd
from prophet import Prophet

from .base import BaseForecaster

SUPPORTED_HORIZONS = (1, 5, 21)


class ProphetForecaster(BaseForecaster):
    """Wraps Facebook Prophet for walk-forward evaluation.

    Weekly seasonality is enabled to cross-check the Phase 5 ARIMA finding
    that SMA(5) adds nothing. If Prophet's weekly component is also negligible
    in amplitude relative to series variance, the negative result is confirmed.

    Yearly seasonality is enabled — VIX has plausible annual patterns
    (earnings seasons, scheduled Fed meetings, year-end positioning).

    Additive mode: appropriate for a stationary series like VIX levels.
    """

    def __init__(
        self,
        weekly_seasonality: bool = True,
        yearly_seasonality: bool = True,
        seasonality_mode: str = "additive",
    ) -> None:
        self.weekly_seasonality = weekly_seasonality
        self.yearly_seasonality = yearly_seasonality
        self.seasonality_mode = seasonality_mode
        self._model: Prophet | None = None
        self._last_date: pd.Timestamp | None = None

    def fit(self, series: pd.Series) -> None:
        if len(series) == 0:
            raise ValueError("Cannot fit on an empty series.")
        df = pd.DataFrame({"ds": series.index, "y": series.values})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._model = Prophet(
                weekly_seasonality=self.weekly_seasonality,
                yearly_seasonality=self.yearly_seasonality,
                daily_seasonality=False,
                seasonality_mode=self.seasonality_mode,
            )
            self._model.fit(df)
        self._last_date = series.index[-1]

    def predict(self, horizon: int) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model has not been fitted yet.")
        if horizon not in SUPPORTED_HORIZONS:
            raise ValueError(f"horizon must be one of {SUPPORTED_HORIZONS}, got {horizon}.")
        # Generate business days (Mon–Fri) starting the day after the last
        # training observation. This approximates trading days closely enough
        # for a portfolio project; the actual exchange calendar differs only
        # on US market holidays (~9 days/year).
        future_dates = pd.bdate_range(
            start=self._last_date + pd.Timedelta(days=1),
            periods=horizon,
        )
        forecast = self._model.predict(pd.DataFrame({"ds": future_dates}))
        return forecast["yhat"].to_numpy()

    def seasonality_amplitudes(self) -> dict:
        """Return peak-to-trough amplitude of each seasonality component.

        Useful for checking whether a component is meaningful relative
        to the series standard deviation.
        """
        if self._model is None:
            raise RuntimeError("Model has not been fitted yet.")
        components = {}
        for name, s in self._model.seasonalities.items():
            period = s["period"]
            t = np.linspace(0, period, 200)
            df_t = pd.DataFrame({"ds": pd.date_range("2020-01-01", periods=200, freq="D")})
            vals = self._model.predict_seasonal_components(df_t)[name].values
            components[name] = round(float(vals.max() - vals.min()), 4)
        return components
