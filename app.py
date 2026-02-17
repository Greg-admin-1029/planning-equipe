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
# STYLE CSS AMÉLIORÉ (Léo)
# ==========================================
st.markdown("""
    <style>
    /* Style général du tableau */
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    
    /* En-tête du tableau */
    thead tr th { 
        background-color: #2c3e50 !important; 
        color: white !important; 
        font-weight: bold !important; 
        padding: 15px !important;
    }

    /* Alternance de couleurs pour les lignes */
    tbody tr:nth-child(even) { background-color: #f8f9fa; }
    
    /* Style des cellules */
    .stDataFrame td { 
        padding: 10px !important; 
        font-size: 16px !important; 
        border-bottom: 1px solid #eee !important;
    }

    /* Style pour le récapitulatif latéral */
    .recap-container {
        padding: 12px;
        border-radius: 8px;
        background-color: #ffffff;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
        border-left: 5px solid #2c3e50;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .recap-name { font-weight: bold; color: #1a252f; font-size: 15px; }
    .recap-stats { font-size: 13px; color: #34495e; }
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
    st.title("📅 Planning Pro")
    page = st.radio("Menu Principal", ["👀 Planning Mensuel", "✉️ Demande de Congés", "🔒 Administration"])
    st.markdown("---")
    st.subheader("📊 Cumul Annuel")
    current_stats = get_stats()
    for m in MEMBRES_EQUIPE:
        s = current_stats[m]
        st.markdown(f"""
        <div class="recap-container">
            <div class="recap-name">{m}</div>
            <div class="recap-stats">
                🔑 {s['fermetures']} Ferm. | ✈️ {s['vacances']} Vac.<br>
                🚫 {s['absences']} Abs. | 🛠️ {s['samedis']} Sam.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 1 : PLANNING
# ==========================================
if page == "👀 Planning Mensuel":
    st.header("Calendrier de l'équipe")
    
    mois_actuel = datetime.now().month
    default_index = (mois_actuel - 1) if datetime.now().year == 2026 else 0
    mois_sel = st.selectbox("Sélectionner le mois", range(1, 13), index=default_index, format_func=lambda x: MOIS_FR[x-1])
    
    start_date = date(2026, mois_sel, 1)
    if mois_sel == 12: end_date = date(2027, 1, 1) - timedelta(days=1)
    else: end_date = date(2026, mois_sel + 1, 1) - timedelta(days=1)

    jours = []
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 6: # On exclut les dimanches
            jours.append(curr)
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
        
        # Alerte visuelle si peu de monde
        alerte = "🚨" if count_present < 3 else "👥"
        df.at[row_label, "Total Présents"] = f"{alerte} {count_present}"

    # Affichage avec style amélioré
    st.dataframe(
        df, 
        use_container_width=True, 
        height=750,
        column_config={
            col: st.column_config.TextColumn(width="medium") for col in colonnes_tableau
        }
    )
    
    st.write("---")
    st.caption("💡 Astuce : Les lignes grisées vous aident à suivre la semaine. Les dimanches sont masqués.")

# ==========================================
# PAGES 2 & 3 (Restent identiques mais intégrées)
# ==========================================
elif page == "✉️ Demande de Congés":
    st.header("Nouvelle demande")
    with st.form("f"):
        nom = st.selectbox("Qui êtes-vous ?", MEMBRES_EQUIPE)
        type_c = st.selectbox("Type", ["Vacances ✈️", "Absence 🚫", "Télétravail 🏠"])
        d1 = st.date_input("Du"); d2 = st.date_input("Au")
        motif = st.text_area("Précisions")
        if st.form_submit_button("Envoyer"):
            if d1 <= d2:
                data_conges[datetime.now().strftime("%f")] = {"nom":nom,"type":type_c,"debut":str(d1),"fin":str(d2),"motif":motif}
                save_json(CONGES_FILE, data_conges); st.success("Demande enregistrée !")
            else: st.error("Dates incohérentes.")

elif page == "🔒 Administration":
    st.header("Gestion Manager")
    if st.text_input("Mot de passe", type="password") == MANAGER_PASSWORD:
        t1, t2, t3 = st.tabs(["✍️ Modifier le Planning", "🔄 Actions Groupées", "📥 Demandes"])
        with t1:
            type_mod = st.radio("Mode", ["Jour unique", "Période"], horizontal=True)
            u_m = st.selectbox("Collaborateur", MEMBRES_EQUIPE)
            s_m = st.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"])
            n_m = st.text_input("Note")
            if type_mod == "Jour unique":
                dates = [st.date_input("Jour", date(2026,1,1))]
            else:
                d1 = st.date_input("Début", date(2026,1,1)); d2 = st.date_input("Fin", date(2026,1,1))
                dates = [d1 + timedelta(days=x) for x in range((d2-d1).days + 1)]
            if st.button("Valider modification"):
                for d in dates:
                    ds = d.strftime("%Y-%m-%d")
                    if ds not in data_planning: data_planning[ds] = {}
                    data_planning[ds][u_m] = {"statut":s_m, "note":n_m}
                save_json(DATA_FILE, data_planning); st.success("Planning mis à jour !"); st.rerun()
        
        with t2:
            st.subheader("Règles récurrentes")
            c1, c2, c3 = st.columns(3)
            user_r = c1.selectbox("Pour qui ?", MEMBRES_EQUIPE, key="r1")
            day_r = c2.selectbox("Chaque...", JOURS_FR[:6], key="r2")
            stat_r = c3.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"], key="r3")
            if st.button("Appliquer sur toute l'année"):
                idx = JOURS_FR.index(day_r)
                curr = date(2026,1,1)
                while curr.year == 2026:
                    if curr.weekday() == idx:
                        ds = curr.strftime("%Y-%m-%d")
                        if ds not in data_planning: data_planning[ds] = {}
                        data_planning[ds][user_r] = {"statut":stat_r, "note":""}
                    curr += timedelta(days=1)
                save_json(DATA_FILE, data_planning); st.success("Règle appliquée !"); st.rerun()

        with t3:
            for k, v in list(data_conges.items()):
                with st.expander(f"Demande de {v['nom']}"):
                    st.write(f"**Période :** {v['debut']} au {v['fin']}\n\n**Motif :** {v['motif']}")
                    if st.button(f"Supprimer la demande {k}"):
                        del data_conges[k]; save_json(CONGES_FILE, data_conges); st.rerun()
