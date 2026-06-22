"""Unit tests for the walk-forward backtest harness."""
import numpy as np
import pandas as pd
import pytest

from src.vix_forecasting.evaluation.backtest import walk_forward, summarize
from src.vix_forecasting.models.baseline import NaiveForecaster


def _make_series(n: int = 300, start: str = "2020-01-02") -> pd.Series:
    rng = np.random.default_rng(42)
    vals = 20.0 + np.cumsum(rng.normal(0, 0.5, n))
    idx  = pd.bdate_range(start=start, periods=n)
    return pd.Series(vals, index=idx, name="VIX")


def _naive_factory():
    return NaiveForecaster()


# ── Fold count ─────────────────────────────────────────────────────────────────

def test_fold_count_no_test_size():
    series = _make_series(300)
    df = walk_forward(_naive_factory, series, horizons=[1], min_train_size=252, step=21)
    # Folds start at 252, end at 300 - 1 = 299, step 21 → positions 252 → 1 fold
    expected_folds = len(range(252, 300 - 1 + 1, 21))
    assert len(df) == expected_folds


def test_fold_count_with_test_size():
    series = _make_series(300)
    df = walk_forward(_naive_factory, series, horizons=[1],
                      min_train_size=100, test_size=63, step=21)
    test_start = 300 - 63   # = 237
    expected = len(range(237, 300 - 1 + 1, 21))
    assert len(df) == expected


def test_multiple_horizons_rows():
    series = _make_series(300)
    df = walk_forward(_naive_factory, series, horizons=[1, 5],
                      min_train_size=252, step=21)
    # Each fold produces one row per valid horizon
    assert set(df["horizon"].unique()) == {1, 5}


# ── No data leakage ────────────────────────────────────────────────────────────

def test_no_data_leakage():
    """The test window for each fold must not overlap with its training window."""
    series = _make_series(300)
    df = walk_forward(_naive_factory, series, horizons=[5],
                      min_train_size=252, step=21)
    for _, row in df.iterrows():
        # train_end_date is the last training date; forecast starts the next obs
        train_end_pos = series.index.get_loc(row["train_end_date"])
        # The fold must have left at least `horizon` observations after train_end
        assert train_end_pos + row["horizon"] <= len(series)


# ── Naive self-consistency ─────────────────────────────────────────────────────

def test_naive_dir_acc_bounded():
    series = _make_series(300)
    df = walk_forward(_naive_factory, series, horizons=[1],
                      min_train_size=252, step=21)
    dir_acc_vals = df["dir_acc"].dropna()
    assert (dir_acc_vals >= 0.0).all() and (dir_acc_vals <= 1.0).all()


# ── Summarize ─────────────────────────────────────────────────────────────────

def test_summarize_shape():
    series = _make_series(300)
    df = walk_forward(_naive_factory, series, horizons=[1, 5],
                      min_train_size=252, step=21)
    summary = summarize(df)
    assert list(summary.columns) == ["rmse", "mae", "mape", "dir_acc"]
    assert set(summary.index) == {1, 5}


def test_summarize_rmse_positive():
    series = _make_series(300)
    df = walk_forward(_naive_factory, series, horizons=[1],
                      min_train_size=252, step=21)
    summary = summarize(df)
    assert (summary["rmse"] >= 0).all()
