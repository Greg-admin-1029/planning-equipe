import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta

# ==========================================
# CONFIGURATION
# ==========================================
MEMBRES_EQUIPE = ["Collaborateur 1", "Collaborateur 2", "Collaborateur 3", "Collaborateur 4", "Collaborateur 5"]
MANAGER_PASSWORD = "admin"
DATA_FILE = "planning_2026.json"
CONGES_FILE = "conges_2026.json"

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

st.set_page_config(page_title="Planning 2026", layout="wide")

# ==========================================
# STYLE CSS (Léo) - Texte Noir & Tableau
# ==========================================
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    thead tr th { background-color: #2c3e50 !important; color: white !important; font-weight: bold !important; }
    .stDataFrame td { text-align: center !important; font-size: 18px !important; }
    
    /* Style pour le récapitulatif latéral : TEXTE NOIR */
    .recap-container {
        padding: 10px;
        border-radius: 5px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
        border-left: 5px solid #2c3e50;
        color: #000000 !important; /* Force le noir */
    }
    .recap-name { font-weight: bold; color: #000000 !important; margin-bottom: 2px; }
    .recap-stats { font-size: 14px; color: #000000 !important; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GESTION DES FICHIERS
# ==========================================
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f: return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f: json.dump(data, f)

data_planning = load_json(DATA_FILE)
data_conges = load_json(CONGES_FILE)

def get_stats():
    stats = {m: {"fermetures": 0, "vacances": 0, "absences": 0} for m in MEMBRES_EQUIPE}
    for d_key, membres in data_planning.items():
        for m, statut in membres.items():
            if m in stats:
                if statut == "Fermeture": stats[m]["fermetures"] += 1
                elif statut == "Vacances": stats[m]["vacances"] += 1
                elif statut == "Absent": stats[m]["absences"] += 1
    return stats

# ==========================================
# BARRE LATÉRALE
# ==========================================
with st.sidebar:
    st.title("Menu")
    page = st.radio("Navigation", ["📅 Voir le Planning", "✉️ Demande de Congés", "🔒 Espace Manager"])
    st.markdown("---")
    st.subheader("📊 Récapitulatif 2026")
    current_stats = get_stats()
    for m in MEMBRES_EQUIPE:
        s = current_stats[m]
        st.markdown(f"""
        <div class="recap-container">
            <div class="recap-name">{m}</div>
            <div class="recap-stats">
                🔑 Fermetures : {s['fermetures']}<br>
                ✈️ Vacances : {s['vacances']}<br>
                🚫 Absences : {s['absences']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 1 : PLANNING + COLONNE TOTAL
# ==========================================
if page == "📅 Voir le Planning":
    st.header("Planning de l'équipe 2026")
    mois_sel = st.selectbox("Mois", range(1, 13), format_func=lambda x: MOIS_FR[x-1])
    
    start_date = date(2026, mois_sel, 1)
    if mois_sel == 12: end_date = date(2027, 1, 1) - timedelta(days=1)
    else: end_date = date(2026, mois_sel + 1, 1) - timedelta(days=1)

    jours = []
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 6: jours.append(curr)
        curr += timedelta(days=1)

    # Ajout de "Total Présents" dans les colonnes
    colonnes_tableau = MEMBRES_EQUIPE + ["Total Présents"]
    df = pd.DataFrame(index=[f"{JOURS_FR[d.weekday()]} {d.day}" for d in jours], columns=colonnes_tableau)

    for d in jours:
        d_str = d.strftime("%Y-%m-%d")
        row_label = f"{JOURS_FR[d.weekday()]} {d.day}"
        count_present = 5 # On part du maximum
        
        for m in MEMBRES_EQUIPE:
            s = data_planning.get(d_str, {}).get(m, "Présent")
            # Calcul de présence (Absent et Vacances retirent une personne)
            if s in ["Absent", "Vacances"]:
                count_present -= 1
            
            icones = {"Présent":"✅","Télétravail":"🏠","Absent":"🚫","Fermeture":"🔑","Vacances":"✈️"}
            df.at[row_label, m] = icones.get(s, "✅")
        
        # Remplissage de la colonne Total
        df.at[row_label, "Total Présents"] = f"👥 {count_present}"

    st.dataframe(
        df, 
        use_container_width=True, 
        height=750,
        column_config={
            col: st.column_config.TextColumn(width="small") for col in colonnes_tableau
        }
    )
    st.info("Légende : ✅ Présent | 🏠 Télétravail | 🚫 Absent | 🔑 Fermeture | ✈️ Vacances")

# ==========================================
# PAGE 2 : CONGÉS
# ==========================================
elif page == "✉️ Demande de Congés":
    st.header("Soumettre une demande")
    with st.form("f"):
        nom = st.selectbox("Nom", MEMBRES_EQUIPE); deb = st.date_input("Du"); fin = st.date_input("Au"); mot = st.text_area("Motif")
        if st.form_submit_button("Envoyer"):
            data_conges[datetime.now().strftime("%Y%m%d%H%M%S")] = {"nom":nom,"debut":str(deb),"fin":str(fin),"motif":mot}
            save_json(CONGES_FILE, data_conges); st.success("Demande envoyée !")

# ==========================================
# PAGE 3 : MANAGER
# ==========================================
elif page == "🔒 Espace Manager":
    st.header("Administration")
    if st.text_input("Mot de passe", type="password") == MANAGER_PASSWORD:
        t1, t2, t3 = st.tabs(["Modification Unique", "🔄 Actions Groupées", "Gérer les Demandes"])
        
        with t1:
            d_m = st.date_input("Jour", date(2026,1,1)); u_m = st.selectbox("Qui", MEMBRES_EQUIPE); s_m = st.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances"])
            if st.button("Mettre à jour"):
                ds = d_m.strftime("%Y-%m-%d")
                if ds not in data_planning: data_planning[ds] = {}
                data_planning[ds][u_m] = s_m
                save_json(DATA_FILE, data_planning); st.success("Planning mis à jour !"); st.rerun()

        with t2:
            st.subheader("Appliquer une règle sur toute l'année")
            c1, c2, c3 = st.columns(3)
            user_rec = c1.selectbox("Pour qui ?", MEMBRES_EQUIPE, key="rec1")
            day_rec = c2.selectbox("Chaque...", JOURS_FR[:6], key="rec2")
            stat_rec = c3.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances"], key="rec3")
            if st.button("Appliquer à toute l'année 2026"):
                day_idx = JOURS_FR.index(day_rec)
                curr = date(2026, 1, 1)
                while curr.year == 2026:
                    if curr.weekday() == day_idx:
                        ds = curr.strftime("%Y-%m-%d")
                        if ds not in data_planning: data_planning[ds] = {}
                        data_planning[ds][user_rec] = stat_rec
                    curr += timedelta(days=1)
                save_json(DATA_FILE, data_planning); st.success("Règle appliquée !"); st.rerun()

        with t3:
            for k, v in list(data_conges.items()):
                st.write(f"**{v['nom']}** : {v['debut']} au {v['fin']}")
                if st.button(f"Supprimer {k}"): del data_conges[k]; save_json(CONGES_FILE, data_conges); st.rerun()
