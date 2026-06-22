"""Phase 5 order-selection analysis — run once, results inform ARIMAForecaster defaults."""
import sys, warnings, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from src.vix_forecasting.data.preprocessing import load_raw, build_series
from src.vix_forecasting.models.arima import select_order, ARIMAForecaster

vix = build_series(load_raw(Path(__file__).parents[1] / "data" / "raw" / "vix_raw.csv"))

# Order-selection window: last 2,000 trading days (~8 yrs).
# Spans COVID spike, 2022 selloff, post-2022 recovery.
sel = vix.iloc[-2000:]
print(f"Order-selection window: {sel.index[0].date()} to {sel.index[-1].date()}  ({len(sel)} obs)")
print()

# ── 1. Non-seasonal grid search ───────────────────────────────────────────────
print("Fitting non-seasonal  ARIMA(p,0,q)  p in {1,2,3}  q in {0,1,2} ...")
t0 = time.time()
df_ns = select_order(sel, p_values=(1, 2, 3), q_values=(0, 1, 2), d=0, seasonal=False)
print(f"Done in {time.time()-t0:.1f}s\n")
print(df_ns[["order", "aic", "bic", "converged"]].to_string(index=True))

# Non-convergence makes parameter estimates unreliable: prefer converged models.
df_ns_conv = df_ns[df_ns["converged"] == True]
best_ns_row   = df_ns_conv.iloc[0]
best_order    = best_ns_row["order"]
best_aic_ns   = best_ns_row["aic"]

print(f"\nRaw AIC winner : ARIMA{df_ns.iloc[0]['order']}  AIC={df_ns.iloc[0]['aic']}  converged={df_ns.iloc[0]['converged']}")
print(f"Best CONVERGED : ARIMA{best_order}  AIC={best_aic_ns}")

# ── 2. Seasonal test against best converged non-seasonal ─────────────────────
print()
p, d, q = best_order
print(f"Testing seasonal component on ARIMA{best_order}  SARIMA({p},0,{q})(P,0,Q,5)  P,Q in {{0,1}} ...")
t0 = time.time()
df_s = select_order(
    sel,
    p_values=(p,), q_values=(q,), d=0,
    seasonal=True, m=5,
    P_values=(0, 1), Q_values=(0, 1),
)
print(f"Done in {time.time()-t0:.1f}s\n")
print(df_s[["order", "seasonal_order", "aic", "bic", "converged"]].to_string(index=True))

df_s_conv = df_s[df_s["converged"] == True]
if df_s_conv.empty:
    print("\nNo seasonal variants converged. Retaining non-seasonal model.")
    seasonal_useful = False
else:
    best_s_row  = df_s_conv.iloc[0]
    best_aic_s  = best_s_row["aic"]
    improvement = best_aic_ns - best_aic_s
    seasonal_useful = improvement > 2
    print(f"\nBest converged seasonal: SARIMA{best_s_row['order']}{best_s_row['seasonal_order']}  AIC={best_aic_s}")
    print(f"AIC improvement over non-seasonal: {improvement:+.2f}  (threshold >2 to be meaningful)")

print()
print("=" * 60)
print("VERDICT")
print("=" * 60)
if seasonal_useful:
    final_order    = best_s_row["order"]
    final_seasonal = best_s_row["seasonal_order"]
    print(f"Seasonal component IS useful (AIC -{improvement:.1f}).")
    print(f"Final model: SARIMA{final_order}{final_seasonal}")
else:
    final_order    = best_order
    final_seasonal = (0, 0, 0, 0)
    print("Seasonal component does NOT meaningfully improve fit.")
    print(f"Final model: ARIMA{final_order}  (d=0 confirmed by Phase 3)")

# ── 3. Coefficient summary on final model, full series ────────────────────────
print()
print("=" * 60)
print("COEFFICIENT SUMMARY  (final model, fitted on full series)")
print("=" * 60)
model = ARIMAForecaster(order=final_order, seasonal_order=final_seasonal)
model.fit(vix)
print(model._result.summary().tables[1])

# ── 4. Predict sanity check ───────────────────────────────────────────────────
print()
print(f"Current VIX (last obs {vix.index[-1].date()}): {vix.iloc[-1]:.2f}")
print("Multi-step forecasts:")
for h in (1, 5, 21):
    preds = model.predict(h)
    print(f"  horizon={h:2d}  -> {preds.round(3)}")
