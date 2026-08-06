"""
Export PDF des résultats d'analyse avec reportlab.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from modules.calculations import ResultatMateriau

SLATE  = colors.HexColor("#2B3A42")
COPPER = colors.HexColor("#C1553B")
STONE  = colors.HexColor("#5B7C8D")
LIGHT  = colors.HexColor("#F1F3F4")


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
        ["Surface consommée", f"{r.surface_consommee_m2} m²"],
        ["Coût fourniture", f"{r.cout_fourniture:,.0f} €"],
        ["Coût pose", f"{r.cout_pose:,.0f} €"],
        ["Coût initial", f"{r.cout_initial:,.0f} €"],
        ["Valorisation indicative de la surface consommée", f"{r.valorisation_surface:,.0f} €"],
        ["Coût global économique indicatif", f"{r.cout_global:,.0f} €"],
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


def generer_pdf(
    nom_projet: str,
    params: dict,
    principale: ResultatMateriau | None,
    alternative: ResultatMateriau | None,
    ecartees: list[ResultatMateriau],
    explication_principale: str,
    explication_alternative: str,
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

    # Recommandation principale
    if principale:
        story.append(Paragraph("✅ Meilleur compromis technico-économique", s["H2"]))
        # Nettoyer le markdown pour reportlab
        expl = explication_principale.replace("**", "").replace("⚠️", "⚠")
        story.append(Paragraph(expl, s["Corps"]))
        story.append(Spacer(1, 0.2*cm))
        story.append(_table_resultats(principale, s))
        story.append(Spacer(1, 0.5*cm))

    # Alternative
    if alternative:
        story.append(Paragraph("💡 Alternative à investissement initial réduit", s["H2"]))
        expl2 = explication_alternative.replace("**", "").replace("⚠️", "⚠")
        story.append(Paragraph(expl2, s["Corps"]))
        story.append(Spacer(1, 0.2*cm))
        story.append(_table_resultats(alternative, s))
        story.append(Spacer(1, 0.5*cm))

    # Solutions écartées
    if ecartees:
        story.append(Paragraph("Solutions écartées", s["H2"]))
        e_data = [["Matériau", "Motif"]]
        for r in ecartees:
            e_data.append([r.nom, r.motif_exclusion])
        et = Table(e_data, colWidths=[8*cm, 9*cm])
        et.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#9E9E9E")),
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
        story.append(et)
        story.append(Spacer(1, 0.5*cm))

    # Limites
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D8DDE0")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Limites de l'outil", s["H2"]))
    story.append(Paragraph(
        "Cet outil constitue une aide à la décision. Il ne remplace pas une étude thermique "
        "réglementaire, une simulation thermique dynamique, une étude hygrothermique détaillée, "
        "une expertise du bâtiment ou une étude économique complète. La valorisation économique "
        "de la surface consommée est un coût d'opportunité indicatif, non un prix de vente garanti.",
        s["Limite"]))

    doc.build(story)
    return buf.getvalue()
