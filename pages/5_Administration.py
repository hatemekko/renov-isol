"""
Page : Administration — gestion de la base matériaux (protégée par mot de passe).
Le mot de passe est stocké dans st.secrets, jamais dans le code.
"""
import streamlit as st
import json
import pandas as pd

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

PRIX_COLS = {
    "Épaisseur (mm)": st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
    "Fourniture (€/m²)": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.2f"),
    "Pose (€/m²)": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.2f"),
}


def _prix_table_from_epaisseurs(epaisseurs_raw, pf_repli=0.0, pp_repli=0.0) -> pd.DataFrame:
    """Construit le tableau (Épaisseur, Fourniture, Pose) à partir de epaisseurs_mm.
    Ancien format [100, 120] → prix unique appliqué à chaque ligne (modifiable)."""
    rows = []
    for item in (epaisseurs_raw or []):
        if isinstance(item, dict):
            rows.append({"Épaisseur (mm)": int(item.get("e") or 0),
                         "Fourniture (€/m²)": float(item.get("pf") or 0),
                         "Pose (€/m²)": float(item.get("pp") or 0)})
        else:
            try:
                rows.append({"Épaisseur (mm)": int(item),
                             "Fourniture (€/m²)": float(pf_repli or 0),
                             "Pose (€/m²)": float(pp_repli or 0)})
            except (TypeError, ValueError):
                continue
    if not rows:
        rows = [{"Épaisseur (mm)": 100, "Fourniture (€/m²)": 0.0, "Pose (€/m²)": 0.0}]
    return pd.DataFrame(rows)


def _parse_prix_table(df):
    """Transforme le tableau édité en (liste enrichie [{e,pf,pp}], pf_repli, pp_repli)."""
    enrichi = []
    for _, r in df.iterrows():
        e = r.get("Épaisseur (mm)")
        if pd.isna(e) or int(e) <= 0:
            continue
        enrichi.append({"e": int(e),
                        "pf": float(r.get("Fourniture (€/m²)") or 0),
                        "pp": float(r.get("Pose (€/m²)") or 0)})
    enrichi.sort(key=lambda d: d["e"])
    if enrichi:
        return enrichi, enrichi[0]["pf"], enrichi[0]["pp"]
    return [], 0.0, 0.0


def _num_opt(s):
    """Nombre optionnel tolérant virgule/point ; '' si vide/invalide (champ informatif)."""
    s = str(s or "").strip().replace(",", ".")
    if not s:
        return ""
    try:
        return float(s)
    except ValueError:
        return ""


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
        lambda_str = st.text_input("λ (W/m.K) *", value="0.032",
                                   help="Point ou virgule accepté (ex. 0,032 ou 0.032).")

        st.markdown("**Épaisseurs commerciales et prix** *")
        st.caption("Une ligne par épaisseur, avec son prix de fourniture et de pose "
                   "(chaque épaisseur a son propre prix). Bouton « + » en bas du tableau pour ajouter une ligne.")
        prix_df_add = st.data_editor(
            pd.DataFrame({"Épaisseur (mm)": [100, 120, 140],
                          "Fourniture (€/m²)": [0.0, 0.0, 0.0],
                          "Pose (€/m²)": [0.0, 0.0, 0.0]}),
            num_rows="dynamic", use_container_width=True, key="prix_add",
            column_config=PRIX_COLS,
        )

        st.markdown("**Hygrothermique (méthode HYGROBA)**")
        c1, c2 = st.columns(2)
        classe_hygrique = c1.selectbox(
            "Classe hygrique de la solution (P / E)", ["", "P", "E"],
            help="P = perméable / peu résistante aux transferts d'humidité ; E = plus fermée / "
                 "résistante. À saisir d'après les fiches techniques, Avis Techniques, ACERMI… "
                 "Jamais déduite de µ.")
        mu_str = c2.text_input("Facteur µ (informatif)", value="",
                               help="Information / traçabilité — ne détermine pas la classe P/E. "
                                    "Le Sd éventuel se déduit de µ × épaisseur retenue.")
        parement = st.text_input(
            "Parement / frein-vapeur / pare-vapeur — type ou description",
            placeholder="Ex. : pare-vapeur obligatoire ; parement plaque de plâtre ; aucun")
        frein_pare = st.text_input(
            "Frein-vapeur / pare-vapeur éventuel (précision)",
            placeholder="Ex. : pare-vapeur Sd ≥ 18 m ; frein-vapeur hygrovariable")
        commentaire = st.text_area("Commentaire", height=68)

        st.markdown("**Autres**")
        ep_comp = st.number_input("Épaisseur complémentaire du complexe (mm)", min_value=0, value=13)

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
        epaisseurs, prix_f0, prix_p0 = _parse_prix_table(prix_df_add)
        if not epaisseurs:
            erreurs.append("Renseignez au moins une épaisseur avec son prix (fourniture et pose).")

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
                "mu": _num_opt(mu_str),
                "classe_hygrique": classe_hygrique,
                "parement": parement.strip(),
                "frein_pare_vapeur": frein_pare.strip(),
                "commentaire": commentaire.strip(),
                "prix_fourniture_eur_m2": prix_f0,
                "prix_pose_eur_m2": prix_p0,
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
            st.markdown(f"**Classe P/E :** {row.get('classe_hygrique') or '—'}")
        with col2:
            _ths = [(d.get("e") if isinstance(d, dict) else d)
                    for d in (row.get("epaisseurs_mm") or [])]
            st.markdown(f"**Épaisseurs :** {', '.join(str(t) for t in _ths)} mm")
            st.markdown(f"**Source :** {row.get('source', '—')}")
            st.markdown(f"**Mise à jour :** {row.get('date_maj', '—')}")

        st.markdown("---")
        st.markdown("### ✏️ Modifier toutes les caractéristiques")

        def _idx(val, opts):
            v = str(val or "").strip()
            return opts.index(v) if v in opts else 0

        _prix_df_init = _prix_table_from_epaisseurs(
            row.get("epaisseurs_mm"),
            row.get("prix_fourniture_eur_m2"), row.get("prix_pose_eur_m2"))

        with st.form("form_edit_full"):
            c1, c2 = st.columns(2)
            e_nom       = c1.text_input("Nom", value=str(row.get("nom") or ""))
            e_famille   = c2.text_input("Famille", value=str(row.get("famille") or ""))
            e_fabricant = c1.text_input("Fabricant", value=str(row.get("fabricant") or ""))
            e_reference = c2.text_input("Référence", value=str(row.get("reference") or ""))

            e_lambda = st.text_input("λ (W/m.K)", value=str(row.get("lambda_wm K") or ""),
                                     help="Point ou virgule accepté (ex. 0,032).")
            st.markdown("**Épaisseurs commerciales et prix**")
            st.caption("Une ligne par épaisseur, avec son prix de fourniture et de pose.")
            e_prix_df = st.data_editor(_prix_df_init, num_rows="dynamic",
                                       use_container_width=True, key="prix_edit",
                                       column_config=PRIX_COLS)

            st.markdown("**Hygrothermique (méthode HYGROBA)**")
            c1, c2 = st.columns(2)
            e_classe = c1.selectbox("Classe hygrique (P / E)", ["", "P", "E"],
                                    index=_idx(row.get("classe_hygrique"), ["", "P", "E"]),
                                    help="Saisie manuelle, jamais déduite de µ.")
            e_epcomp = c2.number_input("Épaisseur complémentaire (mm)", min_value=0,
                                       value=int(float(row.get("epaisseur_complementaire_mm") or 0)))
            e_mu = st.text_input("µ (informatif)", value=str(row.get("mu") or ""),
                                 help="Point ou virgule accepté. Ne détermine pas la classe P/E.")
            e_parement = st.text_input("Parement / frein-vapeur / pare-vapeur — type ou description",
                                       value=str(row.get("parement") or ""))
            e_frein = st.text_input("Frein-vapeur / pare-vapeur éventuel (précision)",
                                    value=str(row.get("frein_pare_vapeur") or ""))
            e_commentaire = st.text_area("Commentaire", value=str(row.get("commentaire") or ""), height=68)

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
                v_mu = _num_opt(e_mu)
                v_ep, v_pf, v_pp = _parse_prix_table(e_prix_df)
                if not v_ep:
                    errs.append("Renseignez au moins une épaisseur avec son prix.")
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
                        "classe_hygrique": e_classe,
                        "parement": e_parement.strip(), "frein_pare_vapeur": e_frein.strip(),
                        "commentaire": e_commentaire.strip(),
                        "prix_fourniture_eur_m2": v_pf, "prix_pose_eur_m2": v_pp,
                        "epaisseur_complementaire_mm": e_epcomp,
                        "source": e_source.strip(), "url": e_url.strip(),
                    })
                    if ok:
                        st.cache_resource.clear()
                        st.toast("Matériau mis à jour ✅")
                        st.rerun()
                    else:
                        st.error("Échec de l'enregistrement : matériau introuvable (id). "
                                 "Rechargez la page et réessayez.")

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
