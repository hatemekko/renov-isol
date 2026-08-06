"""
Page : Administration — gestion de la base matériaux (protégée par mot de passe).
Le mot de passe est stocké dans st.secrets, jamais dans le code.
"""
import streamlit as st
import json

st.title("🔒 Administration")

# ── Authentification ───────────────────────────────────────────────────────────
if "admin_ok" not in st.session_state:
    st.session_state["admin_ok"] = False

if not st.session_state["admin_ok"]:
    pwd = st.text_input("Mot de passe administrateur", type="password")
    if st.button("Connexion"):
        try:
            secret_pwd = st.secrets["admin_password"]
        except Exception:
            st.error("Secret 'admin_password' non configuré. Ajoutez-le dans les secrets Streamlit.")
            st.stop()
        if pwd == secret_pwd:
            st.session_state["admin_ok"] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
    st.stop()

st.success("Connecté en tant qu'administrateur.")

from database.sheets import lire_materiaux, ajouter_materiau, modifier_materiau, toggle_actif

tab_add, tab_edit = st.tabs(["➕ Ajouter un matériau", "✏️ Modifier / désactiver"])

# ── AJOUTER ────────────────────────────────────────────────────────────────────
with tab_add:
    st.subheader("Nouveau matériau")
    with st.form("form_add"):
        st.markdown("**Identification**")
        c1, c2 = st.columns(2)
        nom        = c1.text_input("Nom *")
        famille    = c2.text_input("Famille (ex. : Laine minérale, Aérogel…) *")
        fabricant  = c1.text_input("Fabricant")
        reference  = c2.text_input("Référence commerciale")

        st.markdown("**Thermique**")
        c1, c2 = st.columns(2)
        lambda_val  = c1.number_input("λ (W/m.K) *", min_value=0.001, max_value=1.0,
                                       value=0.032, format="%.4f")
        epaisseurs_str = c2.text_input(
            "Épaisseurs commerciales (mm), séparées par des virgules *",
            placeholder="Ex. : 100, 120, 140, 160"
        )

        st.markdown("**Hygrothermique**")
        c1, c2, c3 = st.columns(3)
        mu           = c1.number_input("Facteur µ *", min_value=0.0, value=1.0)
        perspirant   = c2.selectbox("Perspirant", ["Oui", "Non", "Partiel"])
        statut_pierre = c3.selectbox("Statut (mur pierre)", ["Compatible", "À vérifier", "Non compatible"])
        statut_beton  = c3.selectbox("Statut (mur béton)", ["Compatible", "À vérifier", "Non compatible"])
        justif_hygro  = st.text_area("Justification hygrothermique")

        st.markdown("**Économique**")
        c1, c2, c3 = st.columns(3)
        prix_fourniture = c1.number_input("Fourniture (€/m²) *", min_value=0.0, value=0.0)
        prix_pose       = c2.number_input("Pose (€/m²) *", min_value=0.0, value=0.0)
        ep_comp         = c3.number_input("Épaisseur complémentaire du complexe (mm)", min_value=0, value=13)

        st.markdown("**Documentation**")
        c1, c2 = st.columns(2)
        source = c1.text_input("Source")
        url    = c2.text_input("URL")

        submit = st.form_submit_button("Enregistrer le matériau", type="primary")

    if submit:
        erreurs = []
        if not nom.strip():
            erreurs.append("Le nom est obligatoire.")
        if not famille.strip():
            erreurs.append("La famille est obligatoire.")
        try:
            epaisseurs = [int(e.strip()) for e in epaisseurs_str.split(",") if e.strip()]
            if not epaisseurs:
                raise ValueError
        except ValueError:
            erreurs.append("Épaisseurs invalides. Entrez des entiers séparés par des virgules.")
            epaisseurs = []

        if erreurs:
            for e in erreurs:
                st.error(e)
        else:
            ok = ajouter_materiau({
                "nom": nom.strip(),
                "famille": famille.strip(),
                "fabricant": fabricant.strip(),
                "reference": reference.strip(),
                "lambda_wm K": lambda_val,
                "epaisseurs_mm": epaisseurs,
                "mu": mu,
                "perspirant": perspirant,
                "statut_hygro_pierre": statut_pierre,
                "statut_hygro_beton": statut_beton,
                "justification_hygro": justif_hygro.strip(),
                "prix_fourniture_eur_m2": prix_fourniture,
                "prix_pose_eur_m2": prix_pose,
                "epaisseur_complementaire_mm": ep_comp,
                "source": source.strip(),
                "url": url.strip(),
            })
            if ok:
                st.success(f"Matériau « {nom} » ajouté avec succès.")
                st.cache_resource.clear()

# ── MODIFIER / DÉSACTIVER ──────────────────────────────────────────────────────
with tab_edit:
    st.subheader("Modifier ou désactiver un matériau")
    try:
        df = lire_materiaux(actif_seulement=False)
    except Exception as e:
        st.error(f"Erreur : {e}")
        st.stop()

    if df.empty:
        st.info("Aucun matériau dans la base.")
    else:
        noms = df["nom"].tolist()
        choix = st.selectbox("Sélectionner un matériau", noms)
        row = df[df["nom"] == choix].iloc[0]
        mat_id = int(row["id"])
        actif = str(row.get("actif")) == "1"

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**λ :** {row.get('lambda_wm K')} W/m.K")
            st.markdown(f"**µ :** {row.get('mu')}")
            st.markdown(f"**Statut hygro pierre :** {row.get('statut_hygro_pierre')}")
            st.markdown(f"**Fourniture :** {row.get('prix_fourniture_eur_m2')} €/m²")
            st.markdown(f"**Pose :** {row.get('prix_pose_eur_m2')} €/m²")
        with col2:
            st.markdown(f"**Épaisseurs :** {row.get('epaisseurs_mm')}")
            st.markdown(f"**Source :** {row.get('source', '—')}")
            st.markdown(f"**Mise à jour :** {row.get('date_maj', '—')}")

        st.markdown("---")
        # Modifier le prix de pose et de fourniture rapidement
        with st.expander("Modifier les prix"):
            with st.form("form_prix"):
                nv_f = st.number_input("Nouveau prix fourniture (€/m²)", value=float(row.get("prix_fourniture_eur_m2") or 0))
                nv_p = st.number_input("Nouveau prix pose (€/m²)", value=float(row.get("prix_pose_eur_m2") or 0))
                if st.form_submit_button("Enregistrer les prix"):
                    modifier_materiau(mat_id, {
                        "prix_fourniture_eur_m2": nv_f,
                        "prix_pose_eur_m2": nv_p,
                    })
                    st.success("Prix mis à jour.")
                    st.cache_resource.clear()

        st.markdown("---")
        label_toggle = "⛔ Désactiver ce matériau" if actif else "✅ Réactiver ce matériau"
        if st.button(label_toggle):
            toggle_actif(mat_id, not actif)
            st.success("Statut mis à jour.")
            st.cache_resource.clear()
            st.rerun()

if st.button("Se déconnecter"):
    st.session_state["admin_ok"] = False
    st.rerun()
