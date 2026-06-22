# VIX Time Series Forecasting

A portfolio project forecasting the CBOE Volatility Index (VIX) using classical time series
methods — naive persistence baseline, ARIMA(1,0,2), and Facebook Prophet — evaluated via
expanding-window walk-forward validation across three forecast horizons: 1, 5, and 21 trading days.

## Key Results

| Model | h=1 RMSE | h=5 RMSE | h=21 RMSE | h=1 Dir Acc | h=21 Dir Acc |
|---|---|---|---|---|---|
| Naive (Persistence) | 1.175 | 1.900 | 3.250 | 0.0% | 0.0% |
| **ARIMA(1,0,2)** | **1.090** | **1.808** | **3.045** | **69.4%** | **50.4%** |
| Prophet | 5.637 | 5.957 | 6.242 | 66.7% | 53.2% |

**ARIMA(1,0,2) wins** across all horizons on all error metrics. Prophet's additive trend decomposition
is structurally incompatible with VIX's mean-reverting dynamics (5× worse RMSE). Key documented
negative result: weekly seasonality in VIX is real but negligible (0.44 VIX pts, ~6% of std dev).

## Repo Structure

```
.
├── config/config.yaml              # All tunable parameters (ticker, horizons, train size)
├── data/raw/                       # vix_raw.csv — yfinance download (^VIX, 1990-01-02 onward)
├── figures/                        # All generated charts (history, ACF/PACF, backtest, etc.)
├── notebooks/
│   ├── 01_eda.ipynb                # Full history, distribution, ACF/PACF
│   ├── 02_stationarity.ipynb       # ADF + KPSS tests; d=0 decision
│   ├── 03_modeling_and_evaluation.ipynb  # ARIMA order selection, Prophet, walk-forward
│   └── 04_results_summary.ipynb   # Final comparison, failure mode analysis
├── outputs/predictions/
│   └── backtest_summary.csv        # Mean metrics per model × horizon across 36 folds
├── reports/
│   ├── results_summary.md          # Prose findings
│   ├── vix_forecasting_report.pdf  # Final CWP-style technical report
│   └── generate_cwp_report.py      # PDF generator (requires reportlab)
├── src/vix_forecasting/
│   ├── data/acquisition.py         # yfinance download + validation
│   ├── data/preprocessing.py       # Series construction (no resampling needed)
│   ├── analysis/eda.py             # Plotting functions
│   ├── analysis/stationarity.py    # ADF + KPSS wrappers
│   ├── models/base.py              # BaseForecaster ABC
│   ├── models/baseline.py          # NaiveForecaster (persistence)
│   ├── models/arima.py             # ARIMAForecaster + select_order()
│   ├── models/prophet_model.py     # ProphetForecaster
│   └── evaluation/
│       ├── metrics.py              # rmse, mae, mape, directional_accuracy
│       └── backtest.py             # walk_forward() + summarize()
└── tests/
    ├── test_metrics.py             # 11 unit tests on all metrics
    └── test_backtest.py            # 7 tests: fold count, no leakage, bounds
```

## Reproducing the Results

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download VIX data
python -c "
from src.vix_forecasting.data.acquisition import download_vix, save_raw
import yaml
cfg = yaml.safe_load(open('config/config.yaml'))
df = download_vix(cfg['data']['ticker'], cfg['data']['start_date'])
save_raw(df, 'data/raw/vix_raw.csv')
"

# 3. Run tests
pytest tests/ -v

# 4. Run the full backtest (takes ~15 min — Prophet is slow)
python reports/_phase7_backtest.py

# 5. Generate the CWP-style PDF report
python reports/generate_cwp_report.py

# 6. Open the notebooks in order (01 → 04) for the interactive analysis
```

## Design Decisions

**d=0 (no differencing):** Both ADF (p≈0.000) and KPSS (p≈0.10) agree VIX levels are stationary.
The slow ACF decay reflects high AR persistence (~0.984), not a unit root.

**ARIMA(1,0,2):** Best converged model by AIC on an 8-year order-selection window. ARIMA(3,0,2)
scored lower AIC but did not converge. Seasonal SMA(5) improved selection-window AIC by 17 points
but its full-series coefficient was 0.0005 (p=0.923) — documented as a negative result.

**Walk-forward validation:** Expanding window with test_size=756 (~3 years), step=21 (monthly
refit), 36 folds. No static train/test split — models are evaluated the way they would be used live.

**Directional accuracy:** Computed step-by-step (direction at each step vs previous actual),
excluding steps where the actual move is exactly flat. Naive gets 0% by design.

## Connection to Capstone

The backtest harness (`src/vix_forecasting/evaluation/`) is model-agnostic and will be reused
for the upcoming live stock market prediction dashboard. Key lesson: for mean-reverting financial
indices, properly validated AR models outperform trend-decomposition approaches.
