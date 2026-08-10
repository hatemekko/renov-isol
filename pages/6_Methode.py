"""
Page : Méthode — explication pédagogique des calculs et de la règle de décision.
"""
import streamlit as st

st.title("📐 Méthode")
st.markdown("Cette page explique comment l'outil calcule et comment il prend ses décisions.")
st.markdown("---")

etapes = [
    ("1 — Données du projet",
     "L'utilisateur renseigne les caractéristiques du logement : surface des murs à isoler, "
     "linéaire des murs, résistance thermique cible (R cible en m².K/W), composition des murs "
     "existants et prix du logement au mètre carré."),
    ("2 — Filtrage technique",
     "Pour chaque matériau de la base, l'outil vérifie trois conditions :\n"
     "- **R obtenu ≥ R cible** grâce à l'épaisseur commerciale disponible.\n"
     "- **Compatibilité hygrothermique** : les murs anciens perspirants (pierre, brique pleine, "
     "pisé) ne sont compatibles qu'avec des isolants perspirants (µ ≤ 10). "
     "Un isolant pare-vapeur (µ > 30) sur un mur perspirant est classé **Non compatible** "
     "et exclu du classement."),
    ("3 — Calcul de l'épaisseur",
     "Pour chaque matériau :\n\n"
     "> **e théorique (mm) = λ × R cible × 1000**\n\n"
     "L'outil recherche ensuite la plus petite épaisseur commerciale disponible telle que :\n\n"
     "> **R obtenu = e (m) / λ ≥ R cible**"),
    ("4 — Calcul de la surface perdue",
     "> **Surface perdue (m²) = linéaire des murs (m) × épaisseur totale (m)**\n\n"
     "L'épaisseur totale inclut l'épaisseur de l'isolant et l'épaisseur complémentaire du "
     "complexe (ossature, parement…) renseignée dans la base."),
    ("5 — Calcul du coût des travaux",
     "> **Coût fourniture = surface des murs × prix fourniture €/m²**\n"
     "> **Coût pose = surface des murs × prix pose €/m²**\n"
     "> **Coût des travaux = coût fourniture + coût pose**"),
    ("6 — Calcul de la valeur des m² perdus",
     "> **Valeur des m² perdus = surface perdue × prix du logement €/m²**\n\n"
     "Il s'agit d'un **coût d'opportunité indicatif**, et non d'un prix de vente garanti. "
     "Il mesure la valeur de marché de la surface habitable définitivement perdue."),
    ("7 — Total : coût + valeur des m² perdus",
     "> **Coût + valeur des m² perdus = coût des travaux + valeur des m² perdus**\n\n"
     "Ce total permet de comparer des solutions à coût des travaux différent en intégrant "
     "le coût d'opportunité de la surface perdue. Il sert uniquement de repère de comparaison."),
    ("8 — Deux repères de comparaison",
     "Parmi les solutions techniquement admissibles :\n\n"
     "**Coût + valeur des m² perdus le plus faible** → solution dont le total "
     "(coût des travaux + valeur des m² perdus) est le plus bas. "
     "En cas d'égalité, on préfère la plus mince.\n\n"
     "**Coût des travaux le plus faible** → solution dont le coût des travaux est le plus bas. "
     "Si c'est la même solution, aucune alternative n'est affichée.\n\n"
     "⚠️ **Aucun score arbitraire n'est utilisé.** La règle de décision est transparente "
     "et basée uniquement sur les deux critères ci-dessus."),
]

for titre, texte in etapes:
    with st.expander(f"**Étape {titre}**", expanded=True):
        st.markdown(texte)

st.markdown("---")
st.info(
    "**Limites de l'outil.** Cet outil ne réalise pas de simulation thermique dynamique, "
    "de calcul hygrothermique complet (type WUFI ou Glaser détaillé), ni d'analyse de cycle de vie. "
    "Il constitue une aide à la décision en phase de comparaison des solutions."
)
