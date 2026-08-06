"""
Page : Résultats — recommandations, tableau comparatif, graphiques, PDF.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.pdf_export import generer_pdf

st.title("📊 Résultats")

if "resultats" not in st.session_state:
    st.info("Aucune analyse en cours. Commencez par renseigner les données dans **Nouvelle analyse**.")
    st.page_link("pages/2_Nouvelle_analyse.py", label="→ Nouvelle analyse", icon="📋")
    st.stop()

data        = st.session_state["resultats"]
nom_projet  = data["nom_projet"]
params      = data["params"]
principale  = data["principale"]
alternative = data["alternative"]
admissibles = data["admissibles"]
ecartees    = data["ecartees"]
expl_p      = data["explication_principale"]
expl_a      = data["explication_alternative"]

st.subheader(f"Projet : {nom_projet}")
st.markdown(f"**Composition des murs :** {params['composition_mur']}  |  "
            f"**R cible :** {params['R_cible']} m².K/W  |  "
            f"**Prix du logement :** {params['prix_m2']:,} €/m²")
st.markdown("---")


def badge_hygro(statut: str) -> str:
    mapping = {
        "Compatible":    '<span class="badge-compatible">Compatible</span>',
        "À vérifier":   '<span class="badge-averifier">À vérifier</span>',
        "Non compatible":'<span class="badge-incompatible">Non compatible</span>',
    }
    return mapping.get(statut, statut)


def afficher_carte(r, titre: str, css_extra: str = ""):
    st.markdown(
        f'<div class="card {css_extra}"><h3>{titre}</h3></div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Matériau", r.nom)
        st.metric("λ (W/m.K)", r.lambda_val)
        st.metric("Épaisseur retenue", f"{r.e_commerciale_mm} mm")
        st.metric("R obtenu", f"{r.R_obtenu} m².K/W")
    with col2:
        st.metric("Surface consommée", f"{r.surface_consommee_m2} m²")
        st.metric("Coût initial", f"{r.cout_initial:,.0f} €")
        st.metric("Valorisation surface", f"{r.valorisation_surface:,.0f} €")
        st.metric("Coût global indicatif", f"{r.cout_global:,.0f} €")
    with col3:
        st.markdown("**Statut hygrothermique**")
        st.markdown(badge_hygro(r.statut_hygro), unsafe_allow_html=True)
        if r.statut_hygro == "À vérifier":
            st.warning("Une étude hygrothermique est recommandée.")
        if r.source:
            st.markdown(f"**Source :** {r.source}")
            if r.url:
                st.markdown(f"[Consulter]({r.url})")
    st.markdown(f"*{expl_p if css_extra == '' else expl_a}*")


# ── Recommandations ────────────────────────────────────────────────────────────
if principale:
    afficher_carte(principale, "✅ Meilleur compromis technico-économique")
else:
    st.error("Aucune solution admissible n'a été trouvée pour les paramètres saisis.")

if alternative:
    afficher_carte(alternative, "💡 Alternative à investissement initial réduit", "card-alt")

st.markdown("---")

# ── Tableau comparatif ─────────────────────────────────────────────────────────
st.subheader("Tableau comparatif — solutions admissibles")
if admissibles:
    rows = []
    for r in admissibles:
        rows.append({
            "Matériau": r.nom,
            "λ": r.lambda_val,
            "Ép. (mm)": r.e_commerciale_mm,
            "R obtenu": r.R_obtenu,
            "Fourniture (€)": r.cout_fourniture,
            "Pose (€)": r.cout_pose,
            "Coût initial (€)": r.cout_initial,
            "Surface cons. (m²)": r.surface_consommee_m2,
            "Valor. surface (€)": r.valorisation_surface,
            "Coût global (€)": r.cout_global,
            "Hygro.": r.statut_hygro,
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exporter CSV", csv, "renov_isol_resultats.csv", "text/csv")
else:
    st.warning("Aucune solution admissible.")

# ── Solutions écartées ─────────────────────────────────────────────────────────
if ecartees:
    with st.expander(f"Solutions écartées ({len(ecartees)})"):
        rows_e = [{"Matériau": r.nom, "Motif": r.motif_exclusion} for r in ecartees]
        st.dataframe(pd.DataFrame(rows_e), use_container_width=True, hide_index=True)

st.markdown("---")

# ── Graphiques ─────────────────────────────────────────────────────────────────
st.subheader("Graphiques")

if len(admissibles) >= 2:
    tab1, tab2 = st.tabs(["Coût initial vs Valorisation surface", "Épaisseur vs Coût global"])

    with tab1:
        df_g = pd.DataFrame([{
            "Matériau": r.nom,
            "Coût initial (€)": r.cout_initial,
            "Valorisation surface (€)": r.valorisation_surface,
            "Coût global (€)": r.cout_global,
            "Épaisseur (mm)": r.e_commerciale_mm,
        } for r in admissibles])
        fig = px.scatter(
            df_g, x="Coût initial (€)", y="Valorisation surface (€)",
            text="Matériau", size="Coût global (€)",
            color_discrete_sequence=["#5B7C8D"],
            title="Coût initial vs Valorisation économique indicative de la surface consommée",
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                          font_color="#2B3A42")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig2 = px.scatter(
            df_g, x="Épaisseur (mm)", y="Coût global (€)",
            text="Matériau", color_discrete_sequence=["#C1553B"],
            title="Épaisseur vs Coût global économique indicatif",
        )
        fig2.update_traces(textposition="top center")
        fig2.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                           font_color="#2B3A42")
        st.plotly_chart(fig2, use_container_width=True)
elif admissibles:
    st.info("Ajoutez au moins deux solutions admissibles pour afficher les graphiques comparatifs.")

st.markdown("---")

# ── Détail des calculs ─────────────────────────────────────────────────────────
with st.expander("🔍 Voir le détail des calculs"):
    for r in admissibles + ecartees:
        st.markdown(f"**{r.nom}**")
        for ligne in r.detail_calculs:
            st.markdown(f"- {ligne}")
        st.markdown("---")

# ── Export PDF ─────────────────────────────────────────────────────────────────
st.subheader("Export")
if st.button("📄 Générer le rapport PDF", type="primary"):
    with st.spinner("Génération du PDF…"):
        try:
            pdf_bytes = generer_pdf(
                nom_projet=nom_projet,
                params=params,
                principale=principale,
                alternative=alternative,
                ecartees=ecartees,
                explication_principale=expl_p,
                explication_alternative=expl_a,
            )
            st.download_button(
                "⬇️ Télécharger le PDF",
                data=pdf_bytes,
                file_name=f"renov_isol_{nom_projet.replace(' ', '_')}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"Erreur lors de la génération du PDF : {e}")
