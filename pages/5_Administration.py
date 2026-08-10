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
        lambda_str  = c1.text_input("λ (W/m.K) *", value="0.032",
                                     help="Point ou virgule accepté (ex. 0,032 ou 0.032).")
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
            lambda_val = float(lambda_str.replace(",", ".").strip())
            if not (0 < lambda_val <= 1.0):
                raise ValueError
        except ValueError:
            erreurs.append("λ invalide. Entrez un nombre entre 0 et 1 (ex. 0,032).")
            lambda_val = 0.0
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
        st.markdown("### ✏️ Modifier toutes les caractéristiques")

        opts_statut = ["Compatible", "À vérifier", "Non compatible"]
        opts_persp = ["Oui", "Non", "Partiel"]

        def _idx(val, opts):
            v = str(val or "").strip()
            return opts.index(v) if v in opts else 0

        try:
            _ep_list = json.loads(row.get("epaisseurs_mm") or "[]")
            _ep_prefill = ", ".join(str(e) for e in _ep_list)
        except Exception:
            _ep_prefill = str(row.get("epaisseurs_mm") or "")

        with st.form("form_edit_full"):
            c1, c2 = st.columns(2)
            e_nom       = c1.text_input("Nom", value=str(row.get("nom") or ""))
            e_famille   = c2.text_input("Famille", value=str(row.get("famille") or ""))
            e_fabricant = c1.text_input("Fabricant", value=str(row.get("fabricant") or ""))
            e_reference = c2.text_input("Référence", value=str(row.get("reference") or ""))

            c1, c2 = st.columns(2)
            e_lambda = c1.text_input("λ (W/m.K)", value=str(row.get("lambda_wm K") or ""),
                                     help="Point ou virgule accepté (ex. 0,032).")
            e_ep     = c2.text_input("Épaisseurs (mm, séparées par des virgules)", value=_ep_prefill)

            c1, c2, c3 = st.columns(3)
            e_mu     = c1.text_input("µ", value=str(row.get("mu") or ""),
                                     help="Point ou virgule accepté.")
            e_persp  = c2.selectbox("Perspirant", opts_persp, index=_idx(row.get("perspirant"), opts_persp))
            e_epcomp = c3.number_input("Épaisseur complémentaire (mm)", min_value=0,
                                       value=int(float(row.get("epaisseur_complementaire_mm") or 0)))

            c1, c2 = st.columns(2)
            e_sp = c1.selectbox("Statut (mur pierre)", opts_statut,
                                index=_idx(row.get("statut_hygro_pierre"), opts_statut))
            e_sb = c2.selectbox("Statut (mur béton)", opts_statut,
                                index=_idx(row.get("statut_hygro_beton"), opts_statut))
            e_justif = st.text_area("Justification hygrothermique",
                                    value=str(row.get("justification_hygro") or ""))

            c1, c2 = st.columns(2)
            e_pf = c1.text_input("Fourniture (€/m²)", value=str(row.get("prix_fourniture_eur_m2") or "0"),
                                 help="Point ou virgule accepté.")
            e_pp = c2.text_input("Pose (€/m²)", value=str(row.get("prix_pose_eur_m2") or "0"),
                                 help="Point ou virgule accepté.")

            c1, c2 = st.columns(2)
            e_source = c1.text_input("Source", value=str(row.get("source") or ""))
            e_url    = c2.text_input("URL", value=str(row.get("url") or ""))

            if st.form_submit_button("💾 Enregistrer les modifications", type="primary"):
                errs = []

                def _num(s, label, maxi=None):
                    try:
                        v = float(str(s).replace(",", ".").strip())
                        if v < 0 or (maxi is not None and v > maxi):
                            raise ValueError
                        return v
                    except ValueError:
                        errs.append(f"{label} invalide.")
                        return None

                v_lambda = _num(e_lambda, "λ", 1.0)
                if v_lambda is not None and v_lambda <= 0:
                    errs.append("λ doit être supérieur à 0.")
                    v_lambda = None
                v_mu = _num(e_mu, "µ")
                v_pf = _num(e_pf, "Prix fourniture")
                v_pp = _num(e_pp, "Prix pose")
                try:
                    v_ep = [int(x.strip()) for x in e_ep.split(",") if x.strip()]
                    if not v_ep:
                        raise ValueError
                except ValueError:
                    errs.append("Épaisseurs invalides.")
                    v_ep = None
                if not e_nom.strip():
                    errs.append("Le nom est obligatoire.")

                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    ok = modifier_materiau(mat_id, {
                        "nom": e_nom.strip(), "famille": e_famille.strip(),
                        "fabricant": e_fabricant.strip(), "reference": e_reference.strip(),
                        "lambda_wm K": v_lambda, "epaisseurs_mm": v_ep, "mu": v_mu,
                        "perspirant": e_persp,
                        "statut_hygro_pierre": e_sp, "statut_hygro_beton": e_sb,
                        "justification_hygro": e_justif.strip(),
                        "prix_fourniture_eur_m2": v_pf, "prix_pose_eur_m2": v_pp,
                        "epaisseur_complementaire_mm": e_epcomp,
                        "source": e_source.strip(), "url": e_url.strip(),
                    })
                    if ok:
                        st.success("Matériau mis à jour. Rechargez la page (R) pour voir les nouvelles valeurs.")
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
