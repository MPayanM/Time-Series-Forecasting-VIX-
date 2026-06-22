"""
Portfolio article PDF — version française.
Même gabarit que la version anglaise (CUP-inspired, colonne unique).
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
OUTPUT  = ROOT / "reports" / "vix_forecasting_article_fr.pdf"

# ── Palette ───────────────────────────────────────────────────────────────────
BLACK       = colors.HexColor("#1A1A1A")
DARK_GRAY   = colors.HexColor("#333333")
MID_GRAY    = colors.HexColor("#777777")
RULE_COLOR  = colors.HexColor("#CCCCCC")
ABSTRACT_BG = colors.HexColor("#EFEFEF")

# ── Page geometry ─────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = letter
L_MAR  = 1.05 * inch
R_MAR  = 1.05 * inch
T_MAR  = 0.80 * inch
B_MAR  = 0.85 * inch
TXT_W  = PAGE_W - L_MAR - R_MAR

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
SHORT = "Prévoir la volatilité des marchés"

def _cb_first(canvas, doc):
    canvas.saveState()
    y = PAGE_H - T_MAR + 0.22 * inch
    canvas.setStrokeColor(BLACK)
    canvas.setLineWidth(1.0)
    canvas.line(L_MAR, y, PAGE_W - R_MAR, y)
    canvas.setFont(HVB, 6.5)
    canvas.setFillColor(BLACK)
    canvas.drawString(L_MAR, y + 0.07 * inch, "PORTEFEUILLE DATA SCIENCE · PROJET 1 SUR 5")
    canvas.setFont(HV, 6.5)
    canvas.setFillColor(MID_GRAY)
    canvas.drawRightString(PAGE_W - R_MAR, y + 0.07 * inch, "Portefeuille Data Science")
    canvas.restoreState()


def _cb_body(canvas, doc):
    canvas.saveState()
    y = PAGE_H - T_MAR + 0.22 * inch
    canvas.setStrokeColor(RULE_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(L_MAR, y, PAGE_W - R_MAR, y)
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


# ── Bloc d'en-tête (première page) ────────────────────────────────────────────
def header_block():
    s = []
    s.append(sp(2))
    s.append(Paragraph("ÉTUDE PRÉVISIONNELLE", S_badge))
    s.append(hr(thickness=0.75, c=BLACK, spaceAfter=8))
    s.append(Paragraph(
        "Prévoir la volatilité des marchés : "
        "ce qu’un modèle simple sait faire, "
        "et là où il échoue",
        S_title,
    ))
    s.append(Paragraph("Mauricio Payan", S_author))
    s.append(Paragraph(
        "Portefeuille Data Science, 2026 · Étude de prévision de séries temporelles",
        S_affil,
    ))
    s.append(sp(5))
    s.append(Paragraph(
        "<b>Mots-clés :</b>  VIX · ARIMA · Prophet · "
        "validation par fenêtre glissante · diagnostic des résidus · "
        "prévision de volatilité",
        S_kw,
    ))
    abs_para = Paragraph(
        "Peut-on prédire, à partir de l’historique du VIX, où "
        "la volatilité se dirige ? Cette étude compare trois approches: "
        "un modèle de référence naïve, un modèle ARIMA "
        "classique et Prophet de Meta, testés sur 36 exercices mensuels "
        "(2023&#x2013;2026) à des horizons d’un jour, une semaine et un "
        "mois. À un jour, ARIMA devance la référence d’environ "
        "7 % et indique la bonne direction 69 % du temps. À un mois, "
        "cet avantage s’évanouit: le modèle ne fait guère mieux "
        "qu’un tirage à pile ou face. Ce qui s’avère plus "
        "révélateur que les chiffres d’erreur, c’est la forme "
        "des écarts. Ils ne sont pas aléatoires. Ils se concentrent "
        "autour des événements de marché réels, dépassent "
        "largement ce qu’un modèle bien calibré devrait produire, et "
        "s’accumulent pendant les périodes de turbulence. Ce n’est "
        "pas un défaut à dissimuler ; c’est un diagnostic "
        "précis de ce qu’un modèle linéaire peut et ne peut pas "
        "faire avec les données de volatilité, et un point de départ "
        "pour construire quelque chose de plus solide.",
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




# ── Corps de l'article ────────────────────────────────────────────────────────
def body_content():
    s = []

    # Introduction (non numérotée)
    s += [
        Paragraph(
            "Ce projet est le premier d'une série de cinq, dont "
            "l'objectif final est un tableau de bord de prévision de "
            "marché en temps réel. Commencer par la prévision de "
            "volatilité plutôt que par quelque chose de plus ambitieux "
            "est un choix délibéré : à ce stade, la "
            "rigueur de l'évaluation compte plus que la sophistication "
            "du modèle.",
            S_body0,
        ),
        Paragraph(
            "La plupart des études de prévision s'arrêtent "
            "à un chiffre d'erreur. Celle-ci va plus loin, parce que "
            "la question intéressante n'est pas de savoir si ARIMA bat "
            "une référence naïve. C'est de savoir où il "
            "cesse d'être fiable, et pourquoi.",
            S_body,
        ),
    ]

    # 1. L'indice VIX
    s.append(KeepTogether([
        Paragraph("1.  L'indice de volatilité CBOE", S_section),
        hr(spaceAfter=6),
        Paragraph(
            "Le VIX mesure la volatilité implicite à 30 jours des "
            "options sur le S&amp;P 500. En période calme, il oscille "
            "généralement dans les vingtaines ; en période de "
            "stress, il peut doubler ou tripler en quelques jours. La Figure 1 "
            "couvre l'historique complet de 1990 à 2026.",
            S_body0,
        ),
    ]))
    s += [
        embed_fig(
            "vix_full_history.png",
            "Historique complet du VIX (1990&#x2013;2026). Quatre grands régimes "
            "de volatilité : l'éclatement de la bulle "
            "technologique, la crise financière mondiale, le début de "
            "la Covid-19 (mars 2020) et la correction boursière de 2022.",
            max_h=3.0 * inch,
        ),
        Paragraph(
            "Deux tests de racine unitaire s'accordent sur la stationnarité "
            "des niveaux du VIX. Le test de Dickey-Fuller augmenté rejette "
            "la présence d'une racine unitaire (H<sub>0</sub> : "
            "racine unitaire, p&#x2248;0), tandis que KPSS ne trouve pas "
            "d'argument contre la stationnarité (H<sub>0</sub> : "
            "série stationnaire, p&#x2248;0,10). Aucune différenciation "
            "n'est nécessaire. La Figure 2 montre la structure "
            "d'autocorrélation : la décroissance est lente, "
            "cohérente avec un coefficient AR(1) d'environ 0,984. La "
            "série est très persistante, mais elle ne dérive pas.",
            S_body,
        ),
        embed_fig(
            "vix_acf_pacf.png",
            "FAC et FACP des niveaux du VIX. La décroissance lente de la FAC "
            "est cohérente avec AR(1)&#x2248;0,984 ; la FACP se coupe "
            "après le retard 2.",
            max_h=2.8 * inch,
        ),
    ]

    # 2. Choix des modèles
    s.append(KeepTogether([
        Paragraph("2.  Choix des modèles", S_section),
        hr(spaceAfter=6),
        Paragraph(
            "La persistence naïve se contente de reporter la valeur du jour "
            "comme prévision du lendemain. C'est le plancher : "
            "tout modèle incapable de faire mieux ne justifie pas son "
            "existence.",
            S_body0,
        ),
    ]))
    s += [
        Paragraph(
            "ARIMA(1,0,2) a été retenu par minimisation de l'AIC "
            "sur une grille de spécifications candidates ajustées à "
            "l'historique complet de 36 ans. Deux alternatives ont été "
            "explicitement testées puis écartées : un terme "
            "saisonnier au retard hebdomadaire s'est révélé "
            "quasi nul (coefficient 0,0005, p = 0,923), et l'ajustement "
            "sur log-VIX plutôt que sur les niveaux bruts a modifié les "
            "métriques d'erreur de moins de 2 %. Le modèle ARIMA "
            "sans terme saisonnier, ajusté sur les niveaux, est ce que les "
            "données justifient.",
            S_body,
        ),
        Paragraph(
            "Prophet a été inclus non pas comme concurrent sérieux, "
            "mais pour répondre à une question précise : le VIX "
            "présente-t-il une saisonnalité hebdomadaire ou annuelle ? "
            "Ses composantes de Fourier ont été conçues pour ce type "
            "de structure. La réponse est non.",
            S_body,
        ),
    ]

    # 3. Validation par fenêtre glissante
    s.append(KeepTogether([
        Paragraph("3.  Validation par fenêtre glissante", S_section),
        hr(spaceAfter=6),
        Paragraph(
            "Plutôt qu'un découpage unique entraînement/test, "
            "chaque modèle est ré-estimé chaque mois sur l'ensemble "
            "des données disponibles jusqu'à cette date, puis "
            "interrogé sur un jour, une semaine et un mois de données "
            "qu'il n'a jamais vues. La fenêtre avance de 21 jours de "
            "bourse à la fois sur trois ans de données de test, produisant "
            "36 exercices de prévision indépendants. Chaque chiffre de "
            "performance rapporté reflète le comportement qu'aurait "
            "eu le modèle en conditions réelles.",
            S_body0,
        ),
    ]))

    # 4. Résultats
    s.append(KeepTogether([
        Paragraph("4.  Résultats", S_section),
        hr(spaceAfter=6),
        Paragraph(
            "ARIMA(1,0,2) arrive en tête à chaque horizon et sur chaque "
            "métrique (Figures 3 et 4). À un jour, l'erreur "
            "moyenne est d'environ 1,09 point de VIX, soit à peu près "
            "7 % en dessous de la référence naïve, et le modèle "
            "indique la bonne direction 69 % du temps. À cinq jours, "
            "l'avantage directionnel se réduit à 56 %, et à "
            "un mois il atteint 50,4 % : statistiquement "
            "indiscernable d'un tirage au sort.",
            S_body0,
        ),
    ]))
    s += [
        Paragraph(
            "Les performances de Prophet en prévision ponctuelle sont "
            "médiocres à tous les horizons, avec un RMSE environ cinq "
            "fois supérieur à celui d'ARIMA. Sa composante de "
            "tendance additive tire systématiquement les prévisions vers "
            "le haut en période de faible volatilité, cherchant un niveau "
            "de long terme qui n'existe pas dans une série à retour "
            "vers la moyenne. Les termes de Fourier hebdomadaires racontent une "
            "histoire similaire : le VIX présente bien un faible effet "
            "jour de la semaine (environ 0,44 point de crête à crête), "
            "mais Prophet l'amplifie d'un facteur neuf. Sa précision "
            "directionnelle, curieusement, reste proche de celle d'ARIMA. "
            "Bien estimer l'amplitude et bien estimer la direction sont deux "
            "problèmes distincts.",
            S_body,
        ),
        embed_fig(
            "backtest_metrics_comparison.png",
            "Métriques de backtest pour tous les modèles et horizons. "
            "ARIMA(1,0,2) domine sur toutes les métriques ; "
            "le RMSE de Prophet est environ 5 fois plus élevé.",
            max_h=3.2 * inch,
        ),
        embed_fig(
            "backtest_forecast_vs_actual.png",
            "Prévisions à un jour vs. VIX réalisé, "
            "fenêtre de test 2023&#x2013;2026. "
            "Les prévisions de Prophet sont systématiquement trop élevées.",
            max_h=3.2 * inch,
        ),
    ]

    # 5. Diagnostic des résidus
    s.append(KeepTogether([
        Paragraph("5.  Diagnostic des résidus", S_section),
        hr(spaceAfter=6),
        Paragraph(
            "Trois tests diagnostiques standards ont été appliqués "
            "aux résidus d'ARIMA(1,0,2) ajusté sur l'historique "
            "complet de 9 183 observations journalières. Les trois "
            "rejettent leurs hypothèses nulles à p &lt; 0,001 "
            "(Tableau 1).",
            S_body0,
        ),
    ]))

    # Tableau diagnostique
    diag_data = [
        [Paragraph("<b>Test</b>", S_cellhd),
         Paragraph("<b>Statistique</b>", S_cellhd),
         Paragraph("<b>H<sub>0</sub> rejetée</b>", S_cellhd)],
        [Paragraph("Ljung-Box Q(20)", S_cell),
         Paragraph("91,07", S_cell),
         Paragraph("Résidus non corrélés", S_cell)],
        [Paragraph("Jarque-Bera", S_cell),
         Paragraph("315 931", S_cell),
         Paragraph("Résidus gaussiens", S_cell)],
        [Paragraph("ARCH-LM (retard=12)", S_cell),
         Paragraph("1 571,17", S_cell),
         Paragraph("Absence d'effets ARCH", S_cell)],
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
        "<b>Tableau 1.</b>  Tests diagnostiques sur les résidus "
        "d'ARIMA(1,0,2) (n = 9 183). Tous rejettent "
        "à p &lt; 0,001.",
        S_caption,
    )
    s.append(KeepTogether([sp(4), dt, sp(4), tbl_cap, sp(6)]))

    s += [
        Paragraph(
            "Les résidus sont à queues épaisses (kurtosis "
            "excédentaire de 31,4, asymétrie de 2,23) et leur variance "
            "n'est pas constante : les périodes calmes produisent "
            "de petites erreurs, et les périodes agitées produisent des "
            "séries d'erreurs importantes. Cela ne disqualifie pas les "
            "prévisions ponctuelles, mais les intervalles de confiance du "
            "modèle ne méritent pas qu'on s'y fie.",
            S_body,
        ),
        embed_fig(
            "arima_residual_qq.png",
            "Graphique Q-Q des résidus d'ARIMA(1,0,2) vs. la loi normale. "
            "Les queues épaisses confirment un kurtosis excédentaire de 31,4.",
            width_frac=0.72, max_h=3.0 * inch,
        ),
        embed_fig(
            "arima_residual_acf.png",
            "FAC des résidus d'ARIMA(1,0,2). Plusieurs retards dépassent "
            "la bande de confiance à 95 %, cohérent avec "
            "Ljung-Box Q(20) = 91,07.",
            width_frac=0.72, max_h=2.7 * inch,
        ),
    ]

    # 6. Discussion
    s.append(KeepTogether([
        Paragraph("6.  Discussion", S_section),
        hr(spaceAfter=6),
        Paragraph(
            "Ce que les diagnostics indiquent, c'est un agenda assez clair "
            "pour la suite. La persistance de la variance des résidus appelle "
            "un modèle GARCH superposé aux résidus d'ARIMA, "
            "qui donnerait à la variance sa propre équation plutôt "
            "que de la traiter comme constante. La prédiction des pics est "
            "un problème différent. Les chocs du VIX sont déclenchés "
            "par des événements extérieurs (décisions de taux, "
            "crises de crédit, événements géopolitiques) qui ne "
            "laissent aucune empreinte dans l'historique du VIX lui-même. "
            "Anticiper ces mouvements nécessiterait des données externes: "
            "spreads de crédit, indicateurs de positionnement sur les options, "
            "indices de surprise macroéconomique. C'est un autre projet.",
            S_body0,
        ),
    ]))
    s += [
        Paragraph(
            "Le dispositif d'évaluation construit ici est agnostique "
            "quant au modèle et s'applique directement aux projets "
            "suivants de ce portefeuille : un backtest de stratégie "
            "momentum, un modèle de risque Monte Carlo et, à terme, un "
            "tableau de bord de prévision en temps réel. Le vrai "
            "livrable de cette étude n'est pas un modèle ARIMA. "
            "C'est un compte rendu documenté et testable des limites de "
            "la prévision linéaire pour cette série en particulier.",
            S_body,
        ),
    ]

    # 7. Conclusions
    s.append(KeepTogether([
        Paragraph("7.  Conclusions", S_section),
        hr(spaceAfter=6),
        Paragraph(
            "Des trois approches testées, ARIMA(1,0,2) s'impose "
            "nettement, devançant la référence naïve d'environ "
            "7 % sur le RMSE de façon constante sur les 36 folds "
            "mensuels. À un jour, il donne la bonne direction environ deux "
            "fois sur trois ; à un mois, il ne fait pas mieux qu'un "
            "tirage à pile ou face. L'analyse des résidus complète "
            "le tableau : les erreurs ne sont pas du bruit aléatoire mais "
            "des écarts structurés provoqués par des pics de "
            "volatilité, concentrés dans le temps et bien plus "
            "asymétriques que ce qu'un modèle gaussien suppose. "
            "Pris ensemble, ces résultats tracent précisément la "
            "limite de ce qu'une approche linéaire peut accomplir avec "
            "le VIX, et ce qu'un modèle plus complet devrait prendre "
            "en charge.",
            S_body0,
        ),
    ]))

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
