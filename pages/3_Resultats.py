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
        st.metric("Surface perdue", f"{r.surface_consommee_m2} m²")
        st.metric("Coût des travaux", f"{r.cout_initial:,.0f} €")
        st.metric("Valeur des m² perdus", f"{r.valorisation_surface:,.0f} €")
        st.metric("Coût + valeur des m² perdus", f"{r.cout_global:,.0f} €")
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
    afficher_carte(principale, "✅ Coût + valeur des m² perdus le plus faible")
else:
    st.error("Aucune solution admissible n'a été trouvée pour les paramètres saisis.")

if alternative:
    afficher_carte(alternative, "💡 Coût des travaux le plus faible", "card-alt")

st.markdown("---")

# ── Tableau comparatif ─────────────────────────────────────────────────────────
st.subheader("Tableau comparatif — solutions admissibles")
if admissibles:
    rows = []
    for r in admissibles:
        rows.append({
            "Matériau": r.nom,
            "λ": r.lambda_val,
            "Épaisseur (mm)": r.e_commerciale_mm,
            "R obtenu": r.R_obtenu,
            "Fourniture (€)": r.cout_fourniture,
            "Pose (€)": r.cout_pose,
            "Coût des travaux (€)": r.cout_initial,
            "Surface perdue (m²)": r.surface_consommee_m2,
            "Valeur des m² perdus (€)": r.valorisation_surface,
            "Coût + valeur des m² perdus (€)": r.cout_global,
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

# ── Graphique d'aide à la décision ─────────────────────────────────────────────
st.subheader("Comparaison des solutions d'ITI")

if admissibles:
    # Le graphique est alimenté par TOUTES les solutions admissibles calculées.
    # Aucune liste de matériaux n'est codée en dur : ajouter un matériau à la base
    # qui passe les conditions l'ajoutera automatiquement ici.
    df_g = pd.DataFrame([{
        "Matériau": r.nom,
        "FabRef": (f"{r.fabricant} — {getattr(r, 'reference', '')}"
                   if getattr(r, 'reference', '') else (r.fabricant or "—")),
        "Ép. isolant (mm)": r.e_commerciale_mm,
        "Ép. totale (mm)": r.e_totale_mm,
        "R obtenu": r.R_obtenu,
        "Coût des travaux (€)": r.cout_initial,
        "Surface perdue (m²)": r.surface_consommee_m2,
        "Valeur des m² perdus (€)": r.valorisation_surface,
        "Somme": r.cout_global,          # coût des travaux + valeur des m² perdus (comparaison interne)
        "Fiabilité": getattr(r, "fiabilite", "—"),
    } for r in admissibles])

    # Taille des bulles = valeur des m² perdus. Si tout est à 0 (prix immobilier = 0),
    # on évite des bulles invisibles avec une taille constante.
    _val = df_g["Valeur des m² perdus (€)"]
    df_g["_taille"] = _val if _val.max() > 0 else 1.0

    fig = px.scatter(
        df_g,
        x="Coût des travaux (€)",
        y="Surface perdue (m²)",
        size="_taille",
        color="Somme",
        text="Matériau",
        custom_data=["Matériau", "FabRef", "Ép. isolant (mm)", "Ép. totale (mm)",
                     "R obtenu", "Coût des travaux (€)", "Surface perdue (m²)",
                     "Valeur des m² perdus (€)", "Fiabilité"],
        color_continuous_scale=[
            [0.0, "#1a9850"], [0.25, "#91cf60"], [0.5, "#fee08b"],
            [0.75, "#fc8d59"], [1.0, "#d73027"],
        ],
        size_max=48,
    )

    fig.update_traces(
        textposition="top center",
        textfont=dict(color="#2B3A42", size=11),
        marker=dict(line=dict(width=1, color="#2B3A42")),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]}<br>"
            "Épaisseur isolant : %{customdata[2]} mm<br>"
            "Épaisseur totale : %{customdata[3]} mm<br>"
            "R obtenu : %{customdata[4]} m².K/W<br>"
            "Coût des travaux : %{customdata[5]:,.0f} €<br>"
            "Surface perdue : %{customdata[6]:.2f} m²<br>"
            "Valeur des m² perdus : %{customdata[7]:,.0f} €<br>"
            "Fiabilité du prix : %{customdata[8]}"
            "<extra></extra>"
        ),
    )

    # Légende de couleur : Faible → Élevé (sans nommer la somme)
    smin, smax = float(df_g["Somme"].min()), float(df_g["Somme"].max())
    colorbar = dict(
        title=dict(text="Coût + valeur<br>des m² perdus", font=dict(color="#2B3A42")),
        tickfont=dict(color="#2B3A42"),
    )
    if smax > smin:
        colorbar.update(tickmode="array", tickvals=[smin, smax],
                        ticktext=["Faible", "Élevé"])

    fig.update_layout(
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(color="#2B3A42", size=13),
        xaxis=dict(
            title=dict(text="Coût des travaux (€)", font=dict(color="#2B3A42", size=14)),
            tickfont=dict(color="#2B3A42"), tickformat=",.0f",
            gridcolor="#E6E9EB", zerolinecolor="#C9CFD3",
            showline=True, linecolor="#9AA3A8",
        ),
        yaxis=dict(
            title=dict(text="Surface perdue (m²)", font=dict(color="#2B3A42", size=14)),
            tickfont=dict(color="#2B3A42"), tickformat=".2f",
            gridcolor="#E6E9EB", zerolinecolor="#C9CFD3",
            showline=True, linecolor="#9AA3A8",
        ),
        coloraxis_colorbar=colorbar,
        margin=dict(l=10, r=10, t=20, b=10),
        height=520,
    )

    fig.add_annotation(
        xref="paper", yref="paper", x=0.01, y=0.02,
        xanchor="left", yanchor="bottom", showarrow=False,
        text="↙ coût plus faible / moins de surface perdue",
        font=dict(color="#5B7C8D", size=11),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "**Comment lire le graphique ?** Plus une solution est à gauche, plus son coût "
        "de travaux est faible. Plus elle est basse, moins elle fait perdre de surface "
        "intérieure. La taille de la bulle représente la valeur des m² perdus selon le "
        "prix immobilier renseigné. La couleur permet de comparer le coût des travaux et "
        "cette valeur entre les solutions du projet."
    )
else:
    st.info("Aucune solution admissible à afficher. Ajustez le R cible ou la composition du mur.")

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
