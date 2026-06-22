"""ARIMA / SARIMA forecaster."""
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .base import BaseForecaster

SUPPORTED_HORIZONS = (1, 5, 21)


def select_order(
    series: pd.Series,
    p_values: tuple = (1, 2, 3),
    q_values: tuple = (0, 1, 2),
    d: int = 0,
    seasonal: bool = False,
    m: int = 5,
    P_values: tuple = (0, 1),
    Q_values: tuple = (0, 1),
) -> pd.DataFrame:
    """Grid-search ARIMA(p,d,q)[× seasonal(P,D,Q,m)] orders by AIC.

    Returns a DataFrame sorted by AIC with columns:
    order, seasonal_order, aic, bic, converged.

    d is fixed at the caller's chosen integration order.
    Seasonal D is fixed at 0 (we test the seasonal AR/MA terms only).
    """
    rows = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for p in p_values:
            for q in q_values:
                if p == 0 and q == 0:
                    continue
                if seasonal:
                    for P in P_values:
                        for Q in Q_values:
                            _fit_candidate(series, (p, d, q), (P, 0, Q, m), rows)
                else:
                    _fit_candidate(series, (p, d, q), (0, 0, 0, 0), rows)

    df = pd.DataFrame(rows).sort_values("aic").reset_index(drop=True)
    return df


def _fit_candidate(
    series: pd.Series,
    order: tuple,
    seasonal_order: tuple,
    rows: list,
) -> None:
    try:
        res = SARIMAX(
            series,
            order=order,
            seasonal_order=seasonal_order,
            trend="c",
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit(disp=False)
        rows.append(
            {
                "order": order,
                "seasonal_order": seasonal_order if seasonal_order != (0, 0, 0, 0) else None,
                "aic": round(res.aic, 2),
                "bic": round(res.bic, 2),
                "converged": res.mle_retvals.get("converged", True),
            }
        )
    except Exception:
        pass


class ARIMAForecaster(BaseForecaster):
    """Wraps statsmodels SARIMAX for walk-forward evaluation.

    Order selection (Phase 5 analysis) on a 2,000-obs window identified
    ARIMA(1,0,2) as the best converged non-seasonal model (AIC=8483).
    Adding SMA(1) at lag 5 improved the selection-window AIC by 16.6
    points, but when the full series (9,183 obs) is used for fitting,
    the SMA(5) coefficient is 0.0005 with p=0.923 — effectively zero.
    The weekly seasonal term is a spurious artefact of the 8-year window,
    not a genuine structural feature of VIX. Documented negative result.

    Final model: ARIMA(1,0,2), d=0 (stationarity confirmed in Phase 3).
    AR(1)≈0.984 confirms the near-unit-root persistence seen in the ACF.

    Default order reflects that finding; override for ablation studies.
    """

    def __init__(
        self,
        order: tuple = (1, 0, 2),
        seasonal_order: tuple = (0, 0, 0, 0),
    ) -> None:
        self.order = order
        self.seasonal_order = seasonal_order
        self._result = None

    def fit(self, series: pd.Series) -> None:
        if len(series) == 0:
            raise ValueError("Cannot fit on an empty series.")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._result = SARIMAX(
                series,
                order=self.order,
                seasonal_order=self.seasonal_order,
                trend="c",
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)

    def predict(self, horizon: int) -> np.ndarray:
        if self._result is None:
            raise RuntimeError("Model has not been fitted yet.")
        if horizon not in SUPPORTED_HORIZONS:
            raise ValueError(f"horizon must be one of {SUPPORTED_HORIZONS}, got {horizon}.")
        return self._result.forecast(steps=horizon).to_numpy()

    def get_residuals(self) -> np.ndarray:
        """Return in-sample residuals from the last fit."""
        if self._result is None:
            raise RuntimeError("Model has not been fitted yet.")
        return self._result.resid.to_numpy()


class LogARIMAForecaster(BaseForecaster):
    """ARIMA(1,0,2) fitted on log(VIX); predictions exponentiated to original scale.

    Non-negativity is guaranteed by construction (exp is always > 0).
    Same order as the level-scale model for a fair apples-to-apples comparison.
    """

    def __init__(
        self,
        order: tuple = (1, 0, 2),
        seasonal_order: tuple = (0, 0, 0, 0),
    ) -> None:
        self._inner = ARIMAForecaster(order=order, seasonal_order=seasonal_order)

    def fit(self, series: pd.Series) -> None:
        if len(series) == 0:
            raise ValueError("Cannot fit on an empty series.")
        log_series = pd.Series(
            np.log(series.values), index=series.index, name=series.name
        )
        self._inner.fit(log_series)

    def predict(self, horizon: int) -> np.ndarray:
        return np.exp(self._inner.predict(horizon))

    def get_log_residuals(self) -> np.ndarray:
        """Residuals from the log-scale fit (not back-transformed)."""
        return self._inner.get_residuals()
