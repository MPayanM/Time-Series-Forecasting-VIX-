"""Clean and index the raw VIX series for modeling."""
from pathlib import Path

import pandas as pd


def load_raw(path: Path) -> pd.DataFrame:
    """Load the raw CSV saved by acquisition.py."""
    return pd.read_csv(path, index_col="Date", parse_dates=True)


def build_series(df: pd.DataFrame) -> pd.Series:
    """Return a DatetimeIndex'd pd.Series of daily VIX Close prices.

    No reindexing to a business-day calendar is performed. The source data
    from yfinance already contains only actual trading days, so absent dates
    are non-trading days (weekends, US holidays) and should remain absent.
    The one known multi-day gap (2001-09-10 to 2001-09-17) is a documented
    market closure after 9/11 — not a data anomaly — and is left as-is.

    We use Close as the canonical price. For a computed index like VIX,
    OHLC all derive from the same intraday calculation; Close is the
    standard reference used in the literature.
    """
    series = df["Close"].dropna().copy()
    series.name = "VIX"
    series.index.name = "Date"
    return series
