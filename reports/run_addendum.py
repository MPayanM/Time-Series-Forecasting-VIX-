"""Addendum runner: residual diagnostics, log-VIX robustness, rolling volatility.

Outputs
-------
figures/arima_residual_qq.png
figures/arima_residual_acf.png
figures/vix_rolling_volatility_by_year.png
outputs/diagnostics/residual_diagnostics.json
outputs/predictions/backtest_summary_log_vix.csv
"""
import sys, json, warnings, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import matplotlib; matplotlib.use("Agg")
import pandas as pd
import numpy as np

from src.vix_forecasting.data.preprocessing import load_raw, build_series
from src.vix_forecasting.models.arima import ARIMAForecaster, LogARIMAForecaster
from src.vix_forecasting.analysis.diagnostics import (
    run_all, plot_residual_qq, plot_residual_acf,
)
from src.vix_forecasting.analysis.eda import plot_rolling_volatility
from src.vix_forecasting.evaluation.backtest import walk_forward, summarize

ROOT     = Path(__file__).resolve().parents[1]
FIGURES  = ROOT / "figures"
DIAG_DIR = ROOT / "outputs" / "diagnostics"
PRED_DIR = ROOT / "outputs" / "predictions"
DIAG_DIR.mkdir(parents=True, exist_ok=True)

vix = build_series(load_raw(ROOT / "data" / "raw" / "vix_raw.csv"))
print(f"Series: {len(vix):,} obs  ({vix.index[0].date()} to {vix.index[-1].date()})")

# ── 1. Residual diagnostics ────────────────────────────────────────────────────
print("\n=== 1. Residual Diagnostics ===")

full_model = ARIMAForecaster()
full_model.fit(vix)
residuals = full_model.get_residuals()
print(f"Residuals: {len(residuals):,} obs  mean={residuals.mean():.4f}  std={residuals.std():.4f}")

diag = run_all(residuals, lb_lags=20, arch_lags=12)

print(f"\nLjung-Box (lag=20)  stat={diag['ljung_box_stat']}  p={diag['ljung_box_pvalue']}")
print(f"  -> {diag['ljung_box']['conclusion']}")

print(f"\nJarque-Bera         stat={diag['jarque_bera_stat']}  p={diag['jarque_bera_pvalue']}")
print(f"  skewness={diag['jarque_bera']['skewness']}  excess kurtosis={diag['jarque_bera']['excess_kurtosis']}")
print(f"  -> {diag['jarque_bera']['conclusion']}")

print(f"\nARCH-LM  (lag=12)   stat={diag['arch_lm_stat']}  p={diag['arch_lm_pvalue']}")
print(f"  -> {diag['arch_lm']['conclusion']}")

# Save JSON (flat keys only, matching spec)
json_out = {
    "ljung_box_stat":     diag["ljung_box_stat"],
    "ljung_box_pvalue":   diag["ljung_box_pvalue"],
    "jarque_bera_stat":   diag["jarque_bera_stat"],
    "jarque_bera_pvalue": diag["jarque_bera_pvalue"],
    "arch_lm_stat":       diag["arch_lm_stat"],
    "arch_lm_pvalue":     diag["arch_lm_pvalue"],
    # Full detail for reference
    "ljung_box_detail":   diag["ljung_box"],
    "jarque_bera_detail": diag["jarque_bera"],
    "arch_lm_detail":     diag["arch_lm"],
}
json_path = DIAG_DIR / "residual_diagnostics.json"
json_path.write_text(json.dumps(json_out, indent=2))
print(f"\nSaved: {json_path.relative_to(ROOT)}")

# Figures
plot_residual_qq(residuals, save_path=FIGURES / "arima_residual_qq.png")
print(f"Saved: figures/arima_residual_qq.png")

plot_residual_acf(residuals, lags=40, save_path=FIGURES / "arima_residual_acf.png")
print(f"Saved: figures/arima_residual_acf.png")

# ── 2. Log-VIX robustness check ───────────────────────────────────────────────
print("\n=== 2. Log-VIX Robustness Check ===")

HORIZONS  = [1, 5, 21]
TEST_SIZE = 756
STEP      = 21
MIN_TRAIN = 252

print("Running log-VIX walk-forward backtest ...", end="", flush=True)
t0 = time.time()
log_results = walk_forward(
    lambda: LogARIMAForecaster(),
    vix,
    HORIZONS,
    MIN_TRAIN,
    TEST_SIZE,
    STEP,
)
elapsed = time.time() - t0
print(f" done in {elapsed:.0f}s  ({len(log_results)} fold-horizon rows)")

log_summary = summarize(log_results)

# Load original ARIMA results for comparison
orig_summary_df = pd.read_csv(ROOT / "outputs" / "predictions" / "backtest_summary.csv")
arima_orig = orig_summary_df[orig_summary_df["model"] == "ARIMA"].set_index("horizon")

print("\nComparison: ARIMA(level) vs ARIMA(log-scale, back-transformed)")
print(f"{'Horizon':<10} {'Metric':<12} {'Level':<10} {'Log-scale':<10} {'Delta':<10}")
print("-" * 52)
for h in HORIZONS:
    for metric in ["rmse", "mae", "mape", "dir_acc"]:
        orig_val = arima_orig.loc[h, metric]
        log_val  = log_summary.loc[h, metric]
        delta    = log_val - orig_val
        print(f"h={h:<8} {metric:<12} {orig_val:<10.4f} {log_val:<10.4f} {delta:+.4f}")

# Save log-VIX backtest CSV (same format as backtest_summary.csv)
log_rows = []
for h in HORIZONS:
    row = log_summary.loc[h].to_dict()
    row["model"]   = "ARIMA_log"
    row["horizon"] = h
    log_rows.append(row)

log_csv = pd.DataFrame(log_rows)[["model", "horizon", "rmse", "mae", "mape", "dir_acc"]]
log_csv_path = PRED_DIR / "backtest_summary_log_vix.csv"
log_csv.to_csv(log_csv_path, index=False)
print(f"\nSaved: outputs/predictions/backtest_summary_log_vix.csv")

# ── 3. Rolling volatility plot ────────────────────────────────────────────────
print("\n=== 3. Rolling Volatility ===")
plot_rolling_volatility(vix, window=252,
                        save_path=FIGURES / "vix_rolling_volatility_by_year.png")
print("Saved: figures/vix_rolling_volatility_by_year.png")

print("\nAll addendum outputs generated.")
