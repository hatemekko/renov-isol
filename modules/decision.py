"""
Moteur de décision : filtrage, classement, recommandation, explication.
Règle transparente — pas de score arbitraire.
"""
from modules.calculations import ResultatMateriau


def filtrer_et_classer(
    resultats: list[ResultatMateriau],
) -> tuple[list[ResultatMateriau], list[ResultatMateriau]]:
    """
    Sépare les solutions admissibles et écartées.
    Admissible = R_obtenu >= R_cible ET statut_hygro != 'Non compatible'.
    Les solutions 'À vérifier' sont admissibles mais signalées.
    """
    admissibles = [r for r in resultats if r.admissible]
    ecartees    = [r for r in resultats if not r.admissible]
    return admissibles, ecartees


def recommandation_principale(admissibles: list[ResultatMateriau]) -> ResultatMateriau | None:
    """
    Coût + valeur des m² perdus le plus faible :
    solution avec le plus faible total (coût des travaux + valeur des m² perdus).
    En cas d'égalité, on préfère la plus mince.
    """
    if not admissibles:
        return None
    return min(admissibles, key=lambda r: (r.cout_global, r.e_totale_mm))


def alternative_economique(
    admissibles: list[ResultatMateriau],
    principale: ResultatMateriau | None,
) -> ResultatMateriau | None:
    """
    Coût des travaux le plus faible :
    solution avec le plus faible coût des travaux.
    En cas d'égalité, on préfère la plus mince.
    Si c'est la même que la principale, retourner None.
    """
    if not admissibles:
        return None
    alt = min(admissibles, key=lambda r: (r.cout_initial, r.e_totale_mm))
    if principale and alt.nom == principale.nom:
        return None
    return alt


def generer_explication(r: ResultatMateriau, est_principale: bool) -> str:
    """
    Génère une explication automatique à partir des données réelles.
    Pas d'IA — règles simples sur les valeurs.
    """
    if est_principale:
        intro = (
            f"**{r.nom}** obtient le coût + valeur des m² perdus le plus faible. "
        )
        thermo = (
            f"Il atteint la résistance thermique cible avec {r.e_commerciale_mm} mm "
            f"(R = {r.R_obtenu} m².K/W pour une cible de {r.R_cible} m².K/W). "
        )
        surface = (
            f"Son épaisseur totale de {r.e_totale_mm} mm entraîne {r.surface_consommee_m2} m² "
            "de surface perdue. "
        )
        eco = (
            f"Son coût des travaux est de {r.cout_initial:,.0f} € et la valeur des m² perdus "
            f"s'élève à {r.valorisation_surface:,.0f} €, soit un total "
            f"(coût + valeur des m² perdus) de {r.cout_global:,.0f} €, "
            "le plus faible parmi les solutions admissibles."
        )
        hygro = ""
        if r.statut_hygro == "À vérifier":
            hygro = (
                " ⚠️ Le statut hygrothermique est **à vérifier** : "
                "une étude hygrothermique détaillée est recommandée avant réalisation."
            )
        return intro + thermo + surface + eco + hygro

    else:
        intro = (
            f"**{r.nom}** présente le coût des travaux le plus faible : {r.cout_initial:,.0f} €. "
        )
        thermo = (
            f"Il atteint la résistance thermique cible avec {r.e_commerciale_mm} mm "
            f"(R = {r.R_obtenu} m².K/W). "
        )
        eco = (
            f"Son total (coût + valeur des m² perdus, {r.cout_global:,.0f} €) est supérieur à celui "
            "de la solution principale en raison d'une surface perdue plus importante "
            f"({r.surface_consommee_m2} m²)."
        )
        hygro = ""
        if r.statut_hygro == "À vérifier":
            hygro = (
                " ⚠️ Le statut hygrothermique est **à vérifier** : "
                "une étude hygrothermique détaillée est recommandée avant réalisation."
            )
        return intro + thermo + eco + hygro
