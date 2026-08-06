"""
Tests des fonctions de calcul — données fictives pour validation interne.
"""
import sys
sys.path.insert(0, ".")

from modules.calculations import (
    calculer_epaisseur_theorique,
    selectionner_epaisseur_commerciale,
    calculer_surface_consommee,
    calculer_couts,
    calculer_valorisation,
    calculer_cout_global,
)
from modules.hygro import resoudre_statut
from modules.decision import (
    recommandation_principale,
    alternative_economique,
)


def approx(a, b, tol=0.01):
    return abs(a - b) <= tol


# ── Calcul thermique ───────────────────────────────────────────────────────────

def test_epaisseur_theorique():
    # laine λ=0.032, R=4.5 → e=144mm
    assert approx(calculer_epaisseur_theorique(0.032, 4.5), 144.0)
    # aérogel λ=0.015, R=4.5 → e=67.5mm
    assert approx(calculer_epaisseur_theorique(0.015, 4.5), 67.5)
    print("✓ epaisseur_theorique")


def test_selection_epaisseur():
    epaisseurs = [60, 80, 100, 120, 140, 160]
    e, R = selectionner_epaisseur_commerciale(epaisseurs, 0.032, 4.5)
    assert e == 160, f"Attendu 160, obtenu {e}"
    assert approx(R, 5.0)
    # aérogel
    epaisseurs_aero = [50, 60, 70, 80]
    e2, R2 = selectionner_epaisseur_commerciale(epaisseurs_aero, 0.015, 4.5)
    assert e2 == 70
    assert approx(R2, 4.667)
    # aucune épaisseur suffisante
    e3, R3 = selectionner_epaisseur_commerciale([30, 40], 0.032, 4.5)
    assert e3 is None
    print("✓ selection_epaisseur")


def test_surface_consommee():
    # 15.6 m × 0.173 m = 2.699 m²
    assert approx(calculer_surface_consommee(15.6, 173), 2.70, tol=0.02)
    # 15.6 m × 0.083 m = 1.295 m²
    assert approx(calculer_surface_consommee(15.6, 83), 1.30, tol=0.02)
    print("✓ surface_consommee")


def test_couts():
    cf, cp, ci = calculer_couts(41.44, 50.0, 62.44)
    assert approx(cf, 2072.0)
    assert approx(cp, 2588.5, tol=1)
    assert approx(ci, cf + cp)
    print("✓ couts")


def test_valorisation():
    vs = calculer_valorisation(1.40, 13649.0)
    assert approx(vs, 19108.6, tol=1)
    print("✓ valorisation")


def test_cout_global():
    cg = calculer_cout_global(5000, 19108.6)
    assert approx(cg, 24108.6, tol=1)
    print("✓ cout_global")


# ── Hygrothermique ─────────────────────────────────────────────────────────────

def test_hygro_compatible():
    statut, _ = resoudre_statut("pierre de taille", 5.0, "Compatible", "")
    assert statut == "Compatible", f"Attendu Compatible, obtenu {statut}"
    print("✓ hygro compatible")


def test_hygro_non_compatible():
    statut, _ = resoudre_statut("pierre de taille", 50.0, "Compatible", "")
    assert statut == "Non compatible", f"Attendu Non compatible, obtenu {statut}"
    print("✓ hygro non compatible")


def test_hygro_a_verifier():
    statut, _ = resoudre_statut("béton", 50.0, "Compatible", "")
    assert statut == "À vérifier", f"Attendu À vérifier, obtenu {statut}"
    print("✓ hygro à vérifier")


# ── Décision ──────────────────────────────────────────────────────────────────

def _make_result(nom, cout_initial, cout_global, e_totale, admissible=True):
    """Crée un ResultatMateriau minimal pour les tests de décision."""
    from modules.calculations import ResultatMateriau
    return ResultatMateriau(
        nom=nom, famille="test", fabricant="test",
        lambda_val=0.032, mu=5.0,
        statut_hygro="Compatible", justification_hygro="",
        R_cible=4.5, e_theorique_mm=144, e_commerciale_mm=e_totale,
        R_obtenu=5.0, epaisseur_complementaire_mm=0,
        e_totale_mm=e_totale, surface_murs_m2=41.44,
        lineaire_m=15.6, surface_consommee_m2=round(15.6*e_totale/1000,2),
        prix_fourniture_m2=50, prix_pose_m2=60,
        cout_fourniture=2072, cout_pose=2486, cout_initial=cout_initial,
        prix_m2_logement=13649, valorisation_surface=cout_global-cout_initial,
        cout_global=cout_global,
        source="", url="", admissible=admissible, motif_exclusion="",
    )


def test_recommandation():
    r1 = _make_result("Laine", 4660, 24000, 173)
    r2 = _make_result("Aérogel", 8000, 21000, 83)
    principale = recommandation_principale([r1, r2])
    assert principale.nom == "Aérogel", f"Attendu Aérogel, obtenu {principale.nom}"
    print("✓ recommandation principale")


def test_alternative():
    r1 = _make_result("Laine", 4660, 24000, 173)
    r2 = _make_result("Aérogel", 8000, 21000, 83)
    principale = recommandation_principale([r1, r2])
    alt = alternative_economique([r1, r2], principale)
    assert alt is not None and alt.nom == "Laine"
    print("✓ alternative économique")


def test_alternative_identique():
    """Si la solution la moins chère à l'achat est aussi la principale, pas d'alternative."""
    r1 = _make_result("UniqueWinner", 4000, 18000, 100)
    principale = recommandation_principale([r1])
    alt = alternative_economique([r1], principale)
    assert alt is None
    print("✓ pas d'alternative si solution unique")


if __name__ == "__main__":
    test_epaisseur_theorique()
    test_selection_epaisseur()
    test_surface_consommee()
    test_couts()
    test_valorisation()
    test_cout_global()
    test_hygro_compatible()
    test_hygro_non_compatible()
    test_hygro_a_verifier()
    test_recommandation()
    test_alternative()
    test_alternative_identique()
    print("\n✅ Tous les tests sont passés.")
