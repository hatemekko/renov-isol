"""
Export PDF des résultats d'analyse avec reportlab.
"""
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import Normalize, LinearSegmentedColormap

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    Image as RLImage,
)
from modules.calculations import ResultatMateriau

SLATE  = colors.HexColor("#2B3A42")
COPPER = colors.HexColor("#C1553B")
STONE  = colors.HexColor("#5B7C8D")
LIGHT  = colors.HexColor("#F1F3F4")

# Police Unicode complète (DejaVu Sans, fournie par matplotlib) enregistrée sous le nom
# "Helvetica" : tout le texte et tous les tableaux affichent alors correctement le « ² »,
# le « € » et les accents, sans autre modification.
try:
    import matplotlib.font_manager as _fm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Helvetica", _fm.findfont("DejaVu Sans")))
    pdfmetrics.registerFont(TTFont("Helvetica-Bold", _fm.findfont("DejaVu Sans:bold")))
except Exception:
    pass


def _style():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Titre",    parent=s["Title"],   fontSize=18, textColor=SLATE,
                          spaceAfter=6))
    s.add(ParagraphStyle("SousTitre",parent=s["Normal"],  fontSize=11, textColor=STONE,
                          spaceAfter=12))
    s.add(ParagraphStyle("H2",       parent=s["Heading2"],fontSize=13, textColor=SLATE,
                          spaceBefore=14, spaceAfter=6))
    s.add(ParagraphStyle("Corps",    parent=s["Normal"],   fontSize=9.5, leading=14,
                          spaceAfter=8))
    s.add(ParagraphStyle("Alert",    parent=s["Normal"],   fontSize=9, textColor=COPPER,
                          spaceAfter=6))
    s.add(ParagraphStyle("Limite",   parent=s["Normal"],   fontSize=8.5,
                          textColor=colors.HexColor("#6E767C"), spaceAfter=4, leading=12))
    return s


def _table_resultats(r: ResultatMateriau, style) -> Table:
    data = [
        ["Indicateur", "Valeur"],
        ["Matériau", r.nom],
        ["Conductivité λ", f"{r.lambda_val} W/m.K"],
        ["Épaisseur retenue", f"{r.e_commerciale_mm} mm"],
        ["Épaisseur totale posée", f"{r.e_totale_mm} mm"],
        ["R obtenu", f"{r.R_obtenu} m².K/W"],
        ["Surface perdue", f"{r.surface_consommee_m2} m²"],
        ["Coût fourniture", f"{r.cout_fourniture:,.0f} €"],
        ["Coût pose", f"{r.cout_pose:,.0f} €"],
        ["Coût des travaux", f"{r.cout_initial:,.0f} €"],
        ["Valeur des m² perdus", f"{r.valorisation_surface:,.0f} €"],
        ["Coût + valeur des m² perdus", f"{r.cout_global:,.0f} €"],
        ["Statut hygrothermique", r.statut_hygro],
        ["Source", r.source or "—"],
    ]
    t = Table(data, colWidths=[10 * cm, 7 * cm])
    ts = TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), SLATE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DDE0")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ])
    t.setStyle(ts)
    return t


def _graph_image(admissibles):
    """Construit le graphique à bulles (coût des travaux × surface perdue) en image PNG."""
    if not admissibles:
        return None
    xs = [r.cout_initial for r in admissibles]
    ys = [r.surface_consommee_m2 for r in admissibles]
    vals = [r.valorisation_surface for r in admissibles]
    sommes = [r.cout_global for r in admissibles]
    noms = [r.nom for r in admissibles]

    vmax = max(vals) if max(vals) > 0 else 1
    sizes = [140 + 1100 * (v / vmax) for v in vals]

    smin, smax = min(sommes), max(sommes)
    cmap = LinearSegmentedColormap.from_list(
        "gyr", ["#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027"])

    fig, ax = plt.subplots(figsize=(7.2, 4.3), dpi=150)
    if smax > smin:
        sc = ax.scatter(xs, ys, s=sizes, c=sommes, cmap=cmap, vmin=smin, vmax=smax,
                        edgecolors="#2B3A42", linewidths=0.9, alpha=0.6, zorder=3)
        cb = fig.colorbar(sc, ax=ax)
        cb.set_label("Coût + valeur des m² perdus", fontsize=8, color="#2B3A42")
        cb.set_ticks([smin, smax])
        cb.set_ticklabels(["Faible", "Élevé"])
        cb.ax.tick_params(labelsize=7, colors="#2B3A42")
    else:
        ax.scatter(xs, ys, s=sizes, c="#1a9850",
                   edgecolors="#2B3A42", linewidths=0.9, alpha=0.6, zorder=3)

    # Numéro au centre de chaque bulle (contour blanc pour rester lisible sur toute couleur)
    for i, (x, y) in enumerate(zip(xs, ys), start=1):
        ax.annotate(str(i), (x, y), fontsize=8, fontweight="bold", color="#1a1a1a",
                    ha="center", va="center", zorder=5,
                    path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])

    ax.set_xlabel("Coût des travaux (€)", fontsize=10, color="#2B3A42")
    ax.set_ylabel("Surface perdue (m²)", fontsize=10, color="#2B3A42")
    ax.grid(True, color="#E6E9EB", linewidth=0.6, zorder=0)
    ax.tick_params(colors="#2B3A42", labelsize=8)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for spine in ax.spines.values():
        spine.set_color("#9AA3A8")

    fig.tight_layout()
    img = io.BytesIO()
    fig.savefig(img, format="png", bbox_inches="tight")
    plt.close(fig)
    img.seek(0)
    return img


def _table_comparatif(admissibles, style) -> Table:
    cell = ParagraphStyle("cellmat", fontSize=8, leading=10, textColor=SLATE)
    hcell = ParagraphStyle("hcell", fontSize=7.5, leading=9,
                           textColor=colors.white, fontName="Helvetica-Bold")
    labels = ["Matériau", "Ép. (mm)", "R", "Coût travaux (€)",
              "Surface perdue (m²)", "Valeur m² perdus (€)", "Coût + valeur (€)"]
    data = [[Paragraph(h, hcell) for h in labels]]
    for r in admissibles:
        data.append([
            Paragraph(r.nom, cell),
            f"{r.e_commerciale_mm}",
            f"{r.R_obtenu}",
            f"{r.cout_initial:,.0f}",
            f"{r.surface_consommee_m2:.2f}",
            f"{r.valorisation_surface:,.0f}",
            f"{r.cout_global:,.0f}",
        ])
    t = Table(data, colWidths=[4.0*cm, 1.6*cm, 1.6*cm, 2.6*cm, 2.6*cm, 2.6*cm, 2.0*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), SLATE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DDE0")),
        ("ALIGN",       (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    return t


def generer_pdf(
    nom_projet: str,
    params: dict,
    principale: ResultatMateriau | None,
    alternative: ResultatMateriau | None,
    ecartees: list[ResultatMateriau],
    explication_principale: str,
    explication_alternative: str,
    admissibles: list[ResultatMateriau] | None = None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    s = _style()
    story = []

    # En-tête
    story.append(Paragraph("RENOV'ISOL", s["Titre"]))
    story.append(Paragraph("Outil d'aide à la décision — Isolation thermique par l'intérieur", s["SousTitre"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COPPER))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Rapport d'analyse — {nom_projet}", s["H2"]))
    story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", s["Limite"]))
    story.append(Spacer(1, 0.4*cm))

    # Paramètres du projet
    story.append(Paragraph("Paramètres du projet", s["H2"]))
    p_data = [
        ["Paramètre", "Valeur"],
        ["Surface du logement", f"{params.get('surface_logement', '')} m²"],
        ["Surface des murs à isoler", f"{params.get('surface_murs', '')} m²"],
        ["Linéaire des murs", f"{params.get('lineaire', '')} m"],
        ["Hauteur sous plafond", f"{params.get('hsp', '')} m"],
        ["Composition des murs", params.get("composition_mur", "")],
        ["Résistance thermique cible", f"{params.get('R_cible', '')} m².K/W"],
        ["Prix du logement", f"{params.get('prix_m2', '')} €/m²"],
    ]
    pt = Table(p_data, colWidths=[9*cm, 8*cm])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), STONE),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D8DDE0")),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
    ]))
    story.append(pt)
    story.append(Spacer(1, 0.5*cm))

    # Comparaison des solutions : graphique + tableau
    if admissibles:
        story.append(Paragraph("Comparaison des solutions", s["H2"]))
        story.append(Paragraph(
            "Le graphique positionne chaque solution admissible selon son coût des travaux "
            "(axe horizontal) et la surface perdue (axe vertical). La taille de la bulle "
            "représente la valeur des m² perdus ; la couleur (verte → rouge) compare, entre "
            "les solutions du projet, la somme « coût des travaux + valeur des m² perdus ». "
            "La zone en bas à gauche réunit les solutions les moins chères qui font perdre "
            "le moins de surface intérieure.", s["Corps"]))
        img = _graph_image(admissibles)
        if img is not None:
            story.append(RLImage(img, width=16*cm, height=9.5*cm))
            legende = "   ·   ".join(f"{i} = {r.nom}"
                                     for i, r in enumerate(admissibles, start=1))
            story.append(Paragraph("<b>Repères :</b> " + legende, s["Limite"]))
        story.append(Paragraph(
            "Comment lire le graphique : plus une solution est à gauche, moins les travaux "
            "coûtent cher ; plus elle est basse, moins elle fait perdre de surface intérieure.",
            s["Limite"]))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Tableau comparatif — solutions admissibles", s["H2"]))
        story.append(_table_comparatif(admissibles, s))
        story.append(Spacer(1, 0.5*cm))

    # Limites
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D8DDE0")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Limites de l'outil", s["H2"]))
    story.append(Paragraph(
        "Cet outil constitue une aide à la décision. Il ne remplace pas une étude thermique "
        "réglementaire, une simulation thermique dynamique, une étude hygrothermique détaillée, "
        "une expertise du bâtiment ou une étude économique complète. La valeur des m² perdus "
        "est un coût d'opportunité indicatif, non un prix de vente garanti.",
        s["Limite"]))

    doc.build(story)
    return buf.getvalue()
