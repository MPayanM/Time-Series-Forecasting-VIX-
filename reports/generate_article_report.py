"""
Portfolio article PDF — CUP-inspired layout, single-column body.

First page: full-width header block (badge · title · author · abstract box)
Body pages: single column, numbered sections with thin rules, running header.
"""

from pathlib import Path
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, NextPageTemplate, FrameBreak,
)
from reportlab.platypus.flowables import Flowable

ROOT    = Path(__file__).parent.parent
FIGURES = ROOT / "figures"
OUTPUT  = ROOT / "reports" / "vix_forecasting_article_en.pdf"

# ── Palette (black/gray only) ─────────────────────────────────────────────────
BLACK       = colors.HexColor("#1A1A1A")
DARK_GRAY   = colors.HexColor("#333333")
MID_GRAY    = colors.HexColor("#777777")
RULE_COLOR  = colors.HexColor("#CCCCCC")
ABSTRACT_BG = colors.HexColor("#EFEFEF")

# ── Page geometry ─────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = letter           # 612 × 792 pts
L_MAR  = 1.05 * inch
R_MAR  = 1.05 * inch
T_MAR  = 0.80 * inch
B_MAR  = 0.85 * inch
TXT_W  = PAGE_W - L_MAR - R_MAR  # ≈ 462 pts

# Page 1 uses a single full-height frame (title block + centred abstract, nothing else)
COL_H_BODY  = PAGE_H - T_MAR - B_MAR - 0.28 * inch
HEADER_H    = COL_H_BODY  # page-1 frame fills the entire body area

# ── Fonts ─────────────────────────────────────────────────────────────────────
TR  = "Times-Roman"
TB  = "Times-Bold"
TI  = "Times-Italic"
HVB = "Helvetica-Bold"
HV  = "Helvetica"

# ── Styles ────────────────────────────────────────────────────────────────────
def _st(name, **kw):
    base = dict(fontName=TR, fontSize=10, leading=14,
                alignment=TA_JUSTIFY, textColor=BLACK, spaceAfter=6)
    base.update(kw)
    return ParagraphStyle(name, **base)

# header block
S_badge   = _st("badge",   fontName=HVB, fontSize=7,   leading=9,
                 alignment=TA_LEFT, textColor=BLACK, spaceAfter=6, letterSpacing=1.5)
S_title   = _st("title",   fontName=TB,  fontSize=20,  leading=25,
                 alignment=TA_LEFT, textColor=BLACK, spaceAfter=6)
S_author  = _st("author",  fontName=TR,  fontSize=10,  leading=14,
                 alignment=TA_LEFT, textColor=BLACK, spaceAfter=2)
S_affil   = _st("affil",   fontName=TI,  fontSize=8.5, leading=12,
                 alignment=TA_LEFT, textColor=MID_GRAY, spaceAfter=2)
S_kw      = _st("kw",      fontName=TR,  fontSize=8.5, leading=12,
                 alignment=TA_LEFT, textColor=DARK_GRAY, spaceAfter=7)
S_abs_bod = _st("abs_bod", fontName=TR,  fontSize=9,   leading=13,
                 alignment=TA_JUSTIFY, textColor=BLACK, spaceAfter=0)

# body
S_body    = _st("body",    firstLineIndent=18)
S_body0   = _st("body0")
S_section = _st("section", fontName=TB,  fontSize=11,  leading=14,
                 alignment=TA_LEFT, textColor=BLACK, spaceBefore=14, spaceAfter=2)
S_caption = _st("caption", fontName=TI,  fontSize=8.5, leading=12,
                 alignment=TA_CENTER, textColor=MID_GRAY, spaceAfter=8)
S_cell    = _st("cell",    fontName=TR,  fontSize=8.5, leading=11,
                 alignment=TA_LEFT, textColor=BLACK, spaceAfter=0)
S_cellhd  = _st("cellhd",  fontName=TB,  fontSize=8.5, leading=11,
                 alignment=TA_LEFT, textColor=BLACK, spaceAfter=0)


def sp(h=6): return Spacer(1, h)

def hr(width=None, thickness=0.4, c=BLACK, **kw):
    return HRFlowable(width=width or TXT_W, thickness=thickness, color=c, **kw)


class _VPad(Flowable):
    """Consume (availH - inner_h) / 2 of vertical space so the content that
    follows lands vertically centred in whatever remains of the frame."""
    def __init__(self, inner_h):
        Flowable.__init__(self)
        self._inner_h = inner_h
    def wrap(self, aW, aH):
        self._h = max(0, (aH - self._inner_h) / 2)
        return aW, self._h
    def draw(self): pass
    def split(self, aW, aH): return []


_fig_n = [0]

def embed_fig(fname, caption_text, width_frac=0.92, max_h=None):
    w = TXT_W * width_frac
    path = FIGURES / fname
    with PILImage.open(str(path)) as im:
        iw, ih = im.size
    h = w * ih / iw
    if max_h and h > max_h:
        h = max_h
        w = h * iw / ih
    _fig_n[0] += 1
    img = Image(str(path), width=w, height=h)
    img.hAlign = "CENTER"
    return KeepTogether([
        sp(6),
        img,
        sp(3),
        Paragraph(f"<b>Figure {_fig_n[0]}.</b>  {caption_text}", S_caption),
        sp(6),
    ])


# ── Page canvas callbacks ─────────────────────────────────────────────────────
SHORT = "Forecasting Market Volatility"

def _cb_first(canvas, doc):
    canvas.saveState()
    y = PAGE_H - T_MAR + 0.22 * inch
    # Heavy top rule
    canvas.setStrokeColor(BLACK)
    canvas.setLineWidth(1.0)
    canvas.line(L_MAR, y, PAGE_W - R_MAR, y)
    # Portfolio label left | date right
    canvas.setFont(HVB, 6.5)
    canvas.setFillColor(BLACK)
    canvas.drawString(L_MAR, y + 0.07 * inch, "PORTFOLIO PROJECT 1 OF 5")
    canvas.setFont(HV, 6.5)
    canvas.setFillColor(MID_GRAY)
    canvas.drawRightString(PAGE_W - R_MAR, y + 0.07 * inch,
                           "Data Science Portfolio")
    canvas.restoreState()


def _cb_body(canvas, doc):
    canvas.saveState()
    y = PAGE_H - T_MAR + 0.22 * inch
    # Light top rule
    canvas.setStrokeColor(RULE_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(L_MAR, y, PAGE_W - R_MAR, y)
    # Running header: title left, page number right
    # Page 2 of the PDF shows "1", page 3 shows "2", etc.
    canvas.setFont(TI, 7.5)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(L_MAR, y + 0.07 * inch, SHORT)
    canvas.setFont(TR, 7.5)
    canvas.drawRightString(PAGE_W - R_MAR, y + 0.07 * inch, str(doc.page - 1))
    canvas.restoreState()


# ── Document template ─────────────────────────────────────────────────────────
class ArticleDoc(BaseDocTemplate):
    def build(self, flowables, **kw):
        # Page 1: single full-height frame — title block + centred abstract
        fr_page1 = Frame(
            L_MAR, B_MAR, TXT_W, HEADER_H,
            id="page1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        # Body pages: single full-width frame
        fr_body = Frame(
            L_MAR, B_MAR, TXT_W, COL_H_BODY,
            id="body", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        self.addPageTemplates([
            PageTemplate(id="First", frames=[fr_page1], onPage=_cb_first),
            PageTemplate(id="Body",  frames=[fr_body],  onPage=_cb_body),
        ])
        super().build(flowables, **kw)


# ── First-page header block ────────────────────────────────────────────────────
def header_block():
    s = []
    s.append(sp(2))
    # Badge — practical label, not academic
    s.append(Paragraph("FORECASTING STUDY", S_badge))
    s.append(hr(thickness=0.75, c=BLACK, spaceAfter=8))
    # Title
    s.append(Paragraph(
        "Forecasting Market Volatility: Where a Simple Model Helps, "
        "and Where It Quietly Breaks",
        S_title,
    ))
    # Author + affiliation
    s.append(Paragraph("Mauricio Payan", S_author))
    s.append(Paragraph(
        "Data Science Portfolio, 2026 · Time Series Forecasting Study",
        S_affil,
    ))
    s.append(sp(5))
    s.append(Paragraph(
        "<b>Keywords:</b>  VIX · ARIMA · Prophet · "
        "walk-forward validation · residual diagnostics · volatility forecasting",
        S_kw,
    ))
    # Abstract in gray box
    abs_para = Paragraph(
        "Can historical VIX data reliably predict where volatility is heading? "
        "This study puts three forecasting approaches head-to-head: a simple "
        "&#x201C;do-nothing&#x201D; baseline, a classical ARIMA model, and "
        "Meta&#x2019;s Prophet, tested across 36 monthly experiments on data "
        "from 2023 to 2026 at one-day, one-week, and one-month horizons. "
        "ARIMA edges out the baseline by about 7% at a one-day horizon, "
        "calling the right direction 69% of the time. Stretch that to one "
        "month, and the edge disappears: the model is no better than a coin "
        "flip. What turns out to be more instructive than the error numbers "
        "is what the mistakes look like. They are not random. The errors "
        "cluster around real market events, run far larger than any "
        "well-behaved model would predict, and compound during turbulent "
        "periods. That is not a flaw to paper over; it is a precise account "
        "of what a linear model can and cannot do with volatility data, and "
        "a starting point for building something better.",
        S_abs_bod,
    )
    abs_tbl = Table([[abs_para]], colWidths=[TXT_W])
    abs_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), ABSTRACT_BG),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
    ]))
    s.append(sp(8))
    s.append(abs_tbl)
    s.append(NextPageTemplate("Body"))
    s.append(FrameBreak())
    return s


# ── Body content ──────────────────────────────────────────────────────────────
def body_content():
    s = []

    # Unnumbered introduction
    s += [
        Paragraph(
            "This is the first of five data science projects building toward a "
            "live market-prediction dashboard. Beginning with volatility "
            "forecasting rather than something flashier is a deliberate choice: "
            "at this stage, the discipline of evaluating a model honestly matters "
            "more than how sophisticated it looks.",
            S_body0,
        ),
        Paragraph(
            "Most forecasting write-ups report a single error number and stop. "
            "This one keeps going, because the interesting question is not "
            "whether ARIMA can beat a naive baseline. It is where it stops being "
            "trustworthy, and why.",
            S_body,
        ),
    ]

    # 1. The VIX
    s += [
        KeepTogether([
            Paragraph("1.  The CBOE Volatility Index", S_section),
            hr(spaceAfter=6),
            Paragraph(
                "The VIX reflects 30-day implied volatility of S&amp;P&#x202F;500 "
                "options. In calm markets it tends to sit in the high teens; during "
                "genuine stress it can double or triple in a matter of days. "
                "Figure 1 covers the full history from 1990 to 2026.",
                S_body0,
            ),
        ]),
        embed_fig(
            "vix_full_history.png",
            "Full VIX history (1990&#x2013;2026). Four major spike regimes: "
            "dot-com bust, Global Financial Crisis, COVID-19 onset (March 2020), "
            "and the 2022 equity selloff.",
            max_h=3.0 * inch,
        ),
        Paragraph(
            "Two unit-root tests agree that VIX levels are stationary. The "
            "Augmented Dickey-Fuller test rejects the presence of a unit root "
            "(p&#x2248;0), while KPSS finds no evidence against stationarity "
            "(p&#x2248;0.10). No differencing is needed. Figure 2 shows the "
            "autocorrelation structure: the decay is slow, consistent with an "
            "AR(1) coefficient of around 0.984. The series is highly persistent, "
            "but it does not drift.",
            S_body,
        ),
        embed_fig(
            "vix_acf_pacf.png",
            "ACF and PACF of VIX levels. Slow ACF decay is consistent with "
            "AR(1)&#x2248;0.984 persistence; PACF cuts off at lag 2.",
            max_h=2.8 * inch,
        ),
    ]

    # 2. Model Selection
    s += [
        KeepTogether([
            Paragraph("2.  Model Selection", S_section),
            hr(spaceAfter=6),
            Paragraph(
                "Naive persistence simply carries today's value forward as "
                "tomorrow's forecast. It is the baseline every other model must beat "
                "to justify its existence.",
                S_body0,
            ),
        ]),
        Paragraph(
            "ARIMA(1,0,2) was chosen by AIC over a grid of candidate "
            "specifications fitted to the full 36-year history. Two alternatives "
            "were explicitly tested and set aside: a seasonal term at the weekly "
            "lag turned out to be essentially zero (coefficient 0.0005, p=0.923), "
            "and fitting on log-VIX instead of raw levels moved the error metrics "
            "by less than 2%. The level-scale ARIMA without seasonal terms is "
            "what the data supports.",
            S_body,
        ),
        Paragraph(
            "Prophet was included not as a serious competitor but as a "
            "test of a specific question: does VIX have weekly or annual "
            "seasonality? Its Fourier components were built for exactly this kind "
            "of structure. The results say no.",
            S_body,
        ),
    ]

    # 3. Walk-Forward Validation
    s += [
        KeepTogether([
            Paragraph("3.  Walk-Forward Validation", S_section),
            hr(spaceAfter=6),
            Paragraph(
                "Rather than a single train/test split, each model is re-estimated "
                "monthly using all data available up to that point, then asked to "
                "forecast one day, one week, and one month ahead on data it has never "
                "seen. The window advances 21 trading days at a time across three "
                "years of test data, producing 36 independent forecast exercises. "
                "Every performance number reported reflects how the model would "
                "actually behave in use.",
                S_body0,
            ),
        ]),
    ]

    # 4. Results
    s += [
        KeepTogether([
            Paragraph("4.  Results", S_section),
            hr(spaceAfter=6),
            Paragraph(
                "ARIMA(1,0,2) comes out ahead at every horizon on every metric "
                "(Figures 3 and 4). At one day out, the average error is about 1.09 "
                "VIX points, roughly 7% below the naive baseline, and the model "
                "calls the right direction 69% of the time. At five days the "
                "directional edge narrows to 56%, and at one month it reaches 50.4%: "
                "statistically indistinguishable from guessing.",
                S_body0,
            ),
        ]),
        Paragraph(
            "Prophet's performance at point forecasting is poor across the board, "
            "with RMSE running about five times higher than ARIMA at every "
            "horizon. Its additive trend component consistently pulls forecasts "
            "upward in low-volatility periods, chasing a long-run level that "
            "does not exist in a mean-reverting series. The weekly Fourier terms "
            "tell a similar story: VIX does have a small day-of-week pattern "
            "(about 0.44 points peak-to-trough), but Prophet amplifies it by a "
            "factor of nine. Its directional accuracy, oddly, stays close to "
            "ARIMA's throughout. Getting the magnitude right and getting the "
            "direction right are two separate problems.",
            S_body,
        ),
        embed_fig(
            "backtest_metrics_comparison.png",
            "Walk-forward metrics across all models and horizons. ARIMA(1,0,2) "
            "leads on all error metrics; Prophet's RMSE is &#x223C;5&#x00D7; larger.",
            max_h=3.2 * inch,
        ),
        embed_fig(
            "backtest_forecast_vs_actual.png",
            "h=1 walk-forward forecasts vs. actual VIX, 2023&#x2013;2026 test "
            "window. Prophet forecasts are systematically elevated.",
            max_h=3.2 * inch,
        ),
    ]

    # 5. Residual Diagnostics
    s += [
        KeepTogether([
            Paragraph("5.  Residual Diagnostics", S_section),
            hr(spaceAfter=6),
            Paragraph(
                "Three standard diagnostic tests were run on the residuals of "
                "ARIMA(1,0,2) fitted to the full history of 9,183 daily "
                "observations. All three reject their null hypotheses at "
                "p &lt; 0.001 (Table 1).",
                S_body0,
            ),
        ]),
    ]

    # Diagnostic table
    diag_data = [
        [Paragraph("<b>Test</b>", S_cellhd),
         Paragraph("<b>Statistic</b>", S_cellhd),
         Paragraph("<b>H<sub>0</sub> rejected</b>", S_cellhd)],
        [Paragraph("Ljung-Box Q(20)", S_cell),
         Paragraph("91.07", S_cell),
         Paragraph("Residuals are white noise", S_cell)],
        [Paragraph("Jarque-Bera", S_cell),
         Paragraph("315,931", S_cell),
         Paragraph("Residuals are Gaussian", S_cell)],
        [Paragraph("ARCH-LM (lag=12)", S_cell),
         Paragraph("1,571.17", S_cell),
         Paragraph("No variance clustering", S_cell)],
    ]
    c1, c2, c3 = TXT_W * 0.30, TXT_W * 0.18, TXT_W * 0.52
    dt = Table(diag_data, colWidths=[c1, c2, c3])
    dt.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4),
        ("LINEABOVE",     (0,0),(-1,0),  0.75, BLACK),
        ("LINEBELOW",     (0,0),(-1,0),  0.5,  BLACK),
        ("LINEBELOW",     (0,-1),(-1,-1),0.75, BLACK),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    tbl_cap = Paragraph(
        "<b>Table 1.</b>  Residual diagnostic tests on ARIMA(1,0,2) fitted to "
        "the full history (n = 9,183). All reject at p &lt; 0.001.",
        S_caption,
    )
    s.append(KeepTogether([sp(4), dt, sp(4), tbl_cap, sp(6)]))

    s += [
        Paragraph(
            "The residuals are fat-tailed (excess kurtosis of 31.4, skewness "
            "of 2.23) and their variance is not constant: calm stretches produce "
            "small errors, and volatile stretches produce runs of large ones. "
            "None of this disqualifies the point forecasts, but it does mean "
            "the model's confidence intervals should not be taken seriously.",
            S_body,
        ),
        embed_fig(
            "arima_residual_qq.png",
            "Q-Q plot of ARIMA(1,0,2) residuals vs. the normal distribution. "
            "Heavy tails in both directions confirm excess kurtosis of 31.4.",
            width_frac=0.72, max_h=3.0 * inch,
        ),
        embed_fig(
            "arima_residual_acf.png",
            "ACF of ARIMA(1,0,2) residuals. Several lags breach the 95% "
            "confidence band, consistent with Ljung-Box Q(20) = 91.07.",
            width_frac=0.72, max_h=2.7 * inch,
        ),
    ]

    # 6. Discussion
    s += [
        KeepTogether([
            Paragraph("6.  Discussion", S_section),
            hr(spaceAfter=6),
            Paragraph(
                "What the diagnostics add up to is a fairly clear agenda for what "
                "comes next. Persistent variance clustering is a textbook case for "
                "a GARCH model layered on top of the ARIMA residuals, which would "
                "give the variance its own equation rather than treating it as "
                "constant. Spike prediction is a harder problem. VIX shocks are "
                "triggered by external events (rate decisions, credit blowups, "
                "geopolitical crises) that leave no fingerprint in historical VIX "
                "values themselves. Getting ahead of those moves would require "
                "bringing in outside data: credit spreads, options-positioning "
                "indicators, macro surprise indices. That is a different project.",
                S_body0,
            ),
        ]),
        Paragraph(
            "The evaluation harness built here is model-agnostic and carries "
            "forward into the rest of this portfolio: a momentum strategy "
            "backtest, a Monte Carlo risk model, and eventually a live "
            "forecasting dashboard. The real output of this study is not an "
            "ARIMA model. It is a documented, testable account of where the "
            "limits of linear forecasting sit for this particular series.",
            S_body,
        ),
    ]

    # 7. Conclusions
    s += [
        KeepTogether([
            Paragraph("7.  Conclusions", S_section),
            hr(spaceAfter=6),
            Paragraph(
                "Of the three approaches tested, ARIMA(1,0,2) is the clear winner, "
                "consistently outperforming the naive baseline by around 7% on RMSE "
                "across all 36 monthly test folds. At a one-day horizon it gets the "
                "direction right roughly two thirds of the time; at one month, it is "
                "no better than a coin flip. The residual analysis tells the rest of "
                "the story: the errors are not random noise but structured departures "
                "driven by volatility spikes, clustered in time, and far "
                "heavier-tailed than a Gaussian model assumes. Taken together, these "
                "results define exactly where a linear approach reaches its ceiling "
                "with VIX, and what a more complete model would need to address.",
                S_body0,
            ),
        ]),
    ]

    return s


# ── Build ─────────────────────────────────────────────────────────────────────
def main():
    _fig_n[0] = 0
    doc = ArticleDoc(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=L_MAR, rightMargin=R_MAR,
        topMargin=T_MAR,  bottomMargin=B_MAR,
    )
    doc.build(header_block() + body_content())
    print(f"Written: {OUTPUT}")


if __name__ == "__main__":
    main()
