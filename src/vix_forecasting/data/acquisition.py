"""Download VIX data from Yahoo Finance."""
from pathlib import Path

import pandas as pd
import yfinance as yf


def download_vix(ticker: str, start_date: str) -> pd.DataFrame:
    """Pull full VIX history from yfinance starting from start_date.

    Returns a DataFrame with a DatetimeIndex and at minimum a 'Close' column.
    """
    raw = yf.download(ticker, start=start_date, auto_adjust=False, progress=False)
    if raw.empty:
        raise RuntimeError(f"yfinance returned no data for {ticker!r}")
    # Flatten MultiIndex columns produced by yfinance >= 0.2.x
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.index = pd.to_datetime(raw.index)
    raw.index.name = "Date"
    return raw


def validate_raw(df: pd.DataFrame) -> None:
    """Check for unexpected gaps and print a summary. Raises on critical issues."""
    n_rows = len(df)
    date_min = df.index.min().date()
    date_max = df.index.max().date()

    print(f"Rows      : {n_rows:,}")
    print(f"Date range: {date_min} to {date_max}")

    # Flag any NaN close prices
    n_missing = df["Close"].isna().sum()
    if n_missing:
        print(f"WARNING   : {n_missing} missing Close values")
    else:
        print("Missing   : none in Close")

    # Check for gaps larger than 5 calendar days (catches extended market closures
    # and data anomalies while ignoring normal weekends + single holidays)
    diffs = df.index.to_series().diff().dropna()
    large_gaps = diffs[diffs > pd.Timedelta(days=5)]
    if large_gaps.empty:
        print("Gaps      : none > 5 calendar days")
    else:
        print(f"Gaps > 5d : {len(large_gaps)} found")
        for date, gap in large_gaps.items():
            print(f"  {date.date()}  ({gap.days} days since previous observation)")

    if n_missing > 0:
        raise ValueError("Critical: missing Close values in raw data.")


def save_raw(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    print(f"Saved     : {path}  ({path.stat().st_size / 1024:.1f} KB)")
