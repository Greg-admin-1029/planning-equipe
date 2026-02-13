import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta

# ==========================================
# CONFIGURATION DE L'ÉQUIPE (À MODIFIER ICI)
# ==========================================
MEMBRES_EQUIPE = ["William", "Ritchie", "Emmanuel", "Kyle", "Kwamy"]
MANAGER_PASSWORD = "1989"  # Code simple pour l'accès manager
DATA_FILE = "planning_2026.json"

# Traduction manuelle pour éviter les soucis de locale serveur
JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

st.set_page_config(page_title="Planning Équipe 2026", layout="wide", page_icon="📅")

# ==========================================
# STYLE CSS PERSONNALISÉ (Léo)
# ==========================================
st.markdown(f"""
    <style>
    .main {{ background-color: #f8f9fa; }}
    /* Style pour les noms des collaborateurs */
    .emp-name {{
        background-color: #007bff;
        color: white;
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 10px;
    }}
    /* Forcer l'aspect compact du tableau */
    div[data-testid="stExpander"] {{ border: none; }}
    .stDataFrame td, .stDataFrame th {{
        width: 50px !important;
        height: 50px !important;
        text-align: center !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FONCTIONS DE DONNÉES
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ==========================================
# INTERFACE PRINCIPALE
# ==========================================
st.title("📅 Planning Équipe 2026")

# Sélection du mois
mois_sel = st.selectbox("Choisir un mois", range(1, 13), format_func=lambda x: MOIS_FR[x-1])

# Affichage des collaborateurs de manière très visible
cols_emp = st.columns(len(MEMBRES_EQUIPE))
for idx, name in enumerate(MEMBRES_EQUIPE):
    cols_emp[idx].markdown(f'<div class="emp-name">{name}</div>', unsafe_allow_html=True)

# Génération du calendrier pour le mois choisi
start_date = date(2026, mois_sel, 1)
if mois_sel == 12:
    end_date = date(2027, 1, 1) - timedelta(days=1)
else:
    end_date = date(2026, mois_sel + 1, 1) - timedelta(days=1)

jours = []
curr = start_date
while curr <= end_date:
    if curr.weekday() < 6: # Lundi à Samedi
        jours.append(curr)
    curr += timedelta(days=1)

# Création du tableau de bord
df_display = pd.DataFrame(index=[f"{JOURS_FR[d.weekday()]} {d.day}" for d in jours], columns=MEMBRES_EQUIPE)

for d in jours:
    date_str = d.strftime("%Y-%m-%d")
    row_label = f"{JOURS_FR[d.weekday()]} {d.day}"
    for m in MEMBRES_EQUIPE:
        statut = data.get(date_str, {}).get(m, "Présent")
        if statut == "Présent":
            df_display.at[row_label, m] = "✅"
        elif statut == "Télétravail":
            df_display.at[row_label, m] = "🏠"
        elif statut == "Absent":
            df_display.at[row_label, m] = "🚫"
        elif statut == "Fermeture":
            df_display.at[row_label, m] = "🔑"

# Affichage du tableau (Léo : colonnes plus étroites)
st.dataframe(df_display, use_container_width=True, height=600)

# ==========================================
# SECTION MANAGER
# ==========================================
st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ Espace Manager"):
    pwd = st.text_input("Mot de passe", type="password")
    if pwd == MANAGER_PASSWORD:
        st.success("Accès autorisé")
        target_date = st.date_input("Date à modifier", value=start_date, min_value=date(2026,1,1), max_value=date(2026,12,31))
        target_user = st.selectbox("Collaborateur", MEMBRES_EQUIPE)
        new_status = st.selectbox("Statut", ["Présent", "Télétravail", "Absent", "Fermeture"])
        
        if st.button("Mettre à jour"):
            d_str = target_date.strftime("%Y-%m-%d")
            if d_str not in data: data[d_str] = {}
            data[d_str][target_user] = new_status
            save_data(data)
            st.rerun()
    elif pwd != "":
        st.error("Mot de passe incorrect")
