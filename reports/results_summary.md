# VIX Forecasting — Results Summary

## Project objective

Forecast the CBOE Volatility Index (VIX) at horizons of 1, 5, and 21 trading days using three classical time series approaches: a naive persistence baseline, ARIMA(1,0,2), and Facebook Prophet. All models are evaluated via expanding-window walk-forward validation on the last three years of data (2023-06 to 2026-06, 36 monthly folds).

## Key findings

### Stationarity
Both ADF and KPSS tests agree: VIX levels are stationary (ADF p≈0.000, KPSS p≈0.10). No differencing is needed. The slow ACF decay reflects near-unit-root persistence (AR coefficient ≈ 0.984), not a true unit root.

### Model selection
The ARIMA(1,0,2) specification was selected as the best converged model by AIC on an 8-year order-selection window. A seasonal SMA(1) term at lag 5 (weekly) improved the selection-window AIC by 17 points but its coefficient was 0.0005 (p = 0.923) on the full 36-year history — a documented negative result. No meaningful weekly seasonality in VIX.

### Walk-forward results

| Model | h=1 RMSE | h=5 RMSE | h=21 RMSE | h=1 Dir Acc | h=21 Dir Acc |
|-------|----------|----------|-----------|-------------|--------------|
| Naive | 1.175 | 1.900 | 3.250 | 0% | 0% |
| ARIMA(1,0,2) | **1.090** | **1.808** | **3.045** | **69.4%** | **50.4%** |
| Prophet | 5.637 | 5.957 | 6.242 | 66.7% | 53.2% |

**ARIMA(1,0,2) is the best model** across all horizons on all error metrics. It beats the persistence baseline by ~7% RMSE — modest but consistent across all 36 folds.

### Where every model fails

**Naive**: Cannot predict direction by construction (always forecasts flat). Accuracy degrades predictably with horizon since VIX mean-reverts.

**ARIMA**: Directional accuracy collapses to ~50% (coin flip) at the 21-day horizon. Spike onsets are not predicted — the model systematically under-forecasts the magnitude of sudden volatility spikes because they are not linearly predictable from recent history. The AR(1)≈0.984 structure is excellent for calm regimes but slow to adapt when VIX jumps.

**Prophet**: Catastrophically worse on point forecast error (5× RMSE vs ARIMA). The additive trend decomposition systematically overestimates VIX during low-volatility regimes by pulling forecasts toward a longer-run trend level that does not match VIX's mean-reverting structure. Prophet's weekly Fourier terms overfit a small but genuine day-of-week signal (~0.44 VIX pts) by a factor of ~9×.

---

## Residual Diagnostics

Diagnostics were run on the ARIMA(1,0,2) model fitted to the full 9,183-observation series. All three tests reject their null hypotheses.

| Test | Statistic | p-value | Conclusion |
|------|-----------|---------|------------|
| Ljung-Box (lag=20) | 91.07 | <0.001 | Residual autocorrelation detected |
| Jarque-Bera | 315,931.00 | <0.001 | Non-normal residuals (fat tails + skew) |
| ARCH-LM (lag=12) | 1,571.17 | <0.001 | Variance clustering present (ARCH effects) |

**Ljung-Box:** The Q(20) statistic of 91.07 (p<0.001) indicates that residuals are not white noise — some autocorrelation structure remains uncaptured by the ARIMA(1,0,2) specification. This is typical of financial time series; a higher-order AR or MA term might reduce it marginally, but at the cost of overfitting a model already near its linear predictability ceiling.

**Jarque-Bera:** Residuals have skewness of 2.23 and excess kurtosis of 31.39 — extreme right skew and very fat tails. This is a direct consequence of volatility spikes (COVID March 2020, 2022 selloff): spike-onset days produce large positive residuals that are highly non-Gaussian. The ARIMA Gaussian likelihood assumption is violated; confidence intervals from the model are unreliable. Point forecasts remain valid, but no probabilistic interpretation should be attached to model standard errors.

**ARCH-LM:** The LM statistic of 1571.17 (p<0.001) confirms strong ARCH effects — residual variance is not constant but clusters around volatility events. This is expected: the ARIMA model cannot capture the heteroskedastic structure of VIX. The natural extension would be a GARCH(1,1) on the ARIMA residuals (ARIMA-GARCH), which would model the conditional variance explicitly. This is left for future work.

**Honest interpretation:** All three diagnostics point to the same underlying phenomenon — VIX spikes are sudden, large, and unpredictable from linear history, producing non-normal, autocorrelated, heteroskedastic residuals. These are findings to report, not problems to hide: they define the hard boundary of what a linear model can do with this series.

---

## Log-Scale Robustness Check

The same walk-forward backtest (36 folds, test_size=756, step=21) was repeated with ARIMA(1,0,2) fitted on log(VIX) instead of raw VIX levels. Log forecasts were exponentiated back to the original scale before computing all metrics, ensuring a fair comparison. Non-negativity is guaranteed by construction (exp is always > 0).

| Horizon | Metric | Level ARIMA | Log-scale ARIMA | Delta |
|---------|--------|-------------|-----------------|-------|
| h=1 | RMSE | **1.0896** | 1.1118 | +0.022 |
| h=1 | MAE | **1.0896** | 1.1118 | +0.022 |
| h=1 | MAPE | **5.93%** | 6.03% | +0.10 pp |
| h=1 | Dir Acc | **69.4%** | 66.7% | −2.8 pp |
| h=5 | RMSE | 1.8081 | **1.8051** | −0.003 |
| h=5 | MAE | **1.5600** | 1.5612 | +0.001 |
| h=5 | MAPE | 8.52% | **8.50%** | −0.02 pp |
| h=5 | Dir Acc | 56.1% | **57.8%** | +1.7 pp |
| h=21 | RMSE | 3.0449 | **2.9971** | −0.048 |
| h=21 | MAE | 2.5282 | **2.4766** | −0.052 |
| h=21 | MAPE | 13.54% | **13.06%** | −0.48 pp |
| h=21 | Dir Acc | 50.4% | **52.0%** | +1.7 pp |

**Verdict:** The differences are negligible across all horizons (< 2% RMSE, < 3 pp directional accuracy). Level-scale ARIMA has a slight edge at h=1; log-scale has a slight edge at h=21. Neither advantage is practically significant. **Level-scale ARIMA(1,0,2) remains the recommended model** — it produces slightly better short-horizon accuracy and is more interpretable (forecasts are directly in VIX units without back-transformation).

The log transform does not meaningfully stabilize variance for ARIMA purposes because the instability comes from discrete spike events, not from proportional variance growth across the level of the series. A GARCH specification would address this more directly.

---

## Practical Questions Answered

**"Can we predict VIX 1 day ahead based on historical data?"**
Yes, with modest accuracy. ARIMA(1,0,2) achieves RMSE=1.09 and MAE=1.09 at h=1, meaning the average forecast error is about 1 VIX point. Directional accuracy is 69.4%, well above the 50% random baseline. This level of accuracy is **useful for risk sizing** (e.g., adjusting portfolio delta hedges, scaling position sizes to expected near-term volatility) but not for trading signals on its own. The model cannot call the magnitude of a spike, only that VIX is likely to remain near its current level on calm days.

**"Can we predict VIX 5 days (1 week) ahead?"**
With degrading reliability. RMSE rises to 1.81 and directional accuracy drops to 56.1% — above random but barely. At this horizon the model's only real information is mean reversion: if VIX is currently above its long-run mean (~19), it will probably be a little lower in 5 days; if below, a little higher. This is **useful for weekly rebalancing decisions** (e.g., when to roll options positions) but should not be relied on for direction in uncertain regimes.

**"Can we predict VIX 21 days (1 month) ahead?"**
Barely better than guessing. RMSE=3.05, directional accuracy=50.4% — a near coin flip. At 21 days, mean reversion has absorbed most of the predictable signal, and the forecast converges toward a constant near the long-run mean regardless of the current VIX level. This is **not useful for directional decisions**. It may still be useful as a baseline for scenario analysis (e.g., "what would a 'no new shocks' month look like?") but should not inform any active trading or hedging decision.

**"Can the model anticipate volatility spikes in advance?"**
No. All three models — Naive, ARIMA, and Prophet — fail to predict spike onsets. Spikes in VIX are driven by exogenous macro/geopolitical events (pandemic announcements, central bank surprises, credit events) that carry no signal in past VIX values. The ARCH-LM result confirms the model knows that variance clusters — but not when the next cluster will begin. The 69.4% directional accuracy at h=1 is achieved mostly on the 90%+ of days when VIX makes a small, predictable mean-reverting move. **Spike prediction would require exogenous regressors** (e.g., credit spread widening, put/call ratio, macro surprise indices, news sentiment) — beyond the scope of this classical time series project.

---

## Connection to upcoming capstone

The methodology established here — walk-forward validation discipline, honest baseline comparison, documented negative results on seasonality, explicit failure-mode analysis — will carry directly into the live stock market prediction dashboard. The ARIMA backtest harness in `src/vix_forecasting/evaluation/` is built to be model-agnostic and will be reused with minimal changes for equity return forecasting. The key lesson from this project: for mean-reverting financial indices, simple AR models with proper out-of-sample validation outperform more complex decomposition approaches.
