"""
RENOV'ISOL — Point d'entrée Streamlit.
"""
import streamlit as st

st.set_page_config(
    page_title="RENOV'ISOL",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS global ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #2B3A42; }
[data-testid="stSidebar"] * { color: #F1F3F4 !important; }
[data-testid="stSidebarNav"] a { color: #F1F3F4 !important; }
h1, h2, h3 { color: #2B3A42; }
.badge-compatible   { background:#e8f5e9; color:#2e7d32; border-radius:6px;
                      padding:2px 10px; font-weight:600; font-size:.85em; }
.badge-averifier    { background:#fff8e1; color:#f57f17; border-radius:6px;
                      padding:2px 10px; font-weight:600; font-size:.85em; }
.badge-incompatible { background:#fce4ec; color:#c62828; border-radius:6px;
                      padding:2px 10px; font-weight:600; font-size:.85em; }
.card { background:#F1F3F4; border-radius:12px; padding:20px 24px;
        margin-bottom:16px; border-left:4px solid #C1553B; }
.card-alt { border-left:4px solid #5B7C8D; }
</style>
""", unsafe_allow_html=True)

# ─── Page d'accueil ───────────────────────────────────────────────────────────
st.title("🏛️ RENOV'ISOL")
st.subheader("Outil d'aide à la décision pour l'isolation thermique par l'intérieur des bâtiments anciens")

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🌡️ PERFORMANCE")
    st.markdown("Vérification de l'atteinte de la résistance thermique cible pour chaque solution.")
with col2:
    st.markdown("### 📐 ÉPAISSEUR")
    st.markdown("Quantification de la surface habitable consommée selon le matériau retenu.")
with col3:
    st.markdown("### 💶 ÉCONOMIE")
    st.markdown("Comparaison du coût initial et du coût global économique indicatif.")

st.markdown("---")

st.info(
    "**Comment utiliser l'outil ?**  \n"
    "1. Rendez-vous dans **Nouvelle analyse** (menu de gauche).  \n"
    "2. Renseignez les caractéristiques du projet.  \n"
    "3. Lancez l'analyse — l'outil compare automatiquement tous les matériaux de la base.  \n"
    "4. Consultez les recommandations, les graphiques et le détail des calculs."
)

st.markdown("---")
st.caption(
    "RENOV'ISOL est un outil d'aide à la décision. "
    "Il ne remplace pas une étude thermique réglementaire, "
    "une simulation thermique dynamique, une étude hygrothermique détaillée "
    "ou une expertise du bâtiment."
)
