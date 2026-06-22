"""ARIMA residual diagnostic tests and figures."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as scipy_stats
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import jarque_bera as sm_jarque_bera


def run_ljung_box(residuals: np.ndarray, lags: int = 20) -> dict:
    """Ljung-Box test for residual autocorrelation.

    H0: no autocorrelation up to lag `lags`. High p → residuals are white noise.
    """
    result = acorr_ljungbox(residuals, lags=[lags], return_df=True)
    stat = float(result["lb_stat"].iloc[0])
    pvalue = float(result["lb_pvalue"].iloc[0])
    return {
        "test": "Ljung-Box",
        "lags_tested": lags,
        "statistic": round(stat, 4),
        "p_value": round(pvalue, 4),
        "h0": "no autocorrelation",
        "conclusion": "white noise — residuals uncorrelated (fail to reject H0)"
        if pvalue >= 0.05
        else "autocorrelation detected in residuals (reject H0)",
    }


def run_jarque_bera(residuals: np.ndarray) -> dict:
    """Jarque-Bera normality test on residuals.

    H0: residuals are normally distributed. Low p → non-normal (fat tails / skew).
    """
    stat, pvalue, skew, excess_kurt = sm_jarque_bera(residuals)
    return {
        "test": "Jarque-Bera",
        "statistic": round(float(stat), 4),
        "p_value": round(float(pvalue), 4),
        "skewness": round(float(skew), 4),
        "excess_kurtosis": round(float(excess_kurt), 4),
        "h0": "normally distributed",
        "conclusion": "normal (fail to reject H0)"
        if pvalue >= 0.05
        else "non-normal — fat tails / skewness present (reject H0)",
    }


def run_arch_lm(residuals: np.ndarray, lags: int = 12) -> dict:
    """ARCH-LM test for heteroskedasticity in residuals.

    H0: no ARCH effects (constant variance). Low p → variance clustering present.
    """
    stat, pvalue, _, _ = het_arch(residuals, nlags=lags)
    return {
        "test": "ARCH-LM",
        "lags_tested": lags,
        "statistic": round(float(stat), 4),
        "p_value": round(float(pvalue), 4),
        "h0": "no ARCH effects (homoskedastic)",
        "conclusion": "homoskedastic (fail to reject H0)"
        if pvalue >= 0.05
        else "ARCH effects detected — variance clustering present (reject H0)",
    }


def plot_residual_qq(residuals: np.ndarray, save_path: Path | None = None) -> plt.Figure:
    """Q-Q plot of ARIMA residuals against a normal distribution."""
    fig, ax = plt.subplots(figsize=(6, 6))
    (osm, osr), (slope, intercept, _) = scipy_stats.probplot(residuals, dist="norm")
    ax.scatter(osm, osr, alpha=0.35, s=8, color="#2B6CB0", label="Residuals")
    x_line = np.array([osm[0], osm[-1]])
    ax.plot(x_line, slope * x_line + intercept, color="#E07070",
            linewidth=1.5, label="Normal reference line")
    ax.set_title("Q-Q Plot — ARIMA(1,0,2) Residuals vs. Normal", fontsize=12)
    ax.set_xlabel("Theoretical quantiles")
    ax.set_ylabel("Sample quantiles")
    ax.legend(fontsize=9)
    fig.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    return fig


def plot_residual_acf(
    residuals: np.ndarray,
    lags: int = 40,
    save_path: Path | None = None,
) -> plt.Figure:
    """ACF of ARIMA residuals to verify no remaining autocorrelation."""
    fig, ax = plt.subplots(figsize=(10, 4))
    plot_acf(residuals, lags=lags, ax=ax, color="#2B6CB0", alpha=0.05)
    ax.set_title("ACF — ARIMA(1,0,2) Residuals", fontsize=12)
    ax.set_xlabel("Lag")
    fig.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    return fig


def run_all(residuals: np.ndarray, lb_lags: int = 20, arch_lags: int = 12) -> dict:
    """Run all three diagnostic tests and return combined results.

    Returns nested sub-dicts per test plus flat top-level keys for JSON output:
    ljung_box_stat, ljung_box_pvalue, jarque_bera_stat, jarque_bera_pvalue,
    arch_lm_stat, arch_lm_pvalue.
    """
    lb = run_ljung_box(residuals, lags=lb_lags)
    jb = run_jarque_bera(residuals)
    arch = run_arch_lm(residuals, lags=arch_lags)
    return {
        "ljung_box": lb,
        "jarque_bera": jb,
        "arch_lm": arch,
        "ljung_box_stat": lb["statistic"],
        "ljung_box_pvalue": lb["p_value"],
        "jarque_bera_stat": jb["statistic"],
        "jarque_bera_pvalue": jb["p_value"],
        "arch_lm_stat": arch["statistic"],
        "arch_lm_pvalue": arch["p_value"],
    }
