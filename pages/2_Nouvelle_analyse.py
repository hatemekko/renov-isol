"""
Page : Nouvelle analyse — saisie des paramètres du projet.
"""
import streamlit as st
from database.sheets import lire_materiaux, sauvegarder_analyse
from modules.calculations import analyser_materiau
from modules.hygro import TYPES_MURS, ETATS_EXTERIEUR, classe_exterieur
from modules.decision import (
    filtrer_et_classer,
    recommandation_principale,
    alternative_economique,
    generer_explication,
)

st.title("📋 Nouvelle analyse")
st.markdown("Renseignez les caractéristiques du projet, puis lancez l'analyse.")
st.markdown("---")

with st.form("form_analyse"):
    st.subheader("Projet")
    nom_projet = st.text_input("Nom du projet *", placeholder="Ex. : Appartement Heredia")

    col1, col2 = st.columns(2)
    with col1:
        surface_logement = st.number_input("Surface du logement (m²) *", min_value=1.0, value=65.0, step=0.5)
        surface_murs     = st.number_input("Surface des murs extérieurs à isoler (m²) *", min_value=1.0, value=41.44, step=0.5)
        lineaire          = st.number_input("Linéaire des murs à isoler (m) *", min_value=0.5, value=15.6, step=0.1)
        hsp               = st.number_input("Hauteur sous plafond (m) *", min_value=1.8, value=3.03, step=0.05)
    with col2:
        composition_mur = st.selectbox("Type de mur existant *", options=TYPES_MURS)
        etat_exterieur  = st.selectbox("État / finition extérieure de la paroi *",
                                       options=ETATS_EXTERIEUR)
        R_cible       = st.number_input("Résistance thermique cible R (m².K/W) *",
                                         min_value=1.0, max_value=10.0, value=4.5, step=0.1)
        prix_m2       = st.number_input("Prix du logement (€/m²) *",
                                         min_value=500, max_value=50000, value=13649, step=100)

    st.caption("Le comportement extérieur (P/E) est déduit de la finition ci-dessus ; la classe "
               "hygrique P/E de chaque isolant est renseignée dans sa fiche (page Administration).")
    st.caption("* Champs obligatoires. Les valeurs négatives sont refusées.")

    lancer = st.form_submit_button("🔍 Lancer l'analyse", use_container_width=True, type="primary")

# ── Traitement ─────────────────────────────────────────────────────────────────
if lancer:
    erreurs = []
    if not nom_projet.strip():
        erreurs.append("Le nom du projet est obligatoire.")
    if surface_murs > surface_logement * 3:
        erreurs.append("La surface des murs semble incohérente par rapport à la surface du logement.")
    if lineaire <= 0:
        erreurs.append("Le linéaire doit être positif.")

    if erreurs:
        for e in erreurs:
            st.error(e)
        st.stop()

    with st.spinner("Chargement des matériaux et calcul en cours…"):
        try:
            df_mat = lire_materiaux(actif_seulement=True)
        except Exception as ex:
            st.error(f"Impossible de lire la base matériaux : {ex}")
            st.info("Vérifiez la configuration Google Sheets dans les secrets Streamlit.")
            st.stop()

    if df_mat.empty:
        st.warning("Aucun matériau actif dans la base. Ajoutez des matériaux via la page Administration.")
        st.stop()

    # Côté extérieur (P/E) déduit de la finition extérieure
    classe_ext = classe_exterieur(etat_exterieur)

    # Analyse de chaque matériau
    resultats = []
    for _, mat in df_mat.iterrows():
        mat_dict = mat.to_dict()
        r = analyser_materiau(
            mat=mat_dict,
            R_cible=R_cible,
            surface_murs_m2=surface_murs,
            lineaire_m=lineaire,
            prix_m2_logement=prix_m2,
            type_mur=composition_mur,
            classe_ext=classe_ext,
        )
        resultats.append(r)

    admissibles, ecartees = filtrer_et_classer(resultats)
    principale  = recommandation_principale(admissibles)
    alternative = alternative_economique(admissibles, principale)

    # Sauvegarde de l'analyse (non bloquant)
    try:
        sauvegarder_analyse({
            "nom_projet": nom_projet,
            "surface_logement_m2": surface_logement,
            "surface_murs_m2": surface_murs,
            "lineaire_m": lineaire,
            "hsp_m": hsp,
            "composition_mur": composition_mur,
            "R_cible": R_cible,
            "prix_m2_logement": prix_m2,
        })
    except Exception:
        pass

    # Stocker dans la session pour la page Résultats
    st.session_state["resultats"] = {
        "nom_projet": nom_projet,
        "params": {
            "surface_logement": surface_logement,
            "surface_murs": surface_murs,
            "lineaire": lineaire,
            "hsp": hsp,
            "composition_mur": composition_mur,
            "etat_exterieur": etat_exterieur,
            "classe_exterieur": classe_ext or "—",
            "R_cible": R_cible,
            "prix_m2": prix_m2,
        },
        "admissibles": admissibles,
        "ecartees": ecartees,
        "principale": principale,
        "alternative": alternative,
        "explication_principale": generer_explication(principale, True) if principale else "",
        "explication_alternative": generer_explication(alternative, False) if alternative else "",
    }

    st.success("Analyse terminée. Consultez les résultats dans la page **Résultats**.")
    st.page_link("pages/3_Resultats.py", label="→ Voir les résultats", icon="📊")
