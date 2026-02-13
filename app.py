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
        for m, info in membres.items():
            statut = info["statut"] if isinstance(info, dict) else info
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
            if isinstance(info, dict):
                statut = info.get("statut", "Présent")
                note = info.get("note", "")
            else:
                statut = info
                note = ""

            if statut in ["Absent", "Vacances"]:
                count_present -= 1
            
            icones = {"Présent":"✅","Télétravail":"🏠","Absent":"🚫","Fermeture":"🔑","Vacances":"✈️"}
            emoj = icones.get(statut, "✅")
            df.at[row_label, m] = f"{note} {emoj}" if note else emoj
        
        df.at[row_label, "Total Présents"] = f"👥 {count_present}"

    st.dataframe(
        df, 
        use_container_width=True, 
        height=750,
        column_config={col: st.column_config.TextColumn(width="medium") for col in colonnes_tableau}
    )

# ==========================================
# PAGE 2 : CONGÉS (DEMANDE DE PÉRIODE)
# ==========================================
elif page == "✉️ Demande de Congés":
    st.header("Soumettre une demande de congés ou vacances")
    st.info("Sélectionnez votre nom et la période souhaitée. Votre demande sera examinée par le manager.")
    
    with st.form("form_conges"):
        c1, c2 = st.columns(2)
        nom = c1.selectbox("Votre nom", MEMBRES_EQUIPE)
        type_conge = c2.selectbox("Type de demande", ["Vacances ✈️", "Absence 🚫", "Télétravail 🏠"])
        
        d_deb = c1.date_input("Date de début", date.today())
        d_fin = c2.date_input("Date de fin", date.today())
        
        motif = st.text_area("Note / Motif (ex: Vacances d'été, Rendez-vous spécial...)")
        
        if st.form_submit_button("Envoyer la demande de période"):
            if d_deb <= d_fin:
                key = datetime.now().strftime("%Y%m%d_%H%M%S")
                data_conges[key] = {
                    "nom": nom,
                    "type": type_conge,
                    "debut": str(d_deb),
                    "fin": str(d_fin),
                    "motif": motif,
                    "date_demande": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                save_json(CONGES_FILE, data_conges)
                st.success(f"Demande envoyée pour la période du {d_deb.strftime('%d/%m/%Y')} au {d_fin.strftime('%d/%m/%Y')} !")
            else:
                st.error("Erreur : La date de fin doit être après la date de début.")

# ==========================================
# PAGE 3 : MANAGER
# ==========================================
elif page == "🔒 Espace Manager":
    st.header("Administration")
    if st.text_input("Mot de passe", type="password") == MANAGER_PASSWORD:
        t1, t2, t3 = st.tabs(["Modification Planning", "🔄 Actions Groupées", "✉️ Demandes reçues"])
        
        with t1:
            type_mod = st.radio("Type de modification", ["Un seul jour", "Une période (plusieurs jours)"], horizontal=True)
            col_a, col_b = st.columns(2)
            u_m = col_a.selectbox("Collaborateur concerné", MEMBRES_EQUIPE)
            s_m = col_b.selectbox("Nouveau Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances"])
            n_m = col_b.text_input("Note / Précision")
            
            if type_mod == "Un seul jour":
                d_m = col_a.date_input("Choisir le jour", date(2026,1,1))
                dates_a_modifier = [d_m]
            else:
                d_debut = col_a.date_input("Date de début", date(2026,1,1))
                d_fin = col_a.date_input("Date de fin", date(2026,1,1))
                dates_a_modifier = []
                if d_debut <= d_fin:
                    curr = d_debut
                    while curr <= d_fin:
                        dates_a_modifier.append(curr)
                        curr += timedelta(days=1)

            if st.button("Enregistrer les modifications"):
                if dates_a_modifier:
                    for d in dates_a_modifier:
                        ds = d.strftime("%Y-%m-%d")
                        if ds not in data_planning: data_planning[ds] = {}
                        data_planning[ds][u_m] = {"statut": s_m, "note": n_m}
                    save_json(DATA_FILE, data_planning)
                    st.success("Mise à jour effectuée !")
                    st.rerun()

        with t2:
            st.subheader("Règles annuelles")
            c1, c2, c3 = st.columns(3)
            user_rec = c1.selectbox("Qui ?", MEMBRES_EQUIPE, key="rec1")
            day_rec = c2.selectbox("Chaque...", JOURS_FR[:6], key="rec2")
            stat_rec = c3.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances"], key="rec3")
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
            st.subheader("Boîte de réception des demandes")
            if not data_conges:
                st.write("Aucune demande en attente.")
            else:
                for k, v in list(data_conges.items()):
                    with st.expander(f"Demande de {v['nom']} - {v['type']}"):
                        st.write(f"**Période :** du {v['debut']} au {v['fin']}")
                        st.write(f"**Motif :** {v['motif']}")
                        st.write(f"*Envoyée le : {v.get('date_demande', 'Date inconnue')}*")
                        if st.button(f"Supprimer / Archiver la demande {k}"):
                            del data_conges[k]
                            save_json(CONGES_FILE, data_conges)
                            st.rerun()
