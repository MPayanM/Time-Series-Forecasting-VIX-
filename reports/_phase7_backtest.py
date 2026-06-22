"""Phase 7 — walk-forward backtest across all three models and horizons."""
import sys, warnings, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import numpy as np
import pandas as pd

from src.vix_forecasting.data.preprocessing import load_raw, build_series
from src.vix_forecasting.models.baseline import NaiveForecaster
from src.vix_forecasting.models.arima import ARIMAForecaster
from src.vix_forecasting.models.prophet_model import ProphetForecaster
from src.vix_forecasting.evaluation.backtest import walk_forward, summarize

sns.set_theme(style="whitegrid", palette="muted")
ROOT    = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"

vix = build_series(load_raw(ROOT / "data" / "raw" / "vix_raw.csv"))

HORIZONS      = [1, 5, 21]
TEST_SIZE     = 756    # ~3 years  (2023-06 to 2026-06)
STEP          = 21     # monthly refit
MIN_TRAIN     = 252

print(f"Series       : {len(vix):,} obs")
print(f"Test window  : last {TEST_SIZE} obs ({vix.index[-TEST_SIZE].date()} to {vix.index[-1].date()})")
print(f"Step         : {STEP}  Horizons: {HORIZONS}")
n_folds = len(range(len(vix) - TEST_SIZE, len(vix) - max(HORIZONS) + 1, STEP))
print(f"Approx folds : {n_folds}")
print()

MODELS = {
    "Naive":   lambda: NaiveForecaster(),
    "ARIMA":   lambda: ARIMAForecaster(),
    "Prophet": lambda: ProphetForecaster(),
}

all_results = {}
for name, factory in MODELS.items():
    print(f"Running {name} ...", end="", flush=True)
    t0 = time.time()
    df = walk_forward(factory, vix, HORIZONS, MIN_TRAIN, TEST_SIZE, STEP)
    elapsed = time.time() - t0
    all_results[name] = df
    print(f" done in {elapsed:.0f}s  ({len(df)} fold-horizon rows)")

# ── Summary table ─────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("WALK-FORWARD RESULTS  (mean across folds, per horizon)")
print("=" * 70)

rows = []
for model_name, df in all_results.items():
    s = summarize(df)
    for h in HORIZONS:
        row = s.loc[h].to_dict()
        row["model"]   = model_name
        row["horizon"] = h
        rows.append(row)

summary_df = pd.DataFrame(rows).set_index(["model", "horizon"])
print(summary_df.to_string())
summary_df.to_csv(ROOT / "outputs" / "predictions" / "backtest_summary.csv")
print()
print("Saved: outputs/predictions/backtest_summary.csv")

# ── Figure 1: Metric comparison bar charts ────────────────────────────────────
metrics   = ["rmse", "mae", "mape", "dir_acc"]
titles    = ["RMSE", "MAE", "MAPE (%)", "Directional Accuracy"]
colors    = {"Naive": "#718096", "ARIMA": "#2B6CB0", "Prophet": "#E07070"}
x         = np.arange(len(HORIZONS))
width     = 0.25

fig, axes = plt.subplots(2, 2, figsize=(13, 8))
axes = axes.flatten()

for ax, metric, title in zip(axes, metrics, titles):
    for i, (model_name, _) in enumerate(MODELS.items()):
        vals = [summary_df.loc[(model_name, h), metric] for h in HORIZONS]
        ax.bar(x + i * width, vals, width, label=model_name,
               color=colors[model_name], alpha=0.85)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels([f"{h}d" for h in HORIZONS])
    ax.set_xlabel("Forecast horizon")
    ax.legend(fontsize=8)
    if metric == "dir_acc":
        ax.set_ylim(0, 1)
        ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, label="random")

fig.suptitle("Walk-forward Evaluation — VIX Forecasting", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(FIGURES / "backtest_metrics_comparison.png", dpi=150)
print("Saved: figures/backtest_metrics_comparison.png")

# ── Figure 2: Actual vs predicted for horizon=5 ───────────────────────────────
fig2, axes2 = plt.subplots(3, 1, figsize=(13, 10), sharex=True)
for ax, (model_name, df) in zip(axes2, all_results.items()):
    df5 = df[df["horizon"] == 5].copy()
    # Reconstruct predicted endpoint per fold
    # We store the fold's predicted[-1] and actual[-1] for the horizon=5 case
    # Re-run a lightweight version to get per-fold endpoint series
    ax.set_title(f"{model_name} — horizon=5d", fontsize=10)
    ax.set_ylabel("VIX")
    ax.plot([], [], color=colors[model_name], label=model_name)
    ax.legend(fontsize=8)

# For a clean actual-vs-predicted plot, run one model at a time collecting
# the h-step-ahead endpoint (predicted[h-1]) and actual[h-1]
fig2, axes2 = plt.subplots(3, 1, figsize=(13, 10), sharex=True)
for ax, (model_name, factory) in zip(axes2, MODELS.items()):
    print(f"Re-collecting {model_name} forecasts for plot ...", end="", flush=True)
    test_start = len(vix) - TEST_SIZE
    fold_dates, actuals_end, preds_end = [], [], []
    df_model = all_results[model_name]
    df5 = df_model[df_model["horizon"] == 5].reset_index(drop=True)

    # We only have aggregate metrics per fold, so reconstruct endpoint from
    # the fold raw data by re-running a single lightweight pass
    for _, row in df5.iterrows():
        t = vix.index.get_loc(row["train_end_date"]) + 1
        if t + 5 > len(vix):
            continue
        fold_dates.append(vix.index[t + 4])
        actuals_end.append(float(vix.iloc[t + 4]))

    # Use last_obs + naive reconstruction for predicted endpoint using RMSE
    # relationship; instead just load model once per fold to get the endpoint
    model_preds = []
    for _, row in df5.iterrows():
        t = vix.index.get_loc(row["train_end_date"]) + 1
        if t + 5 > len(vix):
            continue
        m = factory()
        m.fit(vix.iloc[:t])
        model_preds.append(float(m.predict(5)[-1]))

    fold_dates  = fold_dates[:len(model_preds)]
    actuals_end = actuals_end[:len(model_preds)]

    ax.plot(fold_dates, actuals_end,  color="#1A202C", linewidth=1.2,
            label="Actual VIX (h=5 endpoint)")
    ax.plot(fold_dates, model_preds, color=colors[model_name],
            linewidth=1.0, linestyle="--", marker="o", markersize=3,
            label=f"{model_name} predicted")
    ax.set_title(f"{model_name} — 5-day-ahead endpoint forecast vs actual",
                 fontsize=10)
    ax.set_ylabel("VIX")
    ax.legend(fontsize=8)
    print(" done")

fig2.suptitle("5-Day-Ahead Forecast vs Actual  (one point per fold)", fontsize=12)
fig2.tight_layout()
fig2.savefig(FIGURES / "backtest_forecast_vs_actual.png", dpi=150)
print("Saved: figures/backtest_forecast_vs_actual.png")

# ── Print final verdict ────────────────────────────────────────────────────────
print()
print("=" * 70)
print("VERDICT")
print("=" * 70)
for h in HORIZONS:
    best_rmse = summary_df.xs(h, level="horizon")["rmse"].idxmin()
    best_dir  = summary_df.xs(h, level="horizon")["dir_acc"].idxmax()
    print(f"Horizon {h:2d}d  best RMSE: {best_rmse}  best dir-acc: {best_dir}")
