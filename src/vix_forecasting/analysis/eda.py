"""EDA plotting helpers for VIX time series."""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

sns.set_theme(style="whitegrid", palette="muted")

# Approximate S&P 500 drawdown periods that produced elevated VIX regimes.
_REGIMES = [
    ("Dot-com bust",  "2000-03-24", "2002-10-09", "#E07070"),
    ("GFC",           "2007-10-09", "2009-03-09", "#E0A840"),
    ("COVID-19",      "2020-02-19", "2020-04-07", "#60B8A0"),
    ("2022 selloff",  "2022-01-03", "2022-12-28", "#9B7EC8"),
]


def plot_full_history(
    series: pd.Series,
    save_path: Path | None = None,
) -> plt.Figure:
    """Full VIX history with shaded volatility regimes."""
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(series.index, series.values, color="#2B6CB0", linewidth=0.8, label="VIX")

    for label, start, end, color in _REGIMES:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end),
                   alpha=0.18, color=color, label=label)

    ax.set_title("CBOE VIX — Full History (1990–present)", fontsize=13)
    ax.set_ylabel("VIX Level")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", fontsize=8, framealpha=0.8)
    ax.set_xlim(series.index[0], series.index[-1])
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_distribution(
    series: pd.Series,
    save_path: Path | None = None,
) -> plt.Figure:
    """Histogram + KDE of VIX levels, with percentile markers."""
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(series, bins=60, kde=True, color="#2B6CB0",
                 line_kws={"linewidth": 1.8}, ax=ax)

    for pct, ls in [(25, "--"), (50, "-"), (75, "--"), (90, ":")]:
        val = series.quantile(pct / 100)
        ax.axvline(val, color="#E07070", linestyle=ls, linewidth=1.2,
                   label=f"p{pct} = {val:.1f}")

    ax.set_title("VIX Level — Distribution (all trading days)", fontsize=13)
    ax.set_xlabel("VIX Level")
    ax.set_ylabel("Count")
    ax.legend(fontsize=8)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_rolling_volatility(
    series: pd.Series,
    window: int = 252,
    save_path: Path | None = None,
) -> plt.Figure:
    """Rolling 1-year std of VIX with the same regime shading as plot_full_history."""
    rolling_std = series.rolling(window).std()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(rolling_std.index, rolling_std.values,
            color="#2B6CB0", linewidth=0.9, label=f"Rolling {window}-day std")

    for label, start, end, color in _REGIMES:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end),
                   alpha=0.18, color=color, label=label)

    ax.set_title(f"VIX — Rolling 1-Year Volatility ({window}-day std)", fontsize=13)
    ax.set_ylabel("Std of VIX Level")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", fontsize=8, framealpha=0.8)
    ax.set_xlim(series.index[0], series.index[-1])
    fig.tight_layout()

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    return fig


def plot_acf_pacf(
    series: pd.Series,
    lags: int = 40,
    save_path: Path | None = None,
) -> plt.Figure:
    """ACF and PACF side by side."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4))
    plot_acf(series, lags=lags, ax=ax1, color="#2B6CB0", alpha=0.05)
    plot_pacf(series, lags=lags, ax=ax2, method="ywm",
              color="#2B6CB0", alpha=0.05)

    ax1.set_title("ACF — VIX Close")
    ax2.set_title("PACF — VIX Close")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig
