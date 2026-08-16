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


# ── Explication des résultats ──────────────────────────────────────────────────
if not admissibles:
    st.error("Aucune solution admissible n'a été trouvée pour les paramètres saisis. "
             "Ajustez le R cible ou la composition du mur dans Nouvelle analyse.")
else:
    st.markdown(
        "Le tableau ci-dessous liste **toutes les solutions techniquement admissibles** : "
        "elles atteignent le R cible et sont compatibles avec le mur. Pour chacune, on compare "
        "le **coût des travaux**, la **surface perdue** et la **valeur des m² perdus**. "
        "Le graphique plus bas les positionne les unes par rapport aux autres — la zone "
        "**en bas à gauche** réunit les solutions les moins chères qui font perdre le moins de surface."
    )

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
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exporter CSV", csv, "renov_isol_resultats.csv", "text/csv")
else:
    st.warning("Aucune solution admissible.")

# ── Comportement hygrothermique (HYGROBA) ──────────────────────────────────────
st.markdown("---")
st.subheader("Comportement hygrothermique (HYGROBA)")
st.caption(
    f"Mur : **{params.get('composition_mur', '—')}** · finition extérieure : "
    f"**{params.get('etat_exterieur', '—')}** → côté extérieur classé "
    f"**{params.get('classe_exterieur', '—')}**. La configuration croise ce côté extérieur avec "
    "la classe P/E de chaque isolant. **Seules les configurations privilégiées par HYGROBA sont "
    "retenues** dans la comparaison ci-dessus ; les autres apparaissent plus bas dans "
    "« Solutions non retenues »."
)
with st.expander("ⓘ Comprendre les indicateurs HYGROBA"):
    st.markdown(
        "HYGROBA évalue **trois critères**, chacun sur **trois niveaux** (repris tels quels de "
        "l'étude, sans score chiffré).\n\n"
        "**💧 Quantité d'eau dans la paroi**\n"
        "- 🟢 Faible : peu d'accumulation d'eau et stabilisation.\n"
        "- 🟡 Moyenne.\n"
        "- 🔴 Élevée : accumulation d'eau importante ou stabilisation insuffisante.\n\n"
        "**🌬️ Capacité de séchage en présence d'infiltrations d'humidité**\n"
        "- 🟢 Élevée : peu d'accumulation et stabilisation.\n"
        "- 🟡 Moyenne.\n"
        "- 🔴 Faible : accumulation d'eau importante ou stabilisation insuffisante.\n\n"
        "**💦 Risque de condensation interne dans la paroi**\n"
        "- 🟢 Faible : humidité relative constamment inférieure à 85 %.\n"
        "- 🟡 Modéré : humidité relative comprise entre 85 % et 95 %.\n"
        "- 🔴 Important : humidité relative supérieure à 95 %.\n\n"
        "**Légende générale** : 🟢 Situation favorable — 🟡 Niveau intermédiaire / vigilance — "
        "🔴 Situation défavorable.\n\n"
        "*Cette légende est une aide visuelle ; les intitulés techniques exacts ci-dessus "
        "(« faible », « moyenne », « élevée »…) restent la référence.*"
    )

if admissibles:
    _emoji = {"vert": "🟢", "orange": "🟡", "rouge": "🔴"}
    _lab = {
        "eau": {"vert": "Faible", "orange": "Moyenne", "rouge": "Élevée"},
        "sechage": {"vert": "Élevée", "orange": "Moyenne", "rouge": "Faible"},
        "condensation": {"vert": "Risque faible", "orange": "Risque modéré",
                         "rouge": "Risque important"},
    }
    _stat = {"privilégier": "✅ Retenue par la présélection HYGROBA",
             "vigilance": "⚠️ Retenue par la présélection HYGROBA — vigilance"}

    def _cell(crit, coul):
        return f"{_emoji.get(coul, '')} {_lab[crit].get(coul, coul)}"

    hrows = []
    for r in admissibles:
        if r.hygro_exploitable and r.hygro_criteres:
            c = r.hygro_criteres
            hrows.append({
                "Matériau": r.nom,
                "Classe P/E": r.classe_hygrique or "—",
                "Configuration": r.hygro_config,
                "Statut": _stat.get(r.hygro_statut, r.hygro_statut or "—"),
                "💧 Quantité d'eau": _cell("eau", c["eau"]),
                "🌬️ Capacité de séchage": _cell("sechage", c["sechage"]),
                "💦 Condensation interne": _cell("condensation", c["condensation"]),
            })
        else:
            hrows.append({
                "Matériau": r.nom,
                "Classe P/E": r.classe_hygrique or "—",
                "Configuration": r.hygro_config or "—",
                "Statut": "Vérification complémentaire",
                "💧 Quantité d'eau": "Vérification hygrothermique complémentaire nécessaire",
                "🌬️ Capacité de séchage": "",
                "💦 Condensation interne": "",
            })
    st.dataframe(pd.DataFrame(hrows), use_container_width=True, hide_index=True)
    st.caption("🟢 Situation favorable — 🟡 Niveau intermédiaire / vigilance — 🔴 Situation "
               "défavorable. Les intitulés techniques (« faible », « moyenne », « élevée »…) "
               "restent la référence.")
    # Alertes de vigilance (ex. pierre calcaire dure : faible capacité de séchage)
    for a in sorted({r.hygro_alerte for r in admissibles if r.hygro_alerte}):
        st.warning(a)
    st.info(
        "Cette présélection constitue une aide à la décision fondée sur les résultats de l'étude "
        "HYGROBA. Elle ne remplace pas une étude hygrothermique spécifique de la paroi et des "
        "solutions retenues avant mise en œuvre."
    )

# ── Solutions non retenues ─────────────────────────────────────────────────────
if ecartees:
    st.markdown("---")
    st.subheader("Solutions non retenues")
    st.caption("Ces solutions ne figurent pas dans la comparaison ci-dessus. Elles ne sont pas "
               "« interdites » : elles sont écartées par le R cible, la compatibilité ITI, "
               "ou le filtre de présélection HYGROBA pour cette configuration de paroi.")
    st.dataframe(
        pd.DataFrame([{
            "Matériau": r.nom,
            "Classe P/E": r.classe_hygrique or "—",
            "Configuration": r.hygro_config or "—",
            "Motif": r.motif_exclusion,
        } for r in ecartees]),
        use_container_width=True, hide_index=True)

# ── Graphique d'aide à la décision ─────────────────────────────────────────────
st.subheader("Comparaison des solutions d'ITI")

if admissibles:
    # Le graphique est alimenté par TOUTES les solutions admissibles calculées.
    # Aucune liste de matériaux n'est codée en dur : ajouter un matériau à la base
    # qui passe les conditions l'ajoutera automatiquement ici.
    # Numérotation liée à la couleur : 1 = le plus vert (coût + valeur le plus faible),
    # les numéros augmentent vers le rouge (coût + valeur le plus élevé).
    _ranked = sorted(range(len(admissibles)), key=lambda k: admissibles[k].cout_global)
    _numero = {idx: rank for rank, idx in enumerate(_ranked, start=1)}

    df_g = pd.DataFrame([{
        "N°": str(_numero[i]),
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
    } for i, r in enumerate(admissibles)])

    _val = df_g["Valeur des m² perdus (€)"]
    df_g["_taille"] = _val if _val.max() > 0 else 1.0

    # Dodge : quand des solutions ont un coût ET une surface très proches, leurs bulles se
    # chevauchent. On décale légèrement leur position horizontale (en éventail) pour les rendre
    # lisibles. Les valeurs exactes restent dans l'infobulle et le tableau ci-dessus.
    import numpy as np
    from collections import defaultdict
    _xs = df_g["Coût des travaux (€)"].to_numpy(dtype=float)
    _ys = df_g["Surface perdue (m²)"].to_numpy(dtype=float)
    _rx = float(_xs.max() - _xs.min()) or max(float(_xs.max()), 1.0)
    _ry = float(_ys.max() - _ys.min()) or 1.0
    _groups = defaultdict(list)
    for _i in range(len(_xs)):
        _groups[(round(_xs[_i] / (_rx * 0.07)), round(_ys[_i] / (_ry * 0.09)))].append(_i)
    _xp = _xs.copy()
    _factor = 0.09  # écartement en % (régulier aussi en échelle log)
    for _idxs in _groups.values():
        if len(_idxs) > 1:
            for _j, _i in enumerate(sorted(_idxs)):
                _xp[_i] = _xs[_i] * (1.0 + (_j - (len(_idxs) - 1) / 2.0) * _factor)
    df_g["x_plot"] = _xp

    fig = px.scatter(
        df_g,
        x="x_plot",
        y="Surface perdue (m²)",
        size="_taille",
        color="Somme",
        text="N°",
        custom_data=["Matériau", "FabRef", "Ép. isolant (mm)", "Ép. totale (mm)",
                     "R obtenu", "Coût des travaux (€)", "Surface perdue (m²)",
                     "Valeur des m² perdus (€)", "Fiabilité"],
        color_continuous_scale=[
            [0.0, "#1a9850"], [0.25, "#91cf60"], [0.5, "#fee08b"],
            [0.75, "#fc8d59"], [1.0, "#d73027"],
        ],
        size_max=34,
        opacity=0.6,
    )

    fig.update_traces(
        textposition="middle center",
        textfont=dict(color="#1a1a1a", size=11, family="Arial Black, Arial, sans-serif"),
        marker=dict(sizemin=5, line=dict(width=1.1, color="#2B3A42")),
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

    smin, smax = float(df_g["Somme"].min()), float(df_g["Somme"].max())
    colorbar = dict(
        title=dict(text="Coût + valeur<br>des m² perdus", font=dict(color="#2B3A42", size=11)),
        tickfont=dict(color="#2B3A42"), thickness=14, len=0.9,
    )
    if smax > smin:
        colorbar.update(tickmode="array", tickvals=[smin, smax], ticktext=["Faible", "Élevé"])

    fig.update_layout(
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(color="#2B3A42", size=13),
        xaxis=dict(
            title=dict(text="Coût des travaux (€) — échelle logarithmique",
                       font=dict(color="#2B3A42", size=14)),
            type="log", tickfont=dict(color="#2B3A42"), tickformat=",.0f",
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
        margin=dict(l=10, r=0, t=20, b=10),
        height=560,
    )

    fig.add_annotation(
        xref="paper", yref="paper", x=0.01, y=0.02,
        xanchor="left", yanchor="bottom", showarrow=False,
        text="↙ coût plus faible / moins de surface perdue",
        font=dict(color="#5B7C8D", size=11),
    )

    st.plotly_chart(fig, use_container_width=True)

    legende = "   ·   ".join(f"**{rank}.** {admissibles[idx].nom}"
                             for rank, idx in enumerate(_ranked, start=1))
    st.markdown("**Repères :**  " + legende)

    st.caption(
        "**Comment lire le graphique ?** Chaque bulle est une solution : plus elle est à gauche, "
        "moins les travaux coûtent cher ; plus elle est basse, moins elle fait perdre de surface. "
        "L'axe des coûts est en **échelle logarithmique** (graduations 2 500, 5 000, 10 000, 20 000…) : "
        "les écarts entre solutions abordables restent visibles même en présence d'une solution très chère. "
        "La taille représente la valeur des m² perdus. **Les numéros suivent la couleur : le n°1 est "
        "la solution la plus verte** (coût + valeur des m² perdus le plus faible), et les numéros "
        "augmentent vers le rouge. Quand plusieurs solutions sont très proches, leurs bulles sont "
        "légèrement écartées à l'horizontale pour rester lisibles — les valeurs exactes sont dans "
        "l'infobulle et dans le tableau ci-dessus."
    )
else:
    st.info("Aucune solution admissible à afficher. Ajustez le R cible ou la composition du mur.")

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
                admissibles=admissibles,
            )
            st.download_button(
                "⬇️ Télécharger le PDF",
                data=pdf_bytes,
                file_name=f"renov_isol_{nom_projet.replace(' ', '_')}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"Erreur lors de la génération du PDF : {e}")
