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

# Configuration de la page
st.set_page_config(page_title="Planning 2026", layout="wide", page_icon="📅")

# CSS pour le look "Clean & White"
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 8px; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #007bff; color: white; }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .status-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GESTION DES DONNÉES
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"events": {}, "conges_en_attente": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = load_data()

# ==========================================
# LOGIQUE CALENDRIER
# ==========================================
MONTHS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
          "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

def get_days_of_month(month_idx, year=2026):
    start_date = date(year, month_idx + 1, 1)
    if month_idx == 11:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month_idx + 2, 1)
    
    days = []
    curr = start_date
    while curr < end_date:
        if curr.weekday() != 6:  # Exclure Dimanche (0=Lun, 6=Dim)
            days.append(curr.isoformat())
        curr += timedelta(days=1)
    return days

# ==========================================
# BARRE LATÉRALE & NAVIGATION
# ==========================================
with st.sidebar:
    st.title("🕒 Planning 2026")
    menu = st.radio("Navigation", ["📅 Planning Équipe", "📝 Demander un Congé", "🔐 Espace Manager"])
    
    st.divider()
    if menu == "🔐 Espace Manager":
        pwd = st.text_input("Code d'accès", type="password")
        is_manager = pwd == MANAGER_PASSWORD
    else:
        is_manager = False

# ==========================================
# VUE 1 : PLANNING ÉQUIPE
# ==========================================
if menu == "📅 Planning Équipe":
    st.header("Visualisation de l'équipe")
    
    col1, col2 = st.columns([2, 4])
    with col1:
        selected_month_name = st.selectbox("Choisir un mois", MONTHS)
        month_idx = MONTHS.index(selected_month_name)
    
    days = get_days_of_month(month_idx)
    
    # Construction du tableau de données
    table_data = []
    for d in days:
        dt = date.fromisoformat(d)
        day_str = dt.strftime("%a %d %b")
        
        row = {"Date": day_str}
        presences = 0
        
        for p in MEMBRES_EQUIPE:
            status = st.session_state.db["events"].get(d, {}).get(p, "✅ Présent")
            row[p] = status
            if status == "✅ Présent" or status == "🔑 Fermeture":
                presences += 1
        
        row["Dispo"] = f"{presences}/{len(MEMBRES_EQUIPE)}"
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Affichage avec style
    st.table(df)
    
    st.info("Légende : 🏠 Télétravail | 🚫 Absent | 🔑 Fermeture | ✅ Présent")

# ==========================================
# VUE 2 : DEMANDE DE CONGÉS
# ==========================================
elif menu == "📝 Demander un Congé":
    st.header("Nouvelle demande de congé")
    
    with st.form("leave_form"):
        nom = st.selectbox("Votre nom", MEMBRES_EQUIPE)
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            debut = st.date_input("Date de début", min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))
        with col_d2:
            fin = st.date_input("Date de fin", min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))
        
        motif = st.text_area("Motif (optionnel)")
        submit = st.form_submit_button("Envoyer la demande")
        
        if submit:
            nouvelle_demande = {
                "id": len(st.session_state.db["conges_en_attente"]),
                "nom": nom,
                "debut": debut.isoformat(),
                "fin": fin.isoformat(),
                "motif": motif,
                "statut": "En attente"
            }
            st.session_state.db["conges_en_attente"].append(nouvelle_demande)
            save_data(st.session_state.db)
            st.success("Demande envoyée au manager !")

# ==========================================
# VUE 3 : ESPACE MANAGER
# ==========================================
elif menu == "🔐 Espace Manager":
    if not is_manager:
        st.warning("Veuillez saisir le code d'accès correct dans la barre latérale.")
    else:
        tab1, tab2 = st.tabs(["⚡ Actions Rapides", "📩 Demandes de congés"])
        
        with tab1:
            st.subheader("Assigner un statut")
            c1, c2, c3 = st.columns(3)
            with c1:
                m_date = st.date_input("Jour", value=date(2026, 1, 1))
            with c2:
                m_pers = st.selectbox("Collaborateur", MEMBRES_EQUIPE)
            with c3:
                m_statut = st.selectbox("Statut", ["✅ Présent", "🏠 Télétravail", "🚫 Absent", "🔑 Fermeture"])
            
            if st.button("Mettre à jour le planning"):
                d_str = m_date.isoformat()
                if d_str not in st.session_state.db["events"]:
                    st.session_state.db["events"][d_str] = {}
                
                # Si c'est une fermeture, on vérifie si quelqu'un d'autre fermait déjà
                if m_statut == "🔑 Fermeture":
                    for p in MEMBRES_EQUIPE:
                        if st.session_state.db["events"][d_str].get(p) == "🔑 Fermeture":
                            st.session_state.db["events"][d_str][p] = "✅ Présent"
                
                st.session_state.db["events"][d_str][m_pers] = m_statut
                save_data(st.session_state.db)
                st.success(f"Planning mis à jour pour {m_pers}")

        with tab2:
            st.subheader("Validation des congés")
            demandes = st.session_state.db["conges_en_attente"]
            
            if not demandes:
                st.write("Aucune demande en attente.")
            
            for idx, req in enumerate(demandes):
                with st.expander(f"Demande de {req['nom']} (Du {req['debut']} au {req['fin']})"):
                    st.write(f"**Motif:** {req['motif']}")
                    col_acc, col_ref = st.columns(2)
                    
                    if col_acc.button("✅ Approuver", key=f"app_{idx}"):
                        # Inscrire dans le planning
                        d_start = date.fromisoformat(req['debut'])
                        d_end = date.fromisoformat(req['fin'])
                        curr = d_start
                        while curr <= d_end:
                            d_str = curr.isoformat()
                            if d_str not in st.session_state.db["events"]:
                                st.session_state.db["events"][d_str] = {}
                            st.session_state.db["events"][d_str][req['nom']] = "🚫 Absent"
                            curr += timedelta(days=1)
                        
                        st.session_state.db["conges_en_attente"].pop(idx)
                        save_data(st.session_state.db)
                        st.rerun()
                        
                    if col_ref.button("❌ Refuser", key=f"ref_{idx}"):
                        st.session_state.db["conges_en_attente"].pop(idx)
                        save_data(st.session_state.db)
                        st.rerun()

# Pied de page
st.divider()
st.caption("Application Planning 2026 - Minimalist HR Tool")
