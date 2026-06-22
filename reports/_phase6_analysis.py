"""Phase 6 analysis — Prophet fit, seasonality cross-check, multi-step forecasts."""
import sys, warnings, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from src.vix_forecasting.data.preprocessing import load_raw, build_series
from src.vix_forecasting.models.prophet_model import ProphetForecaster

sns.set_theme(style="whitegrid")
ROOT    = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
vix     = build_series(load_raw(ROOT / "data" / "raw" / "vix_raw.csv"))

# ── 1. Fit on full series ─────────────────────────────────────────────────────
print("Fitting Prophet on full series ...")
t0 = time.time()
model = ProphetForecaster(weekly_seasonality=True, yearly_seasonality=True)
model.fit(vix)
print(f"Done in {time.time()-t0:.1f}s\n")

# ── 2. Seasonality amplitudes ─────────────────────────────────────────────────
amps = model.seasonality_amplitudes()
print("Seasonality component amplitudes (peak-to-trough):")
for name, amp in amps.items():
    pct = amp / vix.std() * 100
    print(f"  {name:10s}: {amp:.4f} VIX pts  ({pct:.1f}% of series std dev {vix.std():.2f})")

# ── 3. Multi-step forecasts ───────────────────────────────────────────────────
print()
print(f"Current VIX ({vix.index[-1].date()}): {vix.iloc[-1]:.2f}")
for h in (1, 5, 21):
    preds = model.predict(h)
    print(f"  horizon={h:2d}d  -> [{preds[0]:.3f} ... {preds[-1]:.3f}]  shape={preds.shape}")

# ── 4. Plot: in-sample fit + components ──────────────────────────────────────
print()
print("Generating Prophet component plots ...")

# Predict on training data for component decomposition
train_df = pd.DataFrame({"ds": vix.index, "y": vix.values})
forecast_df = model._model.predict(train_df)

# Component plot (weekly + yearly)
fig, axes = plt.subplots(2, 1, figsize=(13, 6))

# Weekly component
weekly_cols = [c for c in forecast_df.columns if c.startswith("weekly")]
if weekly_cols:
    comp = forecast_df[weekly_cols[0]]
    # Prophet assigns a day-of-week to each point — pick one week
    week_sample = forecast_df[forecast_df["ds"].dt.dayofweek < 5].head(5)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    y_vals = week_sample[weekly_cols[0]].values[:5]
    axes[0].bar(days[:len(y_vals)], y_vals, color="#2B6CB0", alpha=0.8)
    axes[0].axhline(0, color="gray", linewidth=0.8)
    axes[0].set_title("Weekly seasonality component (additive, VIX pts)", fontsize=10)
    axes[0].set_ylabel("Component value")

# Yearly component
yearly_cols = [c for c in forecast_df.columns if c.startswith("yearly")]
if yearly_cols:
    year_sample = forecast_df[forecast_df["ds"].dt.year == 2019].copy()
    axes[1].plot(year_sample["ds"], year_sample[yearly_cols[0]],
                 color="#2B9348", linewidth=1.2)
    axes[1].axhline(0, color="gray", linewidth=0.8)
    axes[1].set_title("Yearly seasonality component (additive, VIX pts) — 2019 example",
                       fontsize=10)
    axes[1].set_ylabel("Component value")

fig.tight_layout()
fig.savefig(FIGURES / "prophet_components.png", dpi=150)
print("Saved: figures/prophet_components.png")

# In-sample fit (last 2 years)
fig2, ax = plt.subplots(figsize=(13, 4))
recent = vix["2024-01-01":]
fc_recent = forecast_df[forecast_df["ds"] >= pd.Timestamp("2024-01-01")]
ax.plot(recent.index, recent.values, color="#2B6CB0", linewidth=1.0, label="Actual VIX")
ax.plot(fc_recent["ds"], fc_recent["yhat"],
        color="#E07070", linewidth=1.0, linestyle="--", label="Prophet in-sample fit")
ax.fill_between(fc_recent["ds"], fc_recent["yhat_lower"], fc_recent["yhat_upper"],
                alpha=0.15, color="#E07070", label="80% interval")
ax.set_title("Prophet in-sample fit — 2024 to present", fontsize=10)
ax.set_ylabel("VIX Level")
ax.legend(fontsize=8)
fig2.tight_layout()
fig2.savefig(FIGURES / "prophet_insample_fit.png", dpi=150)
print("Saved: figures/prophet_insample_fit.png")

# ── 5. Verdict ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("SEASONALITY CROSS-CHECK VERDICT")
print("=" * 60)
weekly_amp = amps.get("weekly", 0)
yearly_amp = amps.get("yearly", 0)
print(f"Weekly amplitude : {weekly_amp:.4f} VIX pts  ({weekly_amp/vix.std()*100:.1f}% of std)")
print(f"Yearly amplitude : {yearly_amp:.4f} VIX pts  ({yearly_amp/vix.std()*100:.1f}% of std)")
if weekly_amp / vix.std() < 0.05:
    print("\nWeekly component is negligible (< 5% of std dev).")
    print("CONFIRMS Phase 5 finding: no meaningful weekly seasonality in VIX.")
else:
    print(f"\nWeekly component is {weekly_amp/vix.std()*100:.1f}% of std dev — warrants attention.")
