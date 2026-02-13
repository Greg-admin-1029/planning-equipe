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
# STYLE CSS (Léo)
# ==========================================
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    thead tr th {
        background-color: #2c3e50 !important;
        color: white !important;
        font-weight: bold !important;
    }
    .stDataFrame td { text-align: center !important; font-size: 18px !important; }
    
    /* Style pour le récapitulatif dans la barre latérale */
    .recap-container {
        padding: 10px;
        border-radius: 5px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
        border-left: 5px solid #2c3e50;
    }
    .recap-name { font-weight: bold; color: #2c3e50; margin-bottom: 2px; }
    .recap-stats { font-size: 14px; }
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

# ==========================================
# CALCUL DES STATS (Marc)
# ==========================================
def get_stats():
    stats = {m: {"fermetures": 0, "vacances": 0, "absences": 0} for m in MEMBRES_EQUIPE}
    for date_key, membres in data_planning.items():
        for m, statut in membres.items():
            if m in stats:
                if statut == "Fermeture": stats[m]["fermetures"] += 1
                elif statut == "Vacances": stats[m]["vacances"] += 1
                elif statut == "Absent": stats[m]["absences"] += 1
    return stats

# ==========================================
# NAVIGATION ET RECAP (Barre latérale)
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
                🔑 {s['fermetures']} | ✈️ {s['vacances']} | 🚫 {s['absences']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 1 : PLANNING
# ==========================================
if page == "📅 Voir le Planning":
    st.header("Planning de l'équipe 2026")
    mois_sel = st.selectbox("Sélectionner le mois", range(1, 13), format_func=lambda x: MOIS_FR[x-1])
    
    start_date = date(2026, mois_sel, 1)
    if mois_sel == 12: end_date = date(2027, 1, 1) - timedelta(days=1)
    else: end_date = date(2026, mois_sel + 1, 1) - timedelta(days=1)

    jours = []
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 6: jours.append(curr)
        curr += timedelta(days=1)

    df = pd.DataFrame(index=[f"{JOURS_FR[d.weekday()]} {d.day}" for d in jours], columns=MEMBRES_EQUIPE)

    for d in jours:
        d_str = d.strftime("%Y-%m-%d")
        row_label = f"{JOURS_FR[d.weekday()]} {d.day}"
        for m in MEMBRES_EQUIPE:
            statut = data_planning.get(d_str, {}).get(m, "Présent")
            icones = {"Présent": "✅", "Télétravail": "🏠", "Absent": "🚫", "Fermeture": "🔑", "Vacances": "✈️"}
            df.at[row_label, m] = icones.get(statut, "✅")

    # Affichage avec colonnes resserrées (Small)
    st.dataframe(
        df, 
        use_container_width=True, 
        height=700,
        column_config={col: st.column_config.TextColumn(width="small") for col in MEMBRES_EQUIPE}
    )
    st.info("Légende : ✅ Présent | 🏠 Télétravail | 🚫 Absent | 🔑 Fermeture | ✈️ Vacances")

# ==========================================
# PAGE 2 : DEMANDE DE CONGÉS
# ==========================================
elif page == "✉️ Demande de Congés":
    st.header("Soumettre une demande")
    with st.form("form_conges"):
        nom = st.selectbox("Votre nom", MEMBRES_EQUIPE)
        debut = st.date_input("Du", date.today())
        fin = st.date_input("Au", date.today())
        motif = st.text_area("Motif (optionnel)")
        if st.form_submit_button("Envoyer la demande"):
            key = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_conges[key] = {"nom": nom, "debut": str(debut), "fin": str(fin), "motif": motif, "statut": "En attente"}
            save_json(CONGES_FILE, data_conges)
            st.success("Demande envoyée au manager !")

# ==========================================
# PAGE 3 : MANAGER
# ==========================================
elif page == "🔒 Espace Manager":
    st.header("Administration")
    pwd = st.text_input("Mot de passe", type="password")
    
    if pwd == MANAGER_PASSWORD:
        tab1, tab2 = st.tabs(["Modifier Planning", "Gérer les Demandes"])
        
        with tab1:
            c1, c2 = st.columns(2)
            d_mod = c1.date_input("Jour à modifier", date(2026, 1, 1))
            u_mod = c1.selectbox("Collaborateur", MEMBRES_EQUIPE)
            s_mod = c2.selectbox("Nouveau Statut", ["Présent", "Télétravail", "Absent", "Fermeture", "Vacances"])
            if st.button("Valider la modification"):
                d_str = d_mod.strftime("%Y-%m-%d")
                if d_str not in data_planning: data_planning[d_str] = {}
                data_planning[d_str][u_mod] = s_mod
                save_json(DATA_FILE, data_planning)
                st.success("Planning mis à jour !")
                st.rerun()

        with tab2:
            st.subheader("Demandes reçues")
            if not data_conges:
                st.write("Aucune demande en attente.")
            else:
                for k, v in list(data_conges.items()):
                    st.write(f"**{v['nom']}** : du {v['debut']} au {v['fin']} ({v['motif']})")
                    if st.button(f"Supprimer la demande {k}"):
                        del data_conges[k]
                        save_json(CONGES_FILE, data_conges)
                        st.rerun()
