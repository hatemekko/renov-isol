"""
Page : Base matériaux — consultation publique (lecture seule).
"""
import streamlit as st
import pandas as pd

st.title("🗄️ Base matériaux")
st.markdown("Consultez les matériaux disponibles dans la base. La modification est réservée à l'administrateur.")
st.markdown("---")

try:
    from database.sheets import lire_materiaux
    df = lire_materiaux(actif_seulement=False)
except Exception as e:
    st.error(f"Impossible de charger la base : {e}")
    st.stop()

if df.empty:
    st.warning("La base est vide. Ajoutez des matériaux via la page Administration.")
    st.stop()

# Filtres
col1, col2 = st.columns(2)
with col1:
    familles = ["Toutes"] + sorted(df["famille"].dropna().unique().tolist())
    filtre_famille = st.selectbox("Famille", familles)
with col2:
    filtre_actif = st.selectbox("Statut", ["Actifs uniquement", "Tous"])

df_f = df.copy()
if filtre_famille != "Toutes":
    df_f = df_f[df_f["famille"] == filtre_famille]
if filtre_actif == "Actifs uniquement":
    df_f = df_f[df_f["actif"].astype(str) == "1"]

st.markdown(f"**{len(df_f)} matériau(x) trouvé(s)**")

for _, row in df_f.iterrows():
    actif_label = "✅ Actif" if str(row.get("actif")) == "1" else "⛔ Inactif"
    with st.expander(f"{row['nom']} — {row.get('famille', '')} | {actif_label}"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Identification**")
            st.write(f"Fabricant : {row.get('fabricant', '—')}")
            st.write(f"Référence : {row.get('reference', '—')}")
        with col2:
            st.markdown("**Thermique**")
            st.write(f"λ : {row.get('lambda_wm K', '—')} W/m.K")
            epaisseurs = row.get("epaisseurs_mm", [])
            _ths = [(e.get("e") if isinstance(e, dict) else e) for e in (epaisseurs or [])]
            if _ths:
                st.write(f"Épaisseurs : {', '.join(str(e) for e in _ths)} mm")
        with col3:
            st.markdown("**Hygrothermique (HYGROBA)**")
            st.write(f"Classe hygrique : {row.get('classe_hygrique') or '—'}")
            st.write(f"Compatibilité ITI : {row.get('compatibilite_iti') or '—'}")
            st.write(f"µ : {row.get('mu', '—')}  ·  Sd : {row.get('sd') or '—'} m")
            if row.get("parement"):
                st.write(f"Parement / pare-vapeur : {row.get('parement')}")
            if row.get("commentaire"):
                st.caption(f"{row.get('commentaire')}")
        st.markdown("**Économique — prix par épaisseur**")
        _prix_rows = [d for d in (epaisseurs or []) if isinstance(d, dict)]
        if _prix_rows:
            st.dataframe(
                pd.DataFrame([{"Épaisseur (mm)": d.get("e"),
                               "Fourniture (€/m²)": d.get("pf"),
                               "Pose (€/m²)": d.get("pp")} for d in _prix_rows]),
                use_container_width=True, hide_index=True)
        else:
            c1, c2 = st.columns(2)
            c1.metric("Fourniture", f"{row.get('prix_fourniture_eur_m2', '—')} €/m²")
            c2.metric("Pose", f"{row.get('prix_pose_eur_m2', '—')} €/m²")
        if row.get("source"):
            st.markdown(f"📚 Source : {row['source']}")
            if row.get("url"):
                st.markdown(f"[→ Consulter la source]({row['url']})")
        if row.get("date_maj"):
            st.caption(f"Mise à jour : {row['date_maj']}")
