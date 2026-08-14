"""
Couche d'accès à Google Sheets.
Deux onglets : 'materiaux' et 'analyses'.
La clé de service est chargée depuis st.secrets (jamais dans le code).
"""
import json
import streamlit as st
import gspread
from gspread.utils import ValueRenderOption
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_MATERIAUX = "materiaux"
SHEET_ANALYSES  = "analyses"

# ─── Colonnes ─────────────────────────────────────────────────────────────────
COLS_MATERIAUX = [
    "id", "nom", "famille", "fabricant", "reference", "actif",
    "lambda_wm K", "epaisseurs_mm",
    "mu", "perspirant", "statut_hygro_pierre", "statut_hygro_beton",
    "justification_hygro",
    "prix_fourniture_eur_m2", "prix_pose_eur_m2", "epaisseur_complementaire_mm",
    "source", "url", "date_maj",
]

COLS_ANALYSES = [
    "id", "date", "nom_projet",
    "surface_logement_m2", "surface_murs_m2", "lineaire_m", "hsp_m",
    "composition_mur", "R_cible", "prix_m2_logement",
]
# ──────────────────────────────────────────────────────────────────────────────


@st.cache_resource
def _get_client():
    """Connexion unique au compte de service Google."""
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_sheet(tab: str):
    gc = _get_client()
    sh = gc.open_by_key(st.secrets["sheet_id"])
    return sh.worksheet(tab)


def _ensure_header(ws, cols: list[str]):
    """Crée la ligne d'en-tête si l'onglet est vide."""
    if ws.row_count == 0 or ws.cell(1, 1).value != cols[0]:
        ws.clear()
        ws.append_row(cols)


# ─── Matériaux ─────────────────────────────────────────────────────────────────

def _to_float(v) -> float:
    """Convertit en float en acceptant la virgule OU le point (et les espaces/milliers)."""
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = (str(v).strip()
         .replace("\u202f", "").replace("\xa0", "").replace(" ", "")
         .replace(",", "."))
    try:
        return float(s)
    except ValueError:
        return 0.0


def lire_materiaux(actif_seulement: bool = True) -> pd.DataFrame:
    ws = _get_sheet(SHEET_MATERIAUX)
    # UNFORMATTED_VALUE : on récupère la valeur brute (le nombre) et non l'affichage
    # localisé « 0,032 » ; numericise_ignore=['all'] : on désactive la conversion auto de
    # gspread (qui lit la virgule française comme séparateur de milliers → 0,032 devient 32).
    data = ws.get_all_records(value_render_option=ValueRenderOption.unformatted,
                              numericise_ignore=["all"])
    if not data:
        return pd.DataFrame(columns=COLS_MATERIAUX)
    df = pd.DataFrame(data)
    # epaisseurs_mm stocké en JSON string
    df["epaisseurs_mm"] = df["epaisseurs_mm"].apply(
        lambda x: json.loads(x) if isinstance(x, str) and x.strip().startswith("[")
        else (x if isinstance(x, list) else [])
    )
    # Colonnes numériques : lecture tolérante (virgule ou point)
    for _c in ["lambda_wm K", "mu", "prix_fourniture_eur_m2", "prix_pose_eur_m2",
               "epaisseur_complementaire_mm"]:
        if _c in df.columns:
            df[_c] = df[_c].apply(_to_float)
    if actif_seulement:
        df = df[df["actif"].apply(
            lambda x: str(x).strip() in ("1", "1.0", "True", "true", "oui", "Oui", "VRAI"))]
    return df.reset_index(drop=True)


def ajouter_materiau(data: dict) -> bool:
    try:
        ws = _get_sheet(SHEET_MATERIAUX)
        _ensure_header(ws, COLS_MATERIAUX)
        # Générer un id unique
        existing = ws.get_all_values()
        new_id = len(existing)  # entête = ligne 1, donc nb lignes - 1
        data["id"] = new_id
        data["date_maj"] = datetime.now().strftime("%Y-%m-%d")
        data["actif"] = 1
        # Sérialiser les épaisseurs
        if isinstance(data.get("epaisseurs_mm"), list):
            data["epaisseurs_mm"] = json.dumps(data["epaisseurs_mm"])
        row = [data.get(c, "") for c in COLS_MATERIAUX]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'ajout : {e}")
        return False


def modifier_materiau(mat_id: int, updates: dict) -> bool:
    try:
        ws = _get_sheet(SHEET_MATERIAUX)
        data = ws.get_all_records()
        for i, row in enumerate(data, start=2):  # ligne 1 = entête
            if int(row.get("id", -1)) == mat_id:
                for key, val in updates.items():
                    if key in COLS_MATERIAUX:
                        col_idx = COLS_MATERIAUX.index(key) + 1
                        if key == "epaisseurs_mm" and isinstance(val, list):
                            val = json.dumps(val)
                        ws.update_cell(i, col_idx, val)
                return True
        return False
    except Exception as e:
        st.error(f"Erreur lors de la modification : {e}")
        return False


def toggle_actif(mat_id: int, actif: bool) -> bool:
    return modifier_materiau(mat_id, {"actif": 1 if actif else 0})


# ─── Analyses ──────────────────────────────────────────────────────────────────

def sauvegarder_analyse(data: dict) -> bool:
    try:
        ws = _get_sheet(SHEET_ANALYSES)
        _ensure_header(ws, COLS_ANALYSES)
        existing = ws.get_all_values()
        data["id"] = len(existing)
        data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [data.get(c, "") for c in COLS_ANALYSES]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")
        return False
