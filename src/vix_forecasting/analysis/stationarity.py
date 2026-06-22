"""ADF and KPSS stationarity tests."""
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss


def run_adf(series: pd.Series, regression: str = "c") -> dict:
    """ADF test. H0: unit root (non-stationary). Low p → reject H0 → stationary.

    regression: 'c' (constant), 'ct' (constant + trend), 'n' (none).
    Lag selection uses AIC by default (maxlag=None → statsmodels auto).
    """
    stat, p, lags_used, _, crit, _ = adfuller(series.dropna(), regression=regression, autolag="AIC")
    return {
        "test": "ADF",
        "statistic": round(stat, 4),
        "p_value": round(p, 4),
        "lags_used": lags_used,
        "critical_values": {k: round(v, 4) for k, v in crit.items()},
        "h0": "unit root (non-stationary)",
        "conclusion": "stationary" if p < 0.05 else "non-stationary (fail to reject H0)",
    }


def run_kpss(series: pd.Series, regression: str = "c") -> dict:
    """KPSS test. H0: stationary. Low p → reject H0 → non-stationary.

    regression: 'c' (level stationarity), 'ct' (trend stationarity).
    """
    stat, p, lags_used, crit = kpss(series.dropna(), regression=regression, nlags="auto")
    return {
        "test": "KPSS",
        "statistic": round(stat, 4),
        "p_value": round(p, 4),
        "lags_used": lags_used,
        "critical_values": {k: round(v, 4) for k, v in crit.items()},
        "h0": "stationary",
        "conclusion": "non-stationary (reject H0)" if p < 0.05 else "stationary (fail to reject H0)",
    }


def print_result(result: dict) -> None:
    print(f"  Test      : {result['test']}")
    print(f"  H0        : {result['h0']}")
    print(f"  Statistic : {result['statistic']}")
    print(f"  p-value   : {result['p_value']}")
    print(f"  Crit vals : {result['critical_values']}")
    print(f"  --> {result['conclusion']}")
