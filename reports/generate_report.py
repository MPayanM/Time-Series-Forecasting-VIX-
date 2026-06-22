"""Generate a PDF progress report for the VIX forecasting project."""
import sys, warnings
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec

from src.vix_forecasting.data.preprocessing import load_raw, build_series
from src.vix_forecasting.analysis.stationarity import run_adf, run_kpss

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
OUTPUT  = ROOT / "reports" / "vix_forecasting_report.pdf"

vix   = build_series(load_raw(ROOT / "data" / "raw" / "vix_raw.csv"))
diff1 = vix.diff().dropna()

adf_level  = run_adf(vix,   regression="c")
kpss_level = run_kpss(vix,  regression="c")
adf_diff   = run_adf(diff1, regression="c")
kpss_diff  = run_kpss(diff1, regression="c")

# ── Design tokens ─────────────────────────────────────────────────────────────
BLUE   = "#2B6CB0"
LBLUE  = "#EBF4FF"
DARK   = "#1A202C"
GRAY   = "#4A5568"
LGRAY  = "#F7FAFC"
GREEN  = "#276749"
WHITE  = "#FFFFFF"
PAGE_W, PAGE_H = 11, 8.5          # landscape letter

# ── Helpers ───────────────────────────────────────────────────────────────────
def new_page(pdf: PdfPages, title: str, subtitle: str = "") -> plt.Figure:
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), facecolor=WHITE)
    # header bar
    hdr = fig.add_axes([0, 0.91, 1, 0.09])
    hdr.set_facecolor(BLUE); hdr.axis("off")
    hdr.text(0.025, 0.55, title,    color=WHITE,   fontsize=17, fontweight="bold", va="center")
    hdr.text(0.025, 0.15, subtitle, color="#BEE3F8", fontsize=9,  va="center")
    # footer bar
    ftr = fig.add_axes([0, 0, 1, 0.035])
    ftr.set_facecolor(LGRAY); ftr.axis("off")
    ftr.text(0.025, 0.5, "VIX Time Series Forecasting  ·  Portfolio Project",
             color=GRAY, fontsize=8, va="center")
    ftr.text(0.975, 0.5, f"Generated {date.today()}",
             color=GRAY, fontsize=8, va="center", ha="right")
    return fig


def section_label(ax: plt.Axes, text: str) -> None:
    ax.text(0, 1.04, text, transform=ax.transAxes,
            fontsize=10, fontweight="bold", color=BLUE, va="bottom")


def body_text(fig: plt.Figure, x: float, y: float, text: str,
              width: float = 0.9, fontsize: float = 9.5, color: str = DARK) -> None:
    fig.text(x, y, text, fontsize=fontsize, color=color,
             wrap=True, va="top",
             bbox=dict(boxstyle="square,pad=0", fc="none", ec="none"),
             transform=fig.transFigure)


def embed_img(ax: plt.Axes, path: Path) -> None:
    img = mpimg.imread(path)
    ax.imshow(img, aspect="auto")
    ax.axis("off")


def kv_table(ax: plt.Axes, rows: list[tuple], col_labels: list[str],
             col_widths: list[float] | None = None) -> None:
    ax.axis("off")
    tbl = ax.table(
        cellText=rows,
        colLabels=col_labels,
        cellLoc="left",
        loc="center",
        colWidths=col_widths or [0.35, 0.65],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#CBD5E0")
        if r == 0:
            cell.set_facecolor(BLUE)
            cell.set_text_props(color=WHITE, fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor(LBLUE)
        else:
            cell.set_facecolor(WHITE)
        cell.set_linewidth(0.5)
        cell.PAD = 0.06


# ─────────────────────────────────────────────────────────────────────────────
# Page 1 — Cover
# ─────────────────────────────────────────────────────────────────────────────
def page_cover(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), facecolor=BLUE)

    # large title block
    fig.text(0.5, 0.65, "VIX Time Series Forecasting",
             color=WHITE, fontsize=32, fontweight="bold", ha="center", va="center")
    fig.text(0.5, 0.55, "Walk-forward evaluation of Naive Baseline · ARIMA/SARIMA · Prophet",
             color="#BEE3F8", fontsize=14, ha="center", va="center")

    # divider
    line = plt.Line2D([0.1, 0.9], [0.49, 0.49], transform=fig.transFigure,
                      color="#63B3ED", linewidth=1.5)
    fig.add_artist(line)

    # meta block
    meta = [
        ("Forecast horizons", "1 · 5 · 21 trading days"),
        ("Data", f"CBOE VIX  —  1990-01-02 to {vix.index[-1].date()}  ({len(vix):,} trading days)"),
        ("Phases complete", "0 Scaffolding   1 Data Acquisition   2 EDA   3 Stationarity   4 Baseline"),
        ("Status", "In progress  —  Phases 5–8 (ARIMA · Prophet · Backtest · Results) upcoming"),
    ]
    y = 0.43
    for label, value in meta:
        fig.text(0.12, y, f"{label}:", color="#BEE3F8", fontsize=10,
                 fontweight="bold", va="top")
        fig.text(0.37, y, value, color=WHITE, fontsize=10, va="top")
        y -= 0.07

    fig.text(0.5, 0.06, f"Generated {date.today()}",
             color="#63B3ED", fontsize=9, ha="center")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Page 2 — Data Acquisition
# ─────────────────────────────────────────────────────────────────────────────
def page_data(pdf: PdfPages) -> None:
    fig = new_page(pdf, "Phase 1  —  Data Acquisition",
                   "Source: Yahoo Finance (yfinance)  ·  Ticker: ^VIX")

    # stats table (left)
    ax_tbl = fig.add_axes([0.04, 0.12, 0.38, 0.72])
    stats_rows = [
        ("Trading days",    f"{len(vix):,}"),
        ("Start date",      str(vix.index[0].date())),
        ("End date",        str(vix.index[-1].date())),
        ("Minimum VIX",     f"{vix.min():.2f}  (Mar 2017)"),
        ("Maximum VIX",     f"{vix.max():.2f}  (Mar 2020, COVID)"),
        ("Mean",            f"{vix.mean():.2f}"),
        ("Median",          f"{vix.median():.2f}"),
        ("Std deviation",   f"{vix.std():.2f}"),
        ("Missing Close",   "None"),
        ("Gaps > 5 days",   "1  (Sep 10–17, 2001  —  9/11 closure)"),
    ]
    kv_table(ax_tbl, stats_rows, ["Statistic", "Value"], [0.38, 0.62])
    section_label(ax_tbl, "Summary statistics")

    # mini history (right)
    ax_hist = fig.add_axes([0.47, 0.35, 0.5, 0.49])
    ax_hist.plot(vix.index, vix.values, color=BLUE, linewidth=0.7)
    ax_hist.set_title("VIX — Full history preview", fontsize=9, color=GRAY, pad=4)
    ax_hist.set_ylabel("VIX Level", fontsize=8)
    ax_hist.tick_params(labelsize=7)
    ax_hist.grid(True, linewidth=0.4, alpha=0.5)
    section_label(ax_hist, "Full history")

    # percentile table (right-bottom)
    ax_pct = fig.add_axes([0.47, 0.12, 0.5, 0.18])
    pct_rows = [
        (f"p{p}", f"{vix.quantile(p/100):.1f}")
        for p in [10, 25, 50, 75, 90, 95, 99]
    ]
    kv_table(ax_pct, pct_rows, ["Percentile", "VIX Level"], [0.3, 0.7])
    section_label(ax_pct, "Distribution percentiles")

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Page 3 — EDA: Full History
# ─────────────────────────────────────────────────────────────────────────────
def page_eda_history(pdf: PdfPages) -> None:
    fig = new_page(pdf, "Phase 2  —  EDA: Full History",
                   "Shaded regions mark four major volatility regimes")

    ax_img = fig.add_axes([0.03, 0.30, 0.94, 0.58])
    embed_img(ax_img, FIGURES / "vix_full_history.png")

    commentary = (
        "Mean-reversion:  VIX repeatedly spikes and decays toward a long-run level near 20. "
        "It cannot trend indefinitely — high implied volatility suppresses option demand and is "
        "self-correcting, confirming economic stationarity.\n\n"
        "Spike asymmetry:  Rises are abrupt; decays are slow and protracted. This creates a "
        "right-skewed level distribution and makes spike onset the hardest forecasting problem — "
        "all three models will be evaluated on this explicitly.\n\n"
        "Regime heterogeneity:  The four shaded periods account for the majority of extreme "
        "readings. The quiet 2012–2017 regime would produce misleadingly optimistic models if "
        "used as the sole training window."
    )
    body_text(fig, 0.04, 0.27, commentary, fontsize=9)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Page 4 — EDA: Distribution & Autocorrelation
# ─────────────────────────────────────────────────────────────────────────────
def page_eda_dist_acf(pdf: PdfPages) -> None:
    fig = new_page(pdf, "Phase 2  —  EDA: Distribution & Autocorrelation")

    ax_dist = fig.add_axes([0.03, 0.08, 0.44, 0.78])
    embed_img(ax_dist, FIGURES / "vix_distribution.png")

    ax_acf = fig.add_axes([0.50, 0.08, 0.48, 0.78])
    embed_img(ax_acf, FIGURES / "vix_acf_pacf.png")

    fig.text(0.04, 0.055,
             f"Skewness: {vix.skew():.2f}   Excess kurtosis: {vix.kurtosis():.2f}   "
             "→ strongly right-skewed, fat tails; Gaussian assumption is inappropriate.",
             fontsize=8.5, color=DARK)
    fig.text(0.50, 0.055,
             "ACF decays very slowly → high persistence.  "
             "PACF cuts off after lag 1–2 → AR(1)/AR(2) structure.  "
             "No visible weekly (lag-5) spike.",
             fontsize=8.5, color=DARK)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Page 5 — Stationarity
# ─────────────────────────────────────────────────────────────────────────────
def page_stationarity(pdf: PdfPages) -> None:
    fig = new_page(pdf, "Phase 3  —  Stationarity Testing",
                   "ADF (H₀: unit root) × KPSS (H₀: stationary) cross-check")

    ax_img = fig.add_axes([0.03, 0.42, 0.94, 0.45])
    embed_img(ax_img, FIGURES / "vix_level_vs_diff.png")

    # Results table
    ax_tbl = fig.add_axes([0.03, 0.08, 0.60, 0.29])
    tbl_rows = [
        ("VIX level",       "ADF", f"{adf_level['statistic']}",
         f"{adf_level['p_value']:.4f}",  adf_level["conclusion"]),
        ("VIX level",       "KPSS", f"{kpss_level['statistic']}",
         f"{kpss_level['p_value']:.4f}", kpss_level["conclusion"]),
        ("First difference","ADF", f"{adf_diff['statistic']}",
         f"{adf_diff['p_value']:.4f}",  adf_diff["conclusion"]),
        ("First difference","KPSS", f"{kpss_diff['statistic']}",
         f"{kpss_diff['p_value']:.4f}", kpss_diff["conclusion"]),
    ]
    kv_table(ax_tbl, tbl_rows,
             ["Series", "Test", "Statistic", "p-value", "Conclusion"],
             [0.2, 0.1, 0.15, 0.13, 0.42])
    section_label(ax_tbl, "Test results  (5% significance level)")

    # Decision box
    ax_dec = fig.add_axes([0.66, 0.08, 0.31, 0.29])
    ax_dec.set_facecolor(LBLUE)
    ax_dec.axis("off")
    ax_dec.text(0.5, 0.75, "Decision", ha="center", fontsize=10,
                fontweight="bold", color=BLUE, transform=ax_dec.transAxes)
    ax_dec.text(0.5, 0.52, "Both tests agree:", ha="center", fontsize=9,
                color=DARK, transform=ax_dec.transAxes)
    ax_dec.text(0.5, 0.35, "VIX levels are stationary", ha="center",
                fontsize=10, fontweight="bold", color=GREEN, transform=ax_dec.transAxes)
    ax_dec.text(0.5, 0.17, "d = 0  ·  Model in levels\nARIMA(p, 0, q)  with p ∈ {1, 2}",
                ha="center", fontsize=9, color=DARK, transform=ax_dec.transAxes)
    rect = patches.FancyBboxPatch((0.01, 0.01), 0.98, 0.98,
                                   boxstyle="round,pad=0.02",
                                   linewidth=1.5, edgecolor=BLUE,
                                   facecolor="none",
                                   transform=ax_dec.transAxes)
    ax_dec.add_patch(rect)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Page 6 — Baseline Model & Roadmap
# ─────────────────────────────────────────────────────────────────────────────
def page_baseline(pdf: PdfPages) -> None:
    fig = new_page(pdf, "Phase 4  —  Baseline Model & Project Roadmap")

    # Baseline description
    ax_bl = fig.add_axes([0.03, 0.55, 0.44, 0.31])
    bl_rows = [
        ("Model",           "NaiveForecaster  (persistence / random walk)"),
        ("Forecast rule",   "Repeat last observed VIX for all h steps"),
        ("Horizons",        "1 · 5 · 21 trading days"),
        ("Interface",       "fit(series)  ·  predict(horizon) -> np.ndarray"),
        ("Role",            "Performance floor — every model must beat this"),
    ]
    kv_table(ax_bl, bl_rows, ["Property", "Detail"], [0.25, 0.75])
    section_label(ax_bl, "Baseline model")

    # Example forecast box
    ax_ex = fig.add_axes([0.50, 0.55, 0.47, 0.31])
    ax_ex.set_facecolor(LGRAY)
    ax_ex.axis("off")
    section_label(ax_ex, "Example forecast  (training cutoff: 2024-12-31)")
    ax_ex.text(0.04, 0.78,
               "Last observed value:  VIX = 17.35",
               transform=ax_ex.transAxes, fontsize=9.5, color=DARK, fontweight="bold")
    for i, (h, val) in enumerate([(1, "→  [17.35]"),
                                   (5, "→  [17.35, 17.35, 17.35, 17.35, 17.35]"),
                                   (21,"→  [17.35 × 21]")]):
        ax_ex.text(0.04, 0.58 - i * 0.20,
                   f"predict(horizon={h:2d})  {val}",
                   transform=ax_ex.transAxes, fontsize=9,
                   color=DARK, family="monospace")

    # Roadmap table
    ax_road = fig.add_axes([0.03, 0.08, 0.94, 0.40])
    road_rows = [
        ("0", "Scaffolding",            "Complete", "Repo structure, stubs, config, gitignore"),
        ("1", "Data Acquisition",       "Complete", f"^VIX via yfinance  ·  {len(vix):,} rows  ·  1 known gap (9/11)"),
        ("2", "Preprocessing + EDA",    "Complete", "Clean series  ·  History / distribution / ACF-PACF plots"),
        ("3", "Stationarity Testing",   "Complete", "ADF + KPSS agree: stationary in levels  →  d = 0"),
        ("4", "Baseline Model",         "Complete", "NaiveForecaster  ·  all three horizons  ·  interface verified"),
        ("5", "ARIMA / SARIMA",         "Upcoming", "AR(1/2) on levels  ·  test weekly seasonality  ·  AIC/BIC selection"),
        ("6", "Prophet",                "Upcoming", "Cross-check on seasonality conclusion from Phase 5"),
        ("7", "Walk-forward Backtest",  "Upcoming", "RMSE · MAE · MAPE · directional accuracy  ·  per-horizon results"),
        ("8", "Results & Packaging",    "Upcoming", "Final comparison table  ·  honest failure analysis  ·  README"),
    ]
    kv_table(ax_road, road_rows,
             ["Phase", "Name", "Status", "Key deliverable / finding"],
             [0.07, 0.20, 0.12, 0.61])
    section_label(ax_road, "Project roadmap")

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Assemble
# ─────────────────────────────────────────────────────────────────────────────
with PdfPages(OUTPUT) as pdf:
    page_cover(pdf)
    page_data(pdf)
    page_eda_history(pdf)
    page_eda_dist_acf(pdf)
    page_stationarity(pdf)
    page_baseline(pdf)

print(f"Report saved: {OUTPUT}")
