import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta

# ==========================================
# CONFIGURATION
# ==========================================
MEMBRES_EQUIPE = ["William", "Ritchie", "Emmanuel", "Grégory", "Kyle"]
MANAGER_PASSWORD = "admin"
DATA_FILE = "planning_2026.json"
CONGES_FILE = "conges_2026.json"

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

st.set_page_config(page_title="Planning 2026", layout="wide")

# ==========================================
# STYLE CSS
# ==========================================
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    thead tr th { background-color: #2c3e50 !important; color: white !important; font-weight: bold !important; }
    .stDataFrame td { text-align: center !important; font-size: 18px !important; }
    
    .recap-container {
        padding: 10px;
        border-radius: 5px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
        border-left: 5px solid #2c3e50;
        color: #000000 !important;
    }
    .recap-name { font-weight: bold; color: #000000 !important; margin-bottom: 2px; }
    .recap-stats { font-size: 13px; color: #000000 !important; font-weight: 500; }
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
    stats = {m: {"fermetures": 0, "vacances": 0, "absences": 0, "samedis": 0} for m in MEMBRES_EQUIPE}
    for d_key, membres in data_planning.items():
        for m, info in membres.items():
            statut = info["statut"] if isinstance(info, dict) else info
            if m in stats:
                if statut == "Fermeture": stats[m]["fermetures"] += 1
                elif statut == "Vacances": stats[m]["vacances"] += 1
                elif statut == "Absent": stats[m]["absences"] += 1
                elif statut == "Travail Samedi": stats[m]["samedis"] += 1
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
                🔑 Fermetures : {s['fermetures']} | ✈️ Vacances : {s['vacances']}<br>
                🚫 Absences : {s['absences']} | 🛠️ Samedis : {s['samedis']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 1 : PLANNING
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

    colonnes_tableau = MEMBRES_EQUIPE + ["Total Présents"]
    df = pd.DataFrame(index=[f"{JOURS_FR[d.weekday()]} {d.day}" for d in jours], columns=colonnes_tableau)

    for d in jours:
        d_str = d.strftime("%Y-%m-%d")
        row_label = f"{JOURS_FR[d.weekday()]} {d.day}"
        count_present = len(MEMBRES_EQUIPE) 
        
        for m in MEMBRES_EQUIPE:
            info = data_planning.get(d_str, {}).get(m, "Présent")
            statut = info.get("statut", "Présent") if isinstance(info, dict) else info
            note = info.get("note", "") if isinstance(info, dict) else ""

            if statut in ["Absent", "Vacances"]:
                count_present -= 1
            
            icones = {"Présent":"✅","Télétravail":"🏠","Absent":"🚫","Fermeture":"🔑","Vacances":"✈️","Travail Samedi":"🛠️"}
            emoj = icones.get(statut, "✅")
            df.at[row_label, m] = f"{note} {emoj}" if note else emoj
        
        df.at[row_label, "Total Présents"] = f"👥 {count_present}"

    st.dataframe(df, use_container_width=True, height=750, column_config={col: st.column_config.TextColumn(width="medium") for col in colonnes_tableau})
    st.info("Légende : ✅ Présent | 🏠 Télétravail | 🚫 Absent | 🔑 Fermeture | ✈️ Vacances | 🛠️ Travail Samedi")

# ==========================================
# PAGE 2 : CONGÉS
# ==========================================
elif page == "✉️ Demande de Congés":
    st.header("Soumettre une demande")
    with st.form("form_conges"):
        c1, c2 = st.columns(2)
        nom = c1.selectbox("Votre nom", MEMBRES_EQUIPE)
        type_conge = c2.selectbox("Type de demande", ["Vacances ✈️", "Absence 🚫", "Télétravail 🏠"])
        d_deb = c1.date_input("Date de début", date.today())
        d_fin = c2.date_input("Date de fin", date.today())
        motif = st.text_area("Note / Motif")
        if st.form_submit_button("Envoyer la demande"):
            if d_deb <= d_fin:
                key = datetime.now().strftime("%Y%m%d_%H%M%S")
                data_conges[key] = {"nom": nom, "type": type_conge, "debut": str(d_deb), "fin": str(d_fin), "motif": motif, "date_demande": datetime.now().strftime("%d/%m/%Y %H:%M")}
                save_json(CONGES_FILE, data_conges)
                st.success("Demande envoyée !")
            else: st.error("Date de fin invalide.")

# ==========================================
# PAGE 3 : MANAGER
# ==========================================
elif page == "🔒 Espace Manager":
    st.header("Administration")
    if st.text_input("Mot de passe", type="password") == MANAGER_PASSWORD:
        t1, t2, t3 = st.tabs(["Modification Unique / Période", "🔄 Actions Groupées", "✉️ Demandes reçues"])
        
        with t1:
            type_mod = st.radio("Type", ["Un seul jour", "Une période"], horizontal=True)
            col_a, col_b = st.columns(2)
            u_m = col_a.selectbox("Collaborateur", MEMBRES_EQUIPE)
            s_m = col_b.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"])
            n_m = col_b.text_input("Note")
            
            dates_a_modifier = []
            if type_mod == "Un seul jour":
                dates_a_modifier = [col_a.date_input("Jour", date(2026,1,1))]
            else:
                d1 = col_a.date_input("Début", date(2026,1,1)); d2 = col_a.date_input("Fin", date(2026,1,1))
                if d1 <= d2:
                    curr = d1
                    while curr <= d2:
                        dates_a_modifier.append(curr); curr += timedelta(days=1)

            if st.button("Enregistrer"):
                for d in dates_a_modifier:
                    ds = d.strftime("%Y-%m-%d")
                    if ds not in data_planning: data_planning[ds] = {}
                    data_planning[ds][u_m] = {"statut": s_m, "note": n_m}
                save_json(DATA_FILE, data_planning); st.success("Mise à jour faite !"); st.rerun()

        with t2:
            st.subheader("Règles annuelles")
            c1, c2, c3 = st.columns(3)
            user_rec = c1.selectbox("Qui ?", MEMBRES_EQUIPE, key="rec1")
            day_rec = c2.selectbox("Chaque...", JOURS_FR[:6], key="rec2")
            stat_rec = c3.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"], key="rec3")
            if st.button("Appliquer à toute l'année"):
                day_idx = JOURS_FR.index(day_rec)
                curr = date(2026, 1, 1)
                while curr.year == 2026:
                    if curr.weekday() == day_idx:
                        ds = curr.strftime("%Y-%m-%d")
                        if ds not in data_planning: data_planning[ds] = {}
                        data_planning[ds][user_rec] = {"statut": stat_rec, "note": ""}
                    curr += timedelta(days=1)
                save_json(DATA_FILE, data_planning); st.success("Règle appliquée !"); st.rerun()

        with t3:
            if not data_conges: st.write("Aucune demande.")
            else:
                for k, v in list(data_conges.items()):
                    with st.expander(f"Demande de {v['nom']}"):
                        st.write(f"Du {v['debut']} au {v['fin']}"); st.write(f"Motif: {v['motif']}")
                        if st.button(f"Supprimer {k}"): del data_conges[k]; save_json(CONGES_FILE, data_conges); st.rerun()
