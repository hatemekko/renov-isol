"""
Compatibilité hygrothermique — méthode HYGROBA (ITI).

La configuration est déterminée par :
  type de mur + état extérieur (P/E) + classe hygrique de la solution d'ITI (P/E).

- La classe P/E de l'isolant est SAISIE dans la fiche matériau (jamais déduite de µ ou Sd).
- Aucun calcul hygrothermique n'est refait : on lit les résultats HYGROBA de la matrice.
- À ce stade : on affiche les 3 résultats HYGROBA, SANS éliminer de solution sur cette base.
  (La règle vert/orange/rouge → retenu/vigilance/écarté sera définie plus tard.)
"""

# ── Types de murs (le dernier n'est pas couvert par HYGROBA) ────────────────────
TYPES_MURS = [
    "Terre crue",
    "Brique de terre cuite",
    "Pan de bois / torchis",
    "Pierre calcaire dure",
    "Autre / non couvert par HYGROBA",
]

# ── État / finition extérieure de la paroi ──────────────────────────────────────
ETATS_EXTERIEUR = [
    "Mur nu / matériau apparent",
    "Enduit ou revêtement perméable à l'humidité",
    "Enduit ou revêtement peu perméable / étanche",
    "Inconnu",
]


def classe_exterieur(etat: str):
    """Renvoie 'P', 'E' ou None (inconnu) selon la finition extérieure réelle."""
    if etat in ("Mur nu / matériau apparent",
                "Enduit ou revêtement perméable à l'humidité"):
        return "P"
    if etat == "Enduit ou revêtement peu perméable / étanche":
        return "E"
    return None  # Inconnu → pas de classement automatique


# ── Classe hygrique de la solution d'ITI (saisie par l'utilisateur) ─────────────
CLASSES_HYGRIQUES = ["", "P", "E"]   # "" = non renseignée

# ── Critères HYGROBA affichés ───────────────────────────────────────────────────
CRITERES_HYGRO = [
    ("eau", "Quantité d'eau"),
    ("sechage", "Capacité de séchage"),
    ("condensation", "Condensation"),
]

# ── Matrice HYGROBA : mur → configuration (extérieur-intérieur) → 3 critères ─────
#    Couleurs possibles : "vert" | "orange" | "rouge"
HYGROBA = {
    "Terre crue": {
        "P-P": {"eau": "vert",   "sechage": "orange", "condensation": "vert"},
        "P-E": {"eau": "vert",   "sechage": "orange", "condensation": "vert"},
        "E-P": {"eau": "orange", "sechage": "rouge",  "condensation": "orange"},
        "E-E": {"eau": "orange", "sechage": "rouge",  "condensation": "vert"},
    },
    "Brique de terre cuite": {
        "P-P": {"eau": "vert",   "sechage": "orange", "condensation": "vert"},
        "P-E": {"eau": "vert",   "sechage": "rouge",  "condensation": "vert"},
        "E-P": {"eau": "orange", "sechage": "rouge",  "condensation": "orange"},
        "E-E": {"eau": "orange", "sechage": "rouge",  "condensation": "vert"},
    },
    "Pan de bois / torchis": {
        "P-P": {"eau": "vert",   "sechage": "orange", "condensation": "vert"},
        "P-E": {"eau": "vert",   "sechage": "orange", "condensation": "vert"},
        "E-P": {"eau": "orange", "sechage": "orange", "condensation": "orange"},
        "E-E": {"eau": "vert",   "sechage": "rouge",  "condensation": "vert"},
    },
    "Pierre calcaire dure": {
        "P-P": {"eau": "orange", "sechage": "rouge", "condensation": "orange"},
        "P-E": {"eau": "orange", "sechage": "rouge", "condensation": "orange"},
        "E-P": {"eau": "orange", "sechage": "rouge", "condensation": "orange"},
        "E-E": {"eau": "rouge",  "sechage": "rouge", "condensation": "orange"},
    },
}

MESSAGE_VERIF = "Vérification hygrothermique complémentaire nécessaire."

# ── Présélection HYGROBA : configurations CONSERVÉES par type de mur ─────────────
# Valeur = statut de la configuration retenue : "privilégier" ou "vigilance".
# Toute configuration NON listée pour un mur est écartée du comparatif principal
# (mais reste visible dans « Solutions non retenues » — jamais présentée comme interdite).
PRESELECTION_HYGROBA = {
    "Terre crue":            {"P-P": "privilégier", "P-E": "privilégier"},
    "Brique de terre cuite": {"P-P": "privilégier"},
    "Pan de bois / torchis": {"P-P": "privilégier", "P-E": "privilégier"},
    "Pierre calcaire dure":  {"P-P": "vigilance", "P-E": "vigilance", "E-P": "vigilance"},
}

MOTIF_HYGROBA_ECARTE = ("Non retenue par la présélection HYGROBA pour cette "
                        "configuration de paroi.")

ALERTE_SECHAGE = ("Point de vigilance HYGROBA : capacité de séchage limitée signalée "
                  "pour ce type de mur.")


def evaluer_hygroba(type_mur: str, classe_ext, classe_isolant) -> dict:
    """
    Détermine la configuration HYGROBA et applique la présélection par type de mur.

    Retour :
      {
        "exploitable": bool,        # une case HYGROBA correspond
        "config": "P-E" | None,
        "criteres": {...} | None,   # les 3 couleurs (traçabilité)
        "retenu": bool | None,      # True = privilégiée ; False = écartée ; None = non exploitable
        "statut": "privilégier" | "vigilance" | "",
        "alerte": str,              # message de vigilance éventuel
        "message": str,             # message si non exploitable
      }
    """
    vide = {"exploitable": False, "config": None, "criteres": None,
            "retenu": None, "statut": "", "alerte": "", "message": MESSAGE_VERIF}
    ci = (classe_isolant or "").strip().upper()
    if (type_mur not in HYGROBA) or (classe_ext not in ("P", "E")) or (ci not in ("P", "E")):
        return vide
    config = f"{classe_ext}-{ci}"
    criteres = HYGROBA[type_mur].get(config)
    if criteres is None:
        return vide
    statut = PRESELECTION_HYGROBA.get(type_mur, {}).get(config)  # None si config écartée
    retenu = statut is not None
    alerte = ALERTE_SECHAGE if statut == "vigilance" else ""
    return {"exploitable": True, "config": config, "criteres": criteres,
            "retenu": retenu, "statut": statut or "", "alerte": alerte, "message": ""}
