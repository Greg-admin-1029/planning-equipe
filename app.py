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
    .recap-container {
        padding: 10px; border-radius: 5px; background-color: #f0f2f6;
        margin-bottom: 10px; border-left: 5px solid #2c3e50; color: #000000 !important;
    }
    .recap-name { font-weight: bold; color: #000000 !important; }
    .recap-stats { font-size: 13px; color: #000000 !important; }
    .week-header {
        background-color: #2c3e50; color: white; padding: 8px 15px;
        border-radius: 5px; margin-top: 25px; margin-bottom: 5px; font-weight: bold;
        font-size: 18px;
    }
    /* Forcer le style des tables Streamlit */
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #f8f9fa !important; color: #2c3e50 !important; }
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
                🔑 Ferm. : {s['fermetures']} | ✈️ Vac. : {s['vacances']}<br>
                🚫 Abs. : {s['absences']} | 🛠️ Sam. : {s['samedis']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 1 : PLANNING PAR SEMAINES
# ==========================================
if page == "📅 Voir le Planning":
    st.header("Planning de l'équipe 2026")
    
    mois_actuel = datetime.now().month
    default_index = (mois_actuel - 1) if datetime.now().year == 2026 else 0
    mois_sel = st.selectbox("Mois", range(1, 13), index=default_index, format_func=lambda x: MOIS_FR[x-1])
    
    start_date = date(2026, mois_sel, 1)
    if mois_sel == 12: end_date = date(2027, 1, 1) - timedelta(days=1)
    else: end_date = date(2026, mois_sel + 1, 1) - timedelta(days=1)

    jours_par_semaine = {}
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 6: # Lundi à Samedi
            semaine_num = curr.isocalendar()[1]
            if semaine_num not in jours_par_semaine:
                jours_par_semaine[semaine_num] = []
            jours_par_semaine[semaine_num].append(curr)
        curr += timedelta(days=1)

    for num, jours in jours_par_semaine.items():
        st.markdown(f'<div class="week-header">Semaine {num}</div>', unsafe_allow_html=True)
        
        colonnes = MEMBRES_EQUIPE + ["Total Présents"]
        indices = [f"{JOURS_FR[d.weekday()]} {d.day}" for d in jours]
        df = pd.DataFrame(index=indices, columns=colonnes)

        for d in jours:
            d_str = d.strftime("%Y-%m-%d")
            row_label = f"{JOURS_FR[d.weekday()]} {d.day}"
            count_present = len(MEMBRES_EQUIPE)
            
            for m in MEMBRES_EQUIPE:
                info = data_planning.get(d_str, {}).get(m, "Présent")
                statut = info.get("statut", "Présent") if isinstance(info, dict) else info
                note = info.get("note", "") if isinstance(info, dict) else ""
                if statut in ["Absent", "Vacances"]: count_present -= 1
                
                icones = {"Présent":"✅","Télétravail":"🏠","Absent":"🚫","Fermeture":"🔑","Vacances":"✈️","Travail Samedi":"🛠️"}
                df.at[row_label, m] = f"{note} {icones.get(statut, '✅')}" if note else icones.get(statut, "✅")
            
            alerte = "🚨" if count_present < 3 else "👥"
            df.at[row_label, "Total Présents"] = f"{alerte} {count_present}"

        # --- LOGIQUE DE COULEUR (Léo) ---
        def highlight_days(row):
            if "Samedi" in row.name:
                # Gris foncé avec texte blanc pour le Samedi
                return ['background-color: #444444; color: white; font-weight: bold'] * len(row)
            return [''] * len(row)

        st.table(df.style.apply(highlight_days, axis=1))

# ==========================================
# PAGE 2 & 3 (Inchangées)
# ==========================================
elif page == "✉️ Demande de Congés":
    st.header("Soumettre une demande")
    with st.form("f"):
        nom = st.selectbox("Nom", MEMBRES_EQUIPE); type_c = st.selectbox("Type", ["Vacances ✈️", "Absence 🚫", "Télétravail 🏠"])
        d1 = st.date_input("Du"); d2 = st.date_input("Au"); motif = st.text_area("Motif")
        if st.form_submit_button("Envoyer"):
            if d1 <= d2:
                data_conges[datetime.now().strftime("%f")] = {"nom":nom,"type":type_c,"debut":str(d1),"fin":str(d2),"motif":motif}
                save_json(CONGES_FILE, data_conges); st.success("Demande envoyée !")

elif page == "🔒 Espace Manager":
    st.header("Administration")
    if st.text_input("Mot de passe", type="password") == MANAGER_PASSWORD:
        t1, t2, t3 = st.tabs(["Modification", "Actions Groupées", "Demandes"])
        with t1:
            type_mod = st.radio("Mode", ["Jour unique", "Période"], horizontal=True)
            u_m = st.selectbox("Qui", MEMBRES_EQUIPE); s_m = st.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"]); n_m = st.text_input("Note")
            if type_mod == "Jour unique": dates = [st.date_input("Jour", date(2026,1,1))]
            else:
                d_a = st.date_input("Début", date(2026,1,1)); d_b = st.date_input("Fin", date(2026,1,1))
                dates = [d_a + timedelta(days=x) for x in range((d_b-d_a).days + 1)]
            if st.button("Enregistrer"):
                for d in dates:
                    ds = d.strftime("%Y-%m-%d")
                    if ds not in data_planning: data_planning[ds] = {}
                    data_planning[ds][u_m] = {"statut":s_m, "note":n_m}
                save_json(DATA_FILE, data_planning); st.success("Mis à jour !"); st.rerun()
        with t2:
            st.subheader("Règles annuelles")
            c1, c2, c3 = st.columns(3)
            user_r = c1.selectbox("Pour qui ?", MEMBRES_EQUIPE, key="r1"); day_r = c2.selectbox("Chaque...", JOURS_FR[:6], key="r2"); stat_r = c3.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"], key="r3")
            if st.button("Appliquer"):
                idx = JOURS_FR.index(day_r); curr = date(2026,1,1)
                while curr.year == 2026:
                    if curr.weekday() == idx:
                        ds = curr.strftime("%Y-%m-%d")
                        if ds not in data_planning: data_planning[ds] = {}
                        data_planning[ds][user_r] = {"statut":stat_r, "note":""}
                    curr += timedelta(days=1)
                save_json(DATA_FILE, data_planning); st.success("Fait !"); st.rerun()
        with t3:
            for k, v in list(data_conges.items()):
                with st.expander(f"Demande de {v['nom']}"):
                    st.write(f"Du {v['debut']} au {v['fin']}"); st.write(f"Motif: {v['motif']}")
                    if st.button(f"Supprimer {k}"): del data_conges[k]; save_json(CONGES_FILE, data_conges); st.rerun()
