"""
CWP-style technical report generator for the VIX Forecasting project.

Replicates the aesthetic of the Colorado School of Mines Center for Wave Phenomena
report template (cwpreport2020.cls):
  - Times-Roman, 9pt body text
  - 8.5x11in portrait, 6.5in text width
  - UPPERCASE BOLD section headers (numbered)
  - Abstract as indented block
  - "Figure N." bold caption prefix
  - Running header: short title / page number
  - Journal identifier (VIX-001) on title page
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable,
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).parent.parent
FIGURES = ROOT / "figures"
OUTPUT  = ROOT / "reports" / "vix_forecasting_report.pdf"

# ---------------------------------------------------------------------------
# Page geometry (matching cwpreport2020.cls)
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter           # 8.5 x 11 in
L_MARGIN  = 1.015625 * inch
R_MARGIN  = 1.015625 * inch
T_MARGIN  = 0.75 * inch           # topmargin=-0.25 => 1in header - 0.25 = 0.75
B_MARGIN  = 1.5  * inch
TXT_W     = PAGE_W - L_MARGIN - R_MARGIN   # 6.469375 in ~ 6.5 in
TXT_H     = PAGE_H - T_MARGIN - B_MARGIN   # 8.75 in

SHORT_TITLE = "VIX Forecasting: Classical Time Series Methods"
JOURNAL_ID  = "VIX-001"

# ---------------------------------------------------------------------------
# Styles — Times-Roman family, 9pt body (matching CWP)
# ---------------------------------------------------------------------------
_TF  = "Times-Roman"
_TFB = "Times-Bold"
_TFI = "Times-Italic"
_TFBI = "Times-BoldItalic"

BODY_SIZE    = 9
CAPTION_SIZE = 8
HEADER_SIZE  = 8
TITLE_SIZE   = 16
AUTHOR_SIZE  = 11
SECTION_SIZE = 9
LEAD         = 12   # 12pt leading for 9pt body, matching \baselineskip

def _style(name, **kw):
    defaults = dict(
        fontName=_TF, fontSize=BODY_SIZE, leading=LEAD,
        alignment=TA_JUSTIFY, spaceAfter=4,
    )
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

styles = {
    "title": _style("title",
        fontName=_TFB, fontSize=TITLE_SIZE, leading=20,
        alignment=TA_CENTER, spaceAfter=8),
    "subtitle": _style("subtitle",
        fontName=_TFI, fontSize=AUTHOR_SIZE, leading=15,
        alignment=TA_CENTER, spaceAfter=4),
    "affil": _style("affil",
        fontName=_TFI, fontSize=9, leading=12,
        alignment=TA_CENTER, spaceAfter=2),
    "journal": _style("journal",
        fontName=_TFB, fontSize=9, leading=12,
        alignment=TA_CENTER, spaceAfter=0),
    "abstract_label": _style("abstract_label",
        fontName=_TFB, fontSize=BODY_SIZE, leading=LEAD,
        leftIndent=0.5*inch, spaceAfter=2),
    "abstract": _style("abstract",
        fontName=_TFI, fontSize=BODY_SIZE, leading=LEAD,
        leftIndent=0.5*inch, rightIndent=0.5*inch,
        alignment=TA_JUSTIFY, spaceAfter=6),
    "keywords": _style("keywords",
        fontName=_TF, fontSize=BODY_SIZE, leading=LEAD,
        leftIndent=0.5*inch, spaceAfter=10),
    "section": _style("section",
        fontName=_TFB, fontSize=SECTION_SIZE, leading=LEAD,
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=2),
    "subsection": _style("subsection",
        fontName=_TFB, fontSize=BODY_SIZE, leading=LEAD,
        alignment=TA_LEFT, spaceBefore=6, spaceAfter=2),
    "body": _style("body"),
    "body_noindent": _style("body_noindent", firstLineIndent=0),
    "caption": _style("caption",
        fontName=_TF, fontSize=CAPTION_SIZE, leading=10,
        alignment=TA_LEFT, spaceAfter=8),
    "table_head": _style("table_head",
        fontName=_TFB, fontSize=CAPTION_SIZE, leading=10,
        alignment=TA_CENTER),
    "table_cell": _style("table_cell",
        fontName=_TF, fontSize=CAPTION_SIZE, leading=10,
        alignment=TA_CENTER),
    "equation": _style("equation",
        fontName=_TF, fontSize=BODY_SIZE, leading=LEAD,
        alignment=TA_CENTER, leftIndent=0.5*inch, spaceAfter=6),
}

def S(style_name): return styles[style_name]

def sec(n, title):
    return Paragraph(f"{n}. {title.upper()}", S("section"))

def subsec(n, m, title):
    return Paragraph(f"{n}.{m} {title}", S("subsection"))

def body(text):
    return Paragraph(text, S("body"))

def body0(text):
    return Paragraph(text, S("body_noindent"))

def space(h=6):
    return Spacer(1, h)

_fig_counter = [0]

def fig_caption(text):
    _fig_counter[0] += 1
    n = _fig_counter[0]
    return Paragraph(
        f'<b>Figure {n}.</b> {text}',
        S("caption")
    )

def embed_figure(fname, width_frac=0.92, caption_text=None, max_height=None):
    from PIL import Image as PILImage
    path = FIGURES / fname
    w = TXT_W * width_frac
    with PILImage.open(str(path)) as im:
        iw, ih = im.size
    h = w * ih / iw
    if max_height and h > max_height:
        h = max_height
        w = h * iw / ih
    items = [Image(str(path), width=w, height=h)]
    if caption_text:
        items.append(fig_caption(caption_text))
    return KeepTogether(items)

# ---------------------------------------------------------------------------
# Page templates — headers / footers
# ---------------------------------------------------------------------------
def _header_footer_first(canvas, doc):
    canvas.saveState()
    # Journal ID top right
    canvas.setFont(_TFB, HEADER_SIZE)
    canvas.drawRightString(PAGE_W - R_MARGIN, PAGE_H - 0.5*inch, JOURNAL_ID)
    # Horizontal rule below journal ID
    canvas.setLineWidth(0.5)
    canvas.line(L_MARGIN, PAGE_H - 0.58*inch, PAGE_W - R_MARGIN, PAGE_H - 0.58*inch)
    # No page number on title page
    canvas.restoreState()

def _header_footer(canvas, doc):
    canvas.saveState()
    # Horizontal rule at top
    canvas.setLineWidth(0.5)
    y_rule = PAGE_H - 0.5 * inch
    canvas.line(L_MARGIN, y_rule, PAGE_W - R_MARGIN, y_rule)
    # Short title on left
    canvas.setFont(_TFI, HEADER_SIZE)
    canvas.drawString(L_MARGIN, PAGE_H - 0.42 * inch, SHORT_TITLE)
    # Page number on right
    canvas.drawRightString(PAGE_W - R_MARGIN, PAGE_H - 0.42 * inch,
                           f"{doc.page}")
    # Bottom rule
    canvas.line(L_MARGIN, B_MARGIN - 0.15*inch,
                PAGE_W - R_MARGIN, B_MARGIN - 0.15*inch)
    canvas.restoreState()


class CWPDocTemplate(BaseDocTemplate):
    def build(self, flowables, **kw):
        frame_first = Frame(L_MARGIN, B_MARGIN, TXT_W, TXT_H, id="first",
                            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        frame_body  = Frame(L_MARGIN, B_MARGIN, TXT_W, TXT_H, id="body",
                            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        first_page  = PageTemplate(id="First", frames=[frame_first],
                                   onPage=_header_footer_first)
        later_pages = PageTemplate(id="Later", frames=[frame_body],
                                   onPage=_header_footer)
        self.addPageTemplates([first_page, later_pages])
        super().build(flowables, **kw)


# ---------------------------------------------------------------------------
# Report content
# ---------------------------------------------------------------------------
def build_content():
    story = []

    # ---- TITLE PAGE -------------------------------------------------------
    story.append(space(12))
    story.append(Paragraph(
        "VIX Volatility Index Forecasting Using Classical Time Series Methods:<br/>"
        "Walk-Forward Evaluation of Naive, ARIMA, and Prophet Models",
        S("title")))
    story.append(space(8))
    story.append(Paragraph("Mauricio Payan Marin", S("subtitle")))
    story.append(Paragraph(
        "Data Science Portfolio Project &bull; mauriciopayanmarin@gmail.com",
        S("affil")))
    story.append(space(4))
    story.append(HRFlowable(width=TXT_W, thickness=0.5, color=colors.black))
    story.append(space(8))

    # Abstract
    story.append(Paragraph("ABSTRACT", S("abstract_label")))
    story.append(Paragraph(
        "We evaluate three classical time series forecasting methods on the CBOE Volatility Index "
        "(VIX) at horizons of 1, 5, and 21 trading days using expanding-window walk-forward "
        "validation over a three-year test period (2023–2026, 36 monthly folds). A naive "
        "persistence baseline, ARIMA(1,0,2), and Facebook Prophet are benchmarked against each "
        "other on root mean squared error, mean absolute error, mean absolute percentage error, "
        "and step-by-step directional accuracy. Stationarity analysis confirms that VIX levels "
        "require no differencing (ADF p&lt;0.001, KPSS p=0.10); the dominant structure is a "
        "near-unit-root AR(1) coefficient of 0.984 with a long-run mean of approximately 19.3. "
        "ARIMA(1,0,2) achieves the best out-of-sample error across all horizons (h=1 RMSE=1.09, "
        "h=21 RMSE=3.04) and 69.4% directional accuracy at h=1, degrading to a coin flip at h=21. "
        "Prophet produces RMSE five times worse than ARIMA because its piecewise-linear trend "
        "decomposition is structurally incompatible with VIX&apos;s mean-reverting dynamics. "
        "Weekly seasonality is confirmed to be a real but negligible signal (0.44 VIX pts, 6% "
        "of the series standard deviation). Spike onset is not captured by any model tested, "
        "identifying the clear direction for future GARCH or regime-switching extensions.",
        S("abstract")))
    story.append(space(4))
    story.append(Paragraph(
        "<b>Keywords:</b> VIX, volatility forecasting, ARIMA, Prophet, walk-forward validation, "
        "stationarity, time series, financial econometrics",
        S("keywords")))
    story.append(HRFlowable(width=TXT_W, thickness=0.5, color=colors.black))

    # Force later-page template from page 2 onward
    story.append(PageBreak())

    # ---- 1. INTRODUCTION --------------------------------------------------
    story.append(sec(1, "Introduction"))
    story.append(body0(
        "The CBOE Volatility Index (VIX) measures the 30-day implied volatility of S&amp;P 500 "
        "options and is widely used as a real-time gauge of market fear and systemic risk. "
        "Accurate short-horizon VIX forecasts are commercially valuable for options pricing, "
        "risk management, and volatility trading strategies. Unlike equity returns, which are "
        "approximately unpredictable at short horizons, VIX exhibits strong positive "
        "autocorrelation, making it a natural candidate for classical time series methods."))
    story.append(body(
        "This report documents a complete forecasting pipeline built as a portfolio project, "
        "covering data acquisition, exploratory analysis, stationarity testing, model "
        "selection, and rigorously validated out-of-sample evaluation. Three models are compared: "
        "a naive persistence baseline (the simplest possible benchmark), ARIMA(1,0,2) (the best "
        "converged linear model selected by AIC), and Facebook Prophet (a decomposition-based "
        "model included to assess whether trend or seasonality components add value)."))
    story.append(body(
        "All evaluation uses expanding-window walk-forward validation with no static train/test "
        "split, mirroring how models would be deployed in practice: refitted on all available "
        "history each period and evaluated only on unseen future data. The methodology, "
        "codebase architecture, and documented negative results on seasonal ARIMA and Prophet "
        "trend bias are designed to carry forward into a subsequent live equity "
        "forecasting project."))
    story.append(space(4))

    # ---- 2. DATA ----------------------------------------------------------
    story.append(sec(2, "Data"))
    story.append(subsec(2, 1, "Source and Acquisition"))
    story.append(body0(
        "Daily VIX closing prices are downloaded from Yahoo Finance via the yfinance library "
        "(ticker: ^VIX), covering 1990-01-02 through 2026-06-17: 9,158 trading days. The CBOE "
        "first published the modern VIX methodology in 2003; the 1990 history is a backfill "
        "using the original VXO methodology on S&amp;P 100 options. No adjustments are made "
        "for this methodological change since both series share the same broad behavioral "
        "properties (mean reversion, right skew, volatility clustering)."))
    story.append(body(
        "A documented nine-day gap (2001-09-10 to 2001-09-17) corresponds to the NYSE closure "
        "following the September 11 attacks. This is a genuine market closure, not a data "
        "anomaly, and is preserved as-is rather than filled."))

    story.append(subsec(2, 2, "Descriptive Statistics"))
    story.append(body0(
        "Table 1 summarizes the key distributional properties of the full VIX series. "
        "The pronounced right skew (2.21) and excess kurtosis (8.72) reflect the occasional "
        "but extreme volatility spikes characteristic of the series, most notably the "
        "2008 Global Financial Crisis (VIX peak: 80.9), the 2020 COVID-19 onset (peak: 82.7), "
        "and more moderate episodes during the 2002 dot-com bust and 2022 equity selloff."))

    tbl_data = [
        [Paragraph(t, S("table_head")) for t in
         ["Statistic", "Value"]],
        [Paragraph("Observations", S("table_cell")),
         Paragraph("9,158 trading days", S("table_cell"))],
        [Paragraph("Date range", S("table_cell")),
         Paragraph("1990-01-02 to 2026-06-17", S("table_cell"))],
        [Paragraph("Mean", S("table_cell")),
         Paragraph("19.52", S("table_cell"))],
        [Paragraph("Median", S("table_cell")),
         Paragraph("17.09", S("table_cell"))],
        [Paragraph("Std. deviation", S("table_cell")),
         Paragraph("7.75", S("table_cell"))],
        [Paragraph("Skewness", S("table_cell")),
         Paragraph("2.21 (strong right skew)", S("table_cell"))],
        [Paragraph("Excess kurtosis", S("table_cell")),
         Paragraph("8.72 (heavy tails)", S("table_cell"))],
        [Paragraph("Min / Max", S("table_cell")),
         Paragraph("8.56 / 82.69", S("table_cell"))],
        [Paragraph("90th percentile", S("table_cell")),
         Paragraph("29.49", S("table_cell"))],
    ]
    tbl = Table(tbl_data, colWidths=[2.2*inch, 3.5*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DDDDDD")),
        ("FONTNAME",   (0,0), (-1,-1), _TF),
        ("FONTSIZE",   (0,0), (-1,-1), CAPTION_SIZE),
        ("LEADING",    (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "LEFT"),
        ("LEFTPADDING",(0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0),(-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F5F5F5")]),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID",  (0,0), (-1,-1), 0.25, colors.grey),
    ]))
    story.append(space(4))
    story.append(KeepTogether([
        tbl,
        Paragraph("<b>Table 1.</b> Descriptive statistics for the full VIX series (1990–2026).",
                  S("caption")),
    ]))
    story.append(space(4))

    story.append(embed_figure("vix_full_history.png", 0.98,
        "Full VIX history (1990–2026) with annotated volatility regimes. "
        "Four crisis periods are highlighted: Dot-com bust (2000–2002), "
        "Global Financial Crisis (2007–2009), COVID-19 onset (2020), and "
        "2022 equity selloff.", max_height=2.8*inch))
    story.append(space(2))
    story.append(embed_figure("vix_distribution.png", 0.82,
        "VIX closing-price distribution. The histogram and kernel density "
        "estimate illustrate the pronounced right skew. Dashed lines mark "
        "the 25th, 50th, 75th, and 90th percentiles.", max_height=3.0*inch))
    story.append(space(4))

    # ---- 3. STATIONARITY ANALYSIS ----------------------------------------
    story.append(sec(3, "Stationarity Analysis"))
    story.append(body0(
        "Correct specification of the integration order d is foundational for ARIMA model "
        "selection. VIX's slow autocorrelation decay (Figure 3) is often interpreted as "
        "evidence of a unit root, but the same appearance arises from near-unit-root "
        "stationarity, a distinction with important economic content."))

    story.append(subsec(3, 1, "Formal Tests"))
    story.append(body0(
        "Two complementary tests are applied. The Augmented Dickey-Fuller (ADF) test has "
        "H<sub>0</sub>: the series contains a unit root. The KPSS test reverses the null: "
        "H<sub>0</sub>: the series is stationary. Table 2 reports results for VIX levels and "
        "first differences."))

    tbl2_data = [
        [Paragraph(t, S("table_head")) for t in
         ["Series", "ADF statistic", "ADF p-value", "KPSS statistic", "KPSS p-value", "Conclusion"]],
        [Paragraph("VIX levels", S("table_cell")),
         Paragraph("−3.81", S("table_cell")),
         Paragraph("0.003", S("table_cell")),
         Paragraph("0.134", S("table_cell")),
         Paragraph("~0.10", S("table_cell")),
         Paragraph("Stationary (d=0)", S("table_cell"))],
        [Paragraph("VIX first diff.", S("table_cell")),
         Paragraph("−44.1", S("table_cell")),
         Paragraph("<0.001", S("table_cell")),
         Paragraph("0.020", S("table_cell")),
         Paragraph(">0.10", S("table_cell")),
         Paragraph("Stationary", S("table_cell"))],
    ]
    tbl2 = Table(tbl2_data, colWidths=[1.0*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.85*inch, 1.4*inch])
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DDDDDD")),
        ("FONTNAME",   (0,0), (-1,-1), _TF),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("LEADING",    (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("LEFTPADDING",(0,0), (-1,-1), 3),
        ("RIGHTPADDING",(0,0),(-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F5F5F5")]),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID",  (0,0), (-1,-1), 0.25, colors.grey),
    ]))
    story.append(space(4))
    story.append(KeepTogether([
        tbl2,
        Paragraph(
            "<b>Table 2.</b> Stationarity test results. Both ADF (reject H<sub>0</sub> of unit root) "
            "and KPSS (fail to reject H<sub>0</sub> of stationarity) agree: VIX levels are stationary. "
            "Integration order d=0.",
            S("caption")),
    ]))
    story.append(space(4))
    story.append(body0(
        "Both tests agree: VIX levels are stationary (d=0). Economically, VIX is "
        "mean-reverting: a structural floor from options pricing mechanics prevents it from "
        "falling indefinitely, while the impossibility of sustained extreme implied volatility "
        "caps prolonged spikes. Near-unit-root persistence (AR &#8776; 0.984) produces the "
        "slow ACF decay but does not indicate a true stochastic trend."))

    story.append(embed_figure("vix_level_vs_diff.png", 0.98,
        "VIX levels vs first differences. Left panels: time series. Right panels: ACF. "
        "The level series has persistent but damped autocorrelation consistent with "
        "near-unit-root stationarity; first differences show rapid ACF decay.",
        max_height=3.2*inch))
    story.append(space(4))
    story.append(embed_figure("vix_acf_pacf.png", 0.82,
        "Autocorrelation (ACF) and partial autocorrelation (PACF) of VIX levels. "
        "The PACF cuts off after lag 1–2, suggesting a low-order AR process.",
        max_height=2.8*inch))
    story.append(space(4))

    # ---- 4. MODELS --------------------------------------------------------
    story.append(sec(4, "Models"))

    story.append(subsec(4, 1, "Naive Persistence Baseline"))
    story.append(body0(
        "The persistence model forecasts the last observed value for all horizons:"))
    story.append(Paragraph(
        "&#375;<sub>t+h</sub> = y<sub>t</sub>,  h = 1, 2, ..., H",
        S("equation")))
    story.append(body0(
        "This model requires no estimation and provides a natural lower bound on achievable "
        "forecast error for a mean-reverting series with high positive autocorrelation. "
        "By construction, the naive model always forecasts zero change, yielding 0% "
        "directional accuracy under the step-by-step metric."))

    story.append(subsec(4, 2, "ARIMA(1,0,2)"))
    story.append(body0(
        "Order selection uses a grid search over ARIMA(p,0,q) with "
        "p ∈ {1,2,3}, q ∈ {0,1,2} fitted by maximum likelihood on the most recent "
        "2,000 observations (~8 years), minimizing AIC. The best converged model "
        "(ARIMA(3,0,2) had lower AIC but failed to converge) is ARIMA(1,0,2):"))
    story.append(Paragraph(
        "(1 &#8722; &#966;<sub>1</sub>L)(y<sub>t</sub> &#8722; &#956;) = "
        "(1 + &#952;<sub>1</sub>L + &#952;<sub>2</sub>L<sup>2</sup>)&#949;<sub>t</sub>",
        S("equation")))
    story.append(body0(
        "with intercept &#956; constrained so the implied long-run mean "
        "(&#956;/(1&#8722;&#966;<sub>1</sub>)) equals 19.3, close to the empirical mean of 19.5. "
        "Estimated coefficients: &#966;<sub>1</sub> = 0.984 (AR persistence), "
        "&#952;<sub>1</sub> = &#8722;0.21, &#952;<sub>2</sub> = 0.08 (MA short-run corrections)."))
    story.append(body(
        "<b>Seasonal order.</b> A SMA(1) term at lag 5 (weekly frequency) improved the "
        "selection-window AIC by 17 points, suggesting apparent weekly seasonality. When the "
        "same model is fitted on the full 36-year series, however, the SMA coefficient is "
        "0.0005 (p=0.923), statistically indistinguishable from zero. The final model is "
        "non-seasonal. The day-of-week pattern in raw VIX data is genuine but negligible: "
        "the Monday-to-Friday mean spread is only 0.44 VIX pts, or 6% of the series "
        "standard deviation."))

    story.append(subsec(4, 3, "Facebook Prophet"))
    story.append(body0(
        "Prophet decomposes the time series into trend, weekly seasonality, yearly seasonality, "
        "and irregular components using an additive model:"))
    story.append(Paragraph(
        "y<sub>t</sub> = g(t) + s<sup>(7)</sup>(t) + s<sup>(a)</sup>(t) + &#949;<sub>t</sub>",
        S("equation")))
    story.append(body0(
        "where g(t) is a piecewise-linear trend, s<sup>(7)</sup> and s<sup>(a)</sup> are "
        "weekly and yearly Fourier series, and &#949;<sub>t</sub> is the error term. "
        "Prophet is included as a competitor model and as a cross-check on the ARIMA "
        "seasonality finding."))
    story.append(body(
        "Prophet's weekly Fourier amplitude (~4 VIX pts) is approximately nine times the "
        "actual day-of-week effect in raw data, revealing Fourier overfitting of a small "
        "but genuine signal. This overfitting, combined with a structural mismatch between "
        "Prophet's piecewise-linear trend assumption and VIX's mean-reverting character, "
        "produces catastrophically large point forecast errors out of sample."))

    story.append(embed_figure("prophet_insample_fit.png", 0.95,
        "Prophet in-sample fit on the full VIX series. The model tracks the observed "
        "series but the trend component introduces a systematic upward level bias that "
        "persists into out-of-sample forecasts during the calm 2023–2026 test window.",
        max_height=3.0*inch))
    story.append(space(2))
    story.append(embed_figure("vix_day_of_week.png", 0.9,
        "Day-of-week pattern in VIX. Left: mean VIX level by day. Right: mean daily change "
        "by day. The real Monday premium (options pricing the weekend uncertainty gap) amounts "
        "to only 0.44 VIX pts peak-to-trough, far smaller than Prophet's modeled weekly "
        "amplitude of approximately 4 VIX pts.", max_height=2.6*inch))
    story.append(space(4))

    # ---- 5. WALK-FORWARD EVALUATION --------------------------------------
    story.append(sec(5, "Walk-Forward Evaluation"))
    story.append(body0(
        "All models are evaluated using an expanding-window walk-forward protocol to "
        "eliminate look-ahead bias and mirror live deployment conditions. The design "
        "parameters are given in Table 3."))

    tbl3_data = [
        [Paragraph(t, S("table_head")) for t in ["Parameter", "Value", "Rationale"]],
        [Paragraph("Full series length", S("table_cell")),
         Paragraph("9,158 obs", S("table_cell")),
         Paragraph("1990–2026, all available history", S("table_cell"))],
        [Paragraph("Test window size", S("table_cell")),
         Paragraph("756 obs (~3 years)", S("table_cell")),
         Paragraph("Sufficient folds; recent enough to be relevant", S("table_cell"))],
        [Paragraph("Step size", S("table_cell")),
         Paragraph("21 obs (monthly)", S("table_cell")),
         Paragraph("Monthly refit cadence; 36 folds total", S("table_cell"))],
        [Paragraph("Horizons evaluated", S("table_cell")),
         Paragraph("1, 5, 21 days", S("table_cell")),
         Paragraph("Daily, weekly, monthly trading horizons", S("table_cell"))],
        [Paragraph("Minimum train size", S("table_cell")),
         Paragraph("252 obs (1 year)", S("table_cell")),
         Paragraph("Minimum for reliable ARIMA estimation", S("table_cell"))],
        [Paragraph("Metrics", S("table_cell")),
         Paragraph("RMSE, MAE, MAPE, Dir Acc", S("table_cell")),
         Paragraph("Error magnitude + directional signal", S("table_cell"))],
    ]
    tbl3 = Table(tbl3_data, colWidths=[1.4*inch, 1.3*inch, 3.5*inch])
    tbl3.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DDDDDD")),
        ("FONTNAME",   (0,0), (-1,-1), _TF),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("LEADING",    (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "LEFT"),
        ("LEFTPADDING",(0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0),(-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F5F5F5")]),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID",  (0,0), (-1,-1), 0.25, colors.grey),
    ]))
    story.append(space(4))
    story.append(KeepTogether([
        tbl3,
        Paragraph("<b>Table 3.</b> Walk-forward evaluation design parameters.", S("caption")),
    ]))
    story.append(space(6))
    story.append(body0(
        "At each fold t, the model is fit on series[:t], then evaluated against "
        "series[t:t+h] for each horizon h. The directional accuracy metric operates "
        "step-by-step: at each step k within the h-step forecast, the predicted direction "
        "(±) is compared to the actual direction of change from the previous step's actual "
        "value. Steps where the actual move is exactly zero are excluded."))

    # ---- 6. RESULTS -------------------------------------------------------
    story.append(sec(6, "Results"))
    story.append(body0(
        "Table 4 reports mean metrics across all 36 folds. The figures that follow show "
        "the metric breakdown and a representative forecast-vs-actual comparison over the "
        "test window."))

    tbl4_data = [
        [Paragraph(t, S("table_head")) for t in
         ["Model", "h=1 RMSE", "h=5 RMSE", "h=21 RMSE",
          "h=1 MAE", "h=21 MAE", "h=1 DirAcc", "h=21 DirAcc"]],
        [Paragraph("Naive", S("table_cell")),
         Paragraph("1.175", S("table_cell")), Paragraph("1.900", S("table_cell")),
         Paragraph("3.250", S("table_cell")), Paragraph("1.175", S("table_cell")),
         Paragraph("2.705", S("table_cell")), Paragraph("0.0%", S("table_cell")),
         Paragraph("0.0%", S("table_cell"))],
        [Paragraph("ARIMA(1,0,2)", S("table_cell")),
         Paragraph("<b>1.090</b>", S("table_cell")), Paragraph("<b>1.808</b>", S("table_cell")),
         Paragraph("<b>3.045</b>", S("table_cell")), Paragraph("<b>1.090</b>", S("table_cell")),
         Paragraph("<b>2.528</b>", S("table_cell")), Paragraph("<b>69.4%</b>", S("table_cell")),
         Paragraph("<b>50.4%</b>", S("table_cell"))],
        [Paragraph("Prophet", S("table_cell")),
         Paragraph("5.637", S("table_cell")), Paragraph("5.957", S("table_cell")),
         Paragraph("6.242", S("table_cell")), Paragraph("5.637", S("table_cell")),
         Paragraph("5.843", S("table_cell")), Paragraph("66.7%", S("table_cell")),
         Paragraph("53.2%", S("table_cell"))],
    ]
    tbl4 = Table(tbl4_data,
                 colWidths=[1.0*inch,0.65*inch,0.65*inch,0.65*inch,0.65*inch,0.65*inch,0.7*inch,0.7*inch])
    tbl4.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DDDDDD")),
        ("FONTNAME",   (0,0), (-1,-1), _TF),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("LEADING",    (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("LEFTPADDING",(0,0), (-1,-1), 3),
        ("RIGHTPADDING",(0,0),(-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F5F5F5")]),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID",  (0,0), (-1,-1), 0.25, colors.grey),
        ("BACKGROUND", (0,2), (-1,2), colors.HexColor("#EEF4FB")),
    ]))
    story.append(space(4))
    story.append(KeepTogether([
        tbl4,
        Paragraph(
            "<b>Table 4.</b> Walk-forward evaluation results (mean across 36 folds). "
            "Bold = best per column. ARIMA(1,0,2) dominates on all error metrics at all horizons.",
            S("caption")),
    ]))
    story.append(space(6))

    story.append(embed_figure("backtest_metrics_comparison.png", 0.98,
        "Backtest metric comparison across models and horizons. Top row: RMSE and MAE "
        "(lower is better). Bottom row: MAPE and directional accuracy. Prophet’s RMSE "
        "and MAE are approximately 5x worse than ARIMA, placing it off the scale in "
        "the top panels.", max_height=3.5*inch))
    story.append(space(2))
    story.append(embed_figure("backtest_forecast_vs_actual.png", 0.98,
        "Walk-forward h=1 forecasts vs actual VIX over the 2023–2026 test window. "
        "The Naive and ARIMA models closely track actuals in calm regimes. "
        "Prophet forecasts are systematically elevated, reflecting the trend-level bias "
        "identified in the in-sample analysis.", max_height=3.5*inch))
    story.append(space(4))

    # ---- 7. RESIDUAL DIAGNOSTICS -----------------------------------------
    story.append(sec(7, "Residual Diagnostics"))
    story.append(body0(
        "Residual diagnostics were run on the ARIMA(1,0,2) model fitted to the full "
        "9,183-observation series. Three tests are reported: Ljung-Box "
        "(H<sub>0</sub>: residuals are white noise), Jarque-Bera "
        "(H<sub>0</sub>: residuals are normally distributed), and ARCH-LM "
        "(H<sub>0</sub>: residual variance is constant). All three reject their null hypotheses."))

    tbl_diag_data = [
        [Paragraph(t, S("table_head")) for t in ["Test", "Statistic", "p-value", "Conclusion"]],
        [Paragraph("Ljung-Box (lag=20)", S("table_cell")),
         Paragraph("91.07", S("table_cell")),
         Paragraph("&lt;0.001", S("table_cell")),
         Paragraph("Residual autocorrelation detected", S("table_cell"))],
        [Paragraph("Jarque-Bera", S("table_cell")),
         Paragraph("315,931", S("table_cell")),
         Paragraph("&lt;0.001", S("table_cell")),
         Paragraph("Non-normal residuals (fat tails + skew)", S("table_cell"))],
        [Paragraph("ARCH-LM (lag=12)", S("table_cell")),
         Paragraph("1,571.17", S("table_cell")),
         Paragraph("&lt;0.001", S("table_cell")),
         Paragraph("Variance clustering present (ARCH effects)", S("table_cell"))],
    ]
    tbl_diag = Table(tbl_diag_data, colWidths=[1.4*inch, 0.8*inch, 0.7*inch, 3.3*inch])
    tbl_diag.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DDDDDD")),
        ("FONTNAME",   (0,0), (-1,-1), _TF),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("LEADING",    (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "LEFT"),
        ("LEFTPADDING",(0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0),(-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F5F5F5")]),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID",  (0,0), (-1,-1), 0.25, colors.grey),
    ]))
    story.append(space(4))
    story.append(KeepTogether([
        tbl_diag,
        Paragraph(
            "<b>Table 6.</b> Residual diagnostic test results for ARIMA(1,0,2) fitted on the "
            "full VIX series. All three tests reject their null hypotheses.",
            S("caption")),
    ]))
    story.append(space(6))

    story.append(body0(
        "<b>Ljung-Box:</b> Q(20) = 91.07 (p&lt;0.001) indicates that residuals are not white "
        "noise — some autocorrelation structure remains uncaptured by ARIMA(1,0,2). This is "
        "typical of financial time series; a higher-order AR or MA term might reduce it "
        "marginally, but at the cost of overfitting a model already near its linear "
        "predictability ceiling."))
    story.append(body0(
        "<b>Jarque-Bera:</b> Skewness 2.23 and excess kurtosis 31.39 — extreme right skew and "
        "very fat tails. Spike-onset days (COVID March 2020, 2022 selloff) produce large "
        "positive residuals that are highly non-Gaussian. Point forecasts remain valid, but no "
        "probabilistic interpretation should be attached to model standard errors."))
    story.append(body0(
        "<b>ARCH-LM:</b> LM = 1571.17 (p&lt;0.001) confirms strong ARCH effects — residual "
        "variance clusters around volatility events. The natural extension is a GARCH(1,1) on "
        "ARIMA residuals, left for future work."))
    story.append(space(4))

    story.append(embed_figure("arima_residual_qq.png", 0.82,
        "Q-Q plot of ARIMA(1,0,2) residuals against the normal distribution. "
        "The heavy departure in both tails confirms the extreme kurtosis (31.4) reported "
        "by the Jarque-Bera test. Spike-onset days are responsible for the most extreme "
        "positive outliers.", max_height=3.0*inch))
    story.append(space(2))
    story.append(embed_figure("arima_residual_acf.png", 0.82,
        "ACF of ARIMA(1,0,2) residuals. Several lags exceed the 95% confidence band, "
        "consistent with the Ljung-Box Q(20) = 91.07 result. The pattern suggests "
        "remaining structure at weekly and monthly lags not captured by the AR(1)/MA(2) "
        "specification.", max_height=2.8*inch))
    story.append(space(6))

    # ---- 8. DISCUSSION ----------------------------------------------------
    story.append(sec(8, "Discussion"))

    story.append(subsec(8, 1, "ARIMA Performance"))
    story.append(body0(
        "ARIMA(1,0,2) outperforms the persistence baseline by approximately 7% on RMSE at "
        "all horizons, a modest but consistent margin sustained across 36 independent folds. "
        "Consistency across folds matters here: a lucky 7% from a single test split would be "
        "unreliable, but the same gap holding from 2023 to 2026 is structural. The MA(1) and "
        "MA(2) terms contribute roughly 2% of the gain; the properly estimated intercept "
        "(long-run mean anchor at 19.3) drives the remainder, especially at longer horizons."))
    story.append(body(
        "Directional accuracy falls from 69.4% at h=1 to 50.4% at h=21, which is "
        "mechanically expected. As h grows, AR-based forecasts converge to the model's "
        "implied long-run mean rather than tracking the path there, so predicted step-to-step "
        "changes become small and increasingly likely to contradict the actual short-term "
        "direction. At h=21, the 50.4% figure is statistically indistinguishable from random."))

    story.append(subsec(8, 2, "Prophet Failure Mode"))
    story.append(body0(
        "Prophet's RMSE of 5.64 at h=1 (vs 1.09 for ARIMA) traces to a fundamental "
        "assumption mismatch: piecewise-linear trend decomposition presupposes a long-run "
        "drift direction, while VIX is stationary and mean-reverting. During the 2023–2026 "
        "test window, VIX was predominantly in the 12–25 range; however, the trend fitted "
        "on training data that includes the 2020 COVID spike (82.7) anchors forecasts "
        "persistently above actuals. The overfitted weekly Fourier terms (~4 VIX pts amplitude "
        "vs 0.44 pts in raw data) add a secondary error, though the trend bias dominates."))
    story.append(body(
        "Prophet does achieve reasonable directional accuracy (66.7% at h=1), which suggests "
        "its trend-change components capture some signal about future direction. The problem "
        "is that correct direction with five times the magnitude error has limited practical "
        "value: trading signals derived from such forecasts would systematically size positions "
        "incorrectly, and risk estimates would be unreliable."))

    story.append(subsec(8, 3, "Spike Onset: Fundamental Limitation"))
    story.append(body0(
        "No model tested captures VIX spike onset. The 2023–2026 test window contained "
        "multiple sudden increases exceeding 3 points in a single day, each driven by "
        "exogenous macro or geopolitical events such as banking stress in March 2023, "
        "geopolitical escalations, and Federal Reserve communications. Linear time series "
        "models conditioned only on past VIX values cannot anticipate such shocks."))
    story.append(body(
        "Critically, this is not a failure of estimation or model selection. It reflects the "
        "intrinsic limits of univariate linear forecasting for a risk index whose extreme "
        "moves carry information external to the series. Addressing spike onset requires "
        "exogenous regressors (credit spreads, options flow imbalance, economic surprise "
        "indices) or a regime-switching framework with latent state estimation — two "
        "directions that future work can pursue with the evaluation harness already in place."))

    story.append(subsec(8, 4, "Extensions"))
    story.append(body0(
        "Several directions offer the highest marginal return given the results established here:"))
    ext_data = [
        ["GARCH(1,1) on VIX returns",
         "Models volatility clustering in the error term; gives conditional variance forecasts"],
        ["ARIMAX with credit spreads",
         "VIX co-moves with HY credit spreads; exogenous spread signal may improve spike detection"],
        ["Regime-switching AR",
         "Separate AR(1) dynamics for calm vs. crisis regimes using Markov chain state transitions"],
        ["LSTM with attention",
         "Non-linear patterns across longer lookback windows; suitable for multi-horizon joint prediction"],
    ]
    ext_tbl = Table(
        [[Paragraph(r[0], S("table_head")), Paragraph(r[1], S("table_cell"))]
         for r in ext_data],
        colWidths=[1.8*inch, 4.4*inch])
    ext_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), _TF),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("LEADING",    (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "LEFT"),
        ("LEFTPADDING",(0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0),(-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, colors.HexColor("#F5F5F5")]),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID",  (0,0), (-1,-1), 0.25, colors.grey),
    ]))
    story.append(space(4))
    story.append(KeepTogether([
        ext_tbl,
        Paragraph("<b>Table 5.</b> Recommended extensions to the classical linear framework.",
                  S("caption")),
    ]))
    story.append(space(6))

    # ---- 9. CONCLUSIONS ---------------------------------------------------
    story.append(sec(9, "Conclusions"))
    story.append(body0(
        "This study establishes a complete, rigorously validated baseline for VIX forecasting "
        "using classical time series methods. The key findings are:"))
    conclusions = [
        ("Stationarity:",
         "VIX levels are stationary (d=0), confirmed independently by both ADF and KPSS. "
         "The slow ACF decay reflects near-unit-root persistence (AR &#8776; 0.984), "
         "not a true stochastic trend."),
        ("Model selection:",
         "ARIMA(1,0,2) is the best-converged linear model by AIC. A weekly seasonal term "
         "appears beneficial on the order-selection window but collapses to near-zero "
         "(p=0.923) on the full series, a documented negative result."),
        ("Walk-forward results:",
         "ARIMA(1,0,2) achieves the best error across all three horizons (7% RMSE improvement "
         "over persistence) and 69.4% directional accuracy at h=1. By h=21, directional "
         "accuracy degrades to a coin flip as the mean-reversion signal dissipates."),
        ("Prophet failure:",
         "Prophet's trend decomposition is structurally incompatible with mean-reverting "
         "dynamics, producing five times worse RMSE than ARIMA. Without an explicit "
         "flat-trend or mean-reversion constraint, it is not suitable for VIX point forecasting."),
        ("Spike onset:",
         "No tested model predicts abrupt VIX spikes driven by exogenous events, "
         "an intrinsic limitation of univariate linear models rather than a solvable "
         "estimation problem."),
    ]
    for label, text in conclusions:
        story.append(body0(f"<b>{label}</b> {text}"))
        story.append(space(2))

    story.append(body(
        "The walk-forward harness and model interfaces developed here are designed for "
        "reuse in the subsequent capstone project on live equity return forecasting. "
        "The transferable lesson is straightforward: for mean-reverting financial indices, "
        "properly validated AR models with realistic baselines and documented negative "
        "results provide more honest and more useful forecasts than sophisticated "
        "decomposition approaches applied without attention to stationarity assumptions."))
    story.append(space(8))

    # ---- ACKNOWLEDGEMENTS -----------------------------------------------
    story.append(sec(10, "Acknowledgements"))
    story.append(body0(
        "VIX data sourced from Yahoo Finance via the yfinance open-source library. "
        "Statistical modeling uses statsmodels and prophet (Meta). Walk-forward "
        "evaluation infrastructure written in Python with pandas and NumPy. "
        "Report typeset in the style of the Center for Wave Phenomena (CWP) technical "
        "report series, Colorado School of Mines."))

    return story


# ---------------------------------------------------------------------------
# Build the PDF
# ---------------------------------------------------------------------------
def main():
    doc = CWPDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=L_MARGIN,
        rightMargin=R_MARGIN,
        topMargin=T_MARGIN,
        bottomMargin=B_MARGIN,
    )
    story = build_content()
    doc.build(story)
    print(f"Report written to: {OUTPUT}")


if __name__ == "__main__":
    main()
