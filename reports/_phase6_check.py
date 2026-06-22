"""Interface check for all three models + day-of-week figure."""
import sys, warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.vix_forecasting.data.preprocessing import load_raw, build_series
from src.vix_forecasting.models.baseline import NaiveForecaster
from src.vix_forecasting.models.arima import ARIMAForecaster
from src.vix_forecasting.models.prophet_model import ProphetForecaster

ROOT = Path(__file__).resolve().parents[1]
vix  = build_series(load_raw(ROOT / "data" / "raw" / "vix_raw.csv"))

# Day-of-week figure
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
dow = pd.DataFrame({"vix": vix, "day": vix.index.day_name(), "chg": vix.diff()})
dow_stats = dow.groupby("day")[["vix", "chg"]].mean().reindex(day_order)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].bar(day_order, dow_stats["vix"], color="#2B6CB0", alpha=0.8)
axes[0].set_title("Mean VIX level by day of week")
axes[0].set_ylabel("Mean VIX")
axes[0].set_ylim(dow_stats["vix"].min() - 0.5, dow_stats["vix"].max() + 0.5)
colors = ["#E07070" if v > 0 else "#2B9348" for v in dow_stats["chg"]]
axes[1].bar(day_order, dow_stats["chg"], color=colors, alpha=0.8)
axes[1].axhline(0, color="gray", linewidth=0.8)
axes[1].set_title("Mean daily VIX change by day of week")
axes[1].set_ylabel("Mean change (VIX pts)")
fig.tight_layout()
fig.savefig(ROOT / "figures" / "vix_day_of_week.png", dpi=150)
print("Saved: figures/vix_day_of_week.png")

# Three-model interface check
train = vix[:"2024-12-31"]
naive   = NaiveForecaster();   naive.fit(train)
arima   = ARIMAForecaster();   arima.fit(train)
prophet = ProphetForecaster(); prophet.fit(train)

print()
print(f"Last training obs: {train.index[-1].date()}  VIX={train.iloc[-1]:.2f}")
print(f"{'Horizon':>10}  {'Naive':>8}  {'ARIMA':>8}  {'Prophet':>8}")
print("-" * 42)
for h in (1, 5, 21):
    n = naive.predict(h)[-1]
    a = arima.predict(h)[-1]
    p = prophet.predict(h)[-1]
    for m_pred in [naive.predict(h), arima.predict(h), prophet.predict(h)]:
        assert isinstance(m_pred, np.ndarray) and len(m_pred) == h
    print(f"{h:>7d}d  {n:>8.3f}  {a:>8.3f}  {p:>8.3f}")

print()
print("All interface assertions passed.")
