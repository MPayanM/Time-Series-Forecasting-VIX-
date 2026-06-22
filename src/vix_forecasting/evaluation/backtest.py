"""Walk-forward (expanding-window) backtest harness."""
from __future__ import annotations

from typing import Callable

import pandas as pd
import numpy as np

from ..models.base import BaseForecaster
from .metrics import compute_all


def walk_forward(
    model_factory: Callable[[], BaseForecaster],
    series: pd.Series,
    horizons: tuple | list,
    min_train_size: int,
    test_size: int | None = None,
    step: int = 21,
) -> pd.DataFrame:
    """Expanding-window walk-forward validation.

    For each fold the model is re-fitted from scratch on all data up to that
    point, then evaluated against the next `horizon` observations — one fit
    per fold, predictions generated for every requested horizon.

    Args:
        model_factory: Zero-argument callable returning a fresh model instance.
        series:        Full historical series (DatetimeIndex).
        horizons:      Forecast horizons to evaluate (e.g. [1, 5, 21]).
        min_train_size: Minimum number of observations required before the
                       first forecast. Defines where the test period begins
                       when test_size is None.
        test_size:     If given, only the *last* test_size observations are
                       used as the test period (the remainder is always in
                       train). Speeds up the run by limiting fold count.
        step:          Number of observations to advance between folds.

    Returns:
        DataFrame with one row per (fold, horizon) and columns:
        fold, train_end_date, horizon, last_obs, rmse, mae, mape, dir_acc.
    """
    n = len(series)
    test_start = (n - test_size) if test_size is not None else min_train_size
    test_start = max(test_start, min_train_size)

    fold_starts = range(test_start, n - max(horizons) + 1, step)
    if len(fold_starts) == 0:
        raise ValueError("No folds generated. Reduce test_size or horizons.")

    records = []
    for fold_idx, t in enumerate(fold_starts):
        train   = series.iloc[:t]
        last_obs = float(train.iloc[-1])

        model = model_factory()
        model.fit(train)

        for h in horizons:
            if t + h > n:
                continue
            actual    = series.iloc[t : t + h].to_numpy(dtype=float)
            predicted = model.predict(h).astype(float)
            m = compute_all(actual, predicted, last_obs)
            records.append(
                {
                    "fold":           fold_idx,
                    "train_end_date": train.index[-1],
                    "horizon":        h,
                    "last_obs":       last_obs,
                    **m,
                }
            )

    return pd.DataFrame(records)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-fold metrics into a summary table.

    Returns mean RMSE, MAE, MAPE, and directional accuracy per horizon,
    indexed by horizon.
    """
    return (
        results
        .groupby("horizon")[["rmse", "mae", "mape", "dir_acc"]]
        .mean()
        .round(4)
    )
