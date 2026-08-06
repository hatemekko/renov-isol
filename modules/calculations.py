"""
Fonctions de calcul — toutes les formules sont explicites et testables.
"""
from dataclasses import dataclass, field


@dataclass
class ResultatMateriau:
    nom: str
    famille: str
    fabricant: str
    lambda_val: float
    mu: float
    statut_hygro: str          # 'Compatible' | 'À vérifier' | 'Non compatible'
    justification_hygro: str

    R_cible: float
    e_theorique_mm: float
    e_commerciale_mm: float
    R_obtenu: float
    epaisseur_complementaire_mm: float
    e_totale_mm: float

    surface_murs_m2: float
    lineaire_m: float
    surface_consommee_m2: float

    prix_fourniture_m2: float
    prix_pose_m2: float
    cout_fourniture: float
    cout_pose: float
    cout_initial: float

    prix_m2_logement: float
    valorisation_surface: float
    cout_global: float

    source: str
    url: str

    admissible: bool = True
    motif_exclusion: str = ""
    detail_calculs: list = field(default_factory=list)


def calculer_epaisseur_theorique(lambda_val: float, R_cible: float) -> float:
    """e_theorique (m) = λ × R_cible  →  retourné en mm"""
    return round(lambda_val * R_cible * 1000, 1)


def selectionner_epaisseur_commerciale(
    epaisseurs_mm: list[int], lambda_val: float, R_cible: float
) -> tuple[int | None, float]:
    """
    Retourne (épaisseur_commerciale_mm, R_obtenu) pour la plus petite épaisseur
    permettant R_obtenu >= R_cible.
    Retourne (None, 0) si aucune épaisseur ne suffit.
    """
    epaisseurs_triees = sorted([int(e) for e in epaisseurs_mm])
    for e_mm in epaisseurs_triees:
        R = (e_mm / 1000) / lambda_val
        if R >= R_cible:
            return e_mm, round(R, 3)
    return None, 0.0


def calculer_surface_consommee(lineaire_m: float, e_totale_mm: float) -> float:
    """Surface consommée (m²) = linéaire × épaisseur totale (m)"""
    return round(lineaire_m * (e_totale_mm / 1000), 2)


def calculer_couts(
    surface_murs_m2: float,
    prix_fourniture_m2: float,
    prix_pose_m2: float,
) -> tuple[float, float, float]:
    """Retourne (coût_fourniture, coût_pose, coût_initial)"""
    cf = round(surface_murs_m2 * prix_fourniture_m2, 2)
    cp = round(surface_murs_m2 * prix_pose_m2, 2)
    return cf, cp, round(cf + cp, 2)


def calculer_valorisation(surface_consommee_m2: float, prix_m2_logement: float) -> float:
    """Valorisation économique indicative de la surface consommée"""
    return round(surface_consommee_m2 * prix_m2_logement, 2)


def calculer_cout_global(cout_initial: float, valorisation_surface: float) -> float:
    return round(cout_initial + valorisation_surface, 2)


def analyser_materiau(
    mat: dict,
    R_cible: float,
    surface_murs_m2: float,
    lineaire_m: float,
    prix_m2_logement: float,
    statut_hygro_resolu: str,
    justif_hygro: str,
) -> ResultatMateriau:
    """
    Calcule tous les indicateurs pour un matériau donné.
    Retourne un ResultatMateriau complet (admissible ou non).
    """
    lambda_val = float(mat["lambda_wm K"])
    epaisseurs = mat["epaisseurs_mm"]
    e_comp_mm = float(mat.get("epaisseur_complementaire_mm") or 0)
    prix_f = float(mat.get("prix_fourniture_eur_m2") or 0)
    prix_p = float(mat.get("prix_pose_eur_m2") or 0)

    # ── Calcul thermique ──────────────────────────────────────────────
    e_theo_mm = calculer_epaisseur_theorique(lambda_val, R_cible)
    e_com_mm, R_obtenu = selectionner_epaisseur_commerciale(epaisseurs, lambda_val, R_cible)

    detail = [
        f"R cible = {R_cible} m².K/W",
        f"λ = {lambda_val} W/m.K",
        f"e théorique = λ × R = {lambda_val} × {R_cible} = {e_theo_mm / 1000:.4f} m = {e_theo_mm} mm",
    ]

    admissible = True
    motif = ""

    if e_com_mm is None:
        admissible = False
        motif = "Aucune épaisseur commerciale ne permet d'atteindre R cible"
        detail.append(f"→ Aucune épaisseur disponible ≥ {e_theo_mm} mm")
        return ResultatMateriau(
            nom=mat["nom"], famille=mat["famille"], fabricant=mat["fabricant"],
            lambda_val=lambda_val, mu=float(mat.get("mu") or 0),
            statut_hygro=statut_hygro_resolu, justification_hygro=justif_hygro,
            R_cible=R_cible, e_theorique_mm=e_theo_mm,
            e_commerciale_mm=0, R_obtenu=0,
            epaisseur_complementaire_mm=e_comp_mm,
            e_totale_mm=0, surface_murs_m2=surface_murs_m2,
            lineaire_m=lineaire_m, surface_consommee_m2=0,
            prix_fourniture_m2=prix_f, prix_pose_m2=prix_p,
            cout_fourniture=0, cout_pose=0, cout_initial=0,
            prix_m2_logement=prix_m2_logement, valorisation_surface=0,
            cout_global=0, source=mat.get("source", ""), url=mat.get("url", ""),
            admissible=False, motif_exclusion=motif, detail_calculs=detail,
        )

    detail.append(
        f"Épaisseur commerciale retenue = {e_com_mm} mm"
        f"  → R obtenu = {e_com_mm/1000:.3f} / {lambda_val} = {R_obtenu} m².K/W"
    )

    if statut_hygro_resolu == "Non compatible":
        admissible = False
        motif = "Non compatible hygrothermiquement avec les murs existants"

    # ── Calcul géométrique ────────────────────────────────────────────
    e_totale_mm = e_com_mm + e_comp_mm
    s_cons = calculer_surface_consommee(lineaire_m, e_totale_mm)
    detail.append(
        f"Épaisseur totale = {e_com_mm} + {e_comp_mm} = {e_totale_mm} mm"
    )
    detail.append(
        f"Surface consommée = {lineaire_m} m × {e_totale_mm/1000:.3f} m = {s_cons} m²"
    )

    # ── Calcul économique ─────────────────────────────────────────────
    cf, cp, ci = calculer_couts(surface_murs_m2, prix_f, prix_p)
    vs = calculer_valorisation(s_cons, prix_m2_logement)
    cg = calculer_cout_global(ci, vs)
    detail += [
        f"Coût fourniture = {surface_murs_m2} m² × {prix_f} €/m² = {cf} €",
        f"Coût pose = {surface_murs_m2} m² × {prix_p} €/m² = {cp} €",
        f"Coût initial = {cf} + {cp} = {ci} €",
        f"Valorisation surface = {s_cons} m² × {prix_m2_logement} €/m² = {vs} €",
        f"Coût global indicatif = {ci} + {vs} = {cg} €",
    ]

    return ResultatMateriau(
        nom=mat["nom"], famille=mat["famille"], fabricant=mat["fabricant"],
        lambda_val=lambda_val, mu=float(mat.get("mu") or 0),
        statut_hygro=statut_hygro_resolu, justification_hygro=justif_hygro,
        R_cible=R_cible, e_theorique_mm=e_theo_mm,
        e_commerciale_mm=e_com_mm, R_obtenu=R_obtenu,
        epaisseur_complementaire_mm=e_comp_mm,
        e_totale_mm=e_totale_mm, surface_murs_m2=surface_murs_m2,
        lineaire_m=lineaire_m, surface_consommee_m2=s_cons,
        prix_fourniture_m2=prix_f, prix_pose_m2=prix_p,
        cout_fourniture=cf, cout_pose=cp, cout_initial=ci,
        prix_m2_logement=prix_m2_logement, valorisation_surface=vs,
        cout_global=cg, source=mat.get("source", ""), url=mat.get("url", ""),
        admissible=admissible, motif_exclusion=motif, detail_calculs=detail,
    )
