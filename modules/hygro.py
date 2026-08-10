"""
Compatibilité hygrothermique mur/isolant.
Règle basée sur la composition des murs existants et le facteur µ de l'isolant.

Sources : ATHEBA ; règles Th-U (RT 2012) ; littérature PROFEEL/CREBA.
"""

# Seuils µ
MU_PERSPIRANT_MAX = 10    # µ ≤ 10 → perspirant
MU_SEMI_MAX       = 30    # 10 < µ ≤ 30 → semi-étanche
# µ > 30 → pare-vapeur


COMPOSITIONS_PERSPIRANTES = [
    "pierre de taille",
    "brique pleine",
    "brique de terre crue",
    "pisé",
    "torchis",
    "colombage",
    "calcaire",
    "meulière",
    "silex",
]

COMPOSITIONS_SEMI_ETANCHES = [
    "béton",
    "parpaing",
    "béton cellulaire",
    "mâchefer",
    "brique creuse",
]


def _classer_mur(composition: str) -> str:
    """Retourne 'perspirant', 'semi_etanche' ou 'inconnu'."""
    c = composition.lower().strip()
    for kw in COMPOSITIONS_PERSPIRANTES:
        if kw in c:
            return "perspirant"
    for kw in COMPOSITIONS_SEMI_ETANCHES:
        if kw in c:
            return "semi_etanche"
    return "inconnu"


def _classer_isolant(mu: float) -> str:
    """Retourne 'perspirant', 'semi_etanche' ou 'pare_vapeur'."""
    if mu <= MU_PERSPIRANT_MAX:
        return "perspirant"
    if mu <= MU_SEMI_MAX:
        return "semi_etanche"
    return "pare_vapeur"


def resoudre_statut(
    composition_mur: str,
    mu: float,
    statut_base: str,
    justif_base: str,
    type_mur_force: str = "",
) -> tuple[str, str]:
    """
    Détermine le statut hygrothermique effectif en croisant :
    - la composition des murs existants
    - le µ de l'isolant
    - le statut documenté dans la base (prioritaire si 'Non compatible')

    Retourne (statut, justification).
    Statuts possibles : 'Compatible' | 'À vérifier' | 'Non compatible'
    """
    # Si la base dit Non compatible, c'est définitif
    if statut_base == "Non compatible":
        return "Non compatible", justif_base or "Non compatible selon la fiche technique."

    type_mur = type_mur_force or _classer_mur(composition_mur)
    type_isolant = _classer_isolant(mu)

    # Matrice de décision
    matrice = {
        # (type_mur, type_isolant) : (statut, justification)
        ("perspirant",   "perspirant")   : ("Compatible",
            f"Mur perspirant ({composition_mur}) + isolant perspirant (µ={mu}) : "
            "compatible, le mur peut sécher librement vers l'intérieur."),
        ("perspirant",   "semi_etanche") : ("À vérifier",
            f"Mur perspirant ({composition_mur}) + isolant semi-étanche (µ={mu}) : "
            "à vérifier par une étude hygrothermique (risque de condensation à l'interface)."),
        ("perspirant",   "pare_vapeur")  : ("Non compatible",
            f"Mur perspirant ({composition_mur}) + isolant pare-vapeur (µ={mu}) : "
            "non compatible. Le mur ne peut plus sécher vers l'intérieur, "
            "risque de condensation et de dégradation."),
        ("semi_etanche", "perspirant")   : ("Compatible",
            f"Mur semi-étanche ({composition_mur}) + isolant perspirant (µ={mu}) : compatible."),
        ("semi_etanche", "semi_etanche") : ("Compatible",
            f"Mur semi-étanche ({composition_mur}) + isolant semi-étanche (µ={mu}) : compatible."),
        ("semi_etanche", "pare_vapeur")  : ("À vérifier",
            f"Mur semi-étanche ({composition_mur}) + isolant pare-vapeur (µ={mu}) : "
            "à vérifier selon l'hygrométrie intérieure."),
        ("inconnu",      "perspirant")   : ("Compatible",
            f"Composition de mur non identifiée. Isolant perspirant (µ={mu}) : "
            "généralement compatible mais vérification recommandée."),
        ("inconnu",      "semi_etanche") : ("À vérifier",
            f"Composition de mur non identifiée + isolant semi-étanche (µ={mu}) : à vérifier."),
        ("inconnu",      "pare_vapeur")  : ("À vérifier",
            f"Composition de mur non identifiée + isolant pare-vapeur (µ={mu}) : à vérifier."),
    }

    statut, justif = matrice[(type_mur, type_isolant)]

    # Si la base dit 'À vérifier' et notre calcul dit 'Compatible', on est prudent
    if statut_base == "À vérifier" and statut == "Compatible":
        return "À vérifier", justif_base or justif

    return statut, justif
