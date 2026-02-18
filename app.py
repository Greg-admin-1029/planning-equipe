import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import smtplib
from email.mime.text import MIMEText

# ==========================================
# 1. CONNEXION (MISE EN CACHE POUR ÉVITER L'ERREUR 429)
# ==========================================
MEMBRES_EQUIPE = ["William", "Ritchie", "Emmanuel", "Grégory", "Kyle"]
MANAGER_PASSWORD = "admin"
JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

@st.cache_resource
def get_gsheet_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds).open("Planning_Data")

try:
    sheet = get_gsheet_connection()
    planning_sheet = sheet.worksheet("planning")
    conges_sheet = sheet.worksheet("conges")
except Exception as e:
    st.error(f"Erreur Google Sheets : {e}")
    st.stop()

# ==========================================
# 2. CHARGEMENT OPTIMISÉ DES DONNÉES
# ==========================================
def load_all_data():
    # On lit tout d'un coup pour économiser le quota API
    records = planning_sheet.get_all_records()
    plan_dict = {}
    for r in records:
        d_str = str(r['date'])
        if d_str not in plan_dict: plan_dict[d_str] = {}
        plan_dict[d_str][r['membre']] = {"statut": r['statut'], "note": r['note']}
    return plan_dict

data_planning = load_all_data()

# ==========================================
# 3. INTERFACE
# ==========================================
st.set_page_config(page_title="Planning Équipe", layout="wide")
page = st.sidebar.radio("Navigation", ["📅 Planning", "✉️ Congés", "🔒 Manager"])

# ==========================================
# 4. PLANNING (FORMAT FR & ICÔNES)
# ==========================================
if page == "📅 Planning":
    st.header("Planning Équipe 2026")
    mois_sel = st.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: MOIS_FR[x-1])
    
    start_date = date(2026, mois_sel, 1)
    end_date = (date(2026, mois_sel+1, 1) if mois_sel < 12 else date(2027, 1, 1)) - timedelta(days=1)
    
    jours_sem = {}
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 6: # Pas de dimanche
            sn = curr.isocalendar()[1]
            jours_sem.setdefault(sn, []).append(curr)
        curr += timedelta(days=1)

    icones = {"Présent":"✅","Télétravail":"🏠","Absent":"🚫","Fermeture":"🔑","Vacances":"✈️","Travail Samedi":"🛠️"}

    for num, jours in jours_sem.items():
        st.markdown(f'<div style="background-color:#1e1e1e;color:white;padding:10px;border-radius:5px;margin-top:20px;">Semaine {num}</div>', unsafe_allow_html=True)
        indices = [f"{JOURS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}" for d in jours]
        df = pd.DataFrame(index=indices, columns=MEMBRES_EQUIPE)
        
        for d in jours:
            ds = d.strftime("%Y-%m-%d")
            row_label = f"{JOURS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}"
            for m in MEMBRES_EQUIPE:
                info = data_planning.get(ds, {}).get(m, {"statut": "Présent", "note": ""})
                statut = info["statut"]
                note = info["note"]
                df.at[row_label, m] = f"{note} {icones.get(statut, '✅')}" if note else icones.get(statut, "✅")
        st.table(df)

# ==========================================
# 5. CONGÉS (FORMAT DATE FR)
# ==========================================
elif page == "✉️ Congés":
    st.header("Demande de Congés")
    with st.form("f_conges"):
        nom = st.selectbox("Collaborateur", MEMBRES_EQUIPE)
        type_c = st.selectbox("Type", ["Vacances ✈️", "Absence 🚫", "Télétravail 🏠"])
        d1 = st.date_input("Du", format="DD/MM/YYYY")
        d2 = st.date_input("Au", format="DD/MM/YYYY")
        mot = st.text_area("Motif")
        if st.form_submit_button("Envoyer"):
            conges_sheet.append_row([nom, type_c, str(d1), str(d2), mot, datetime.now().strftime("%d/%m/%Y %H:%M")])
            st.success("Demande envoyée !")

# ==========================================
# 6. MANAGER (PÉRIODES, AUTO, VALIDATION)
# ==========================================
elif page == "🔒 Manager":
    if st.text_input("Mot de passe", type="password") == MANAGER_PASSWORD:
        t_per, t_auto, t_val = st.tabs(["📅 Périodes", "⚙️ Automatisations", "📥 Validation"])

        with t_per:
            c1, c2 = st.columns(2)
            u = c1.selectbox("Qui", MEMBRES_EQUIPE, key="u_per")
            s = c1.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"])
            d_s = c2.date_input("Début", format="DD/MM/YYYY", key="ds_per")
            d_e = c2.date_input("Fin", format="DD/MM/YYYY", key="de_per")
            note = st.text_input("Note")
            if st.button("Enregistrer la période"):
                rows = [[(d_s + timedelta(days=x)).strftime("%Y-%m-%d"), u, s, note] for x in range((d_e-d_s).days + 1)]
                planning_sheet.append_rows(rows)
                st.success("Planning mis à jour !"); st.rerun()

        with t_auto:
            st.write("Régler un jour récurrent pour toute l'année 2026")
            col_q, col_j, col_s = st.columns(3)
            a_nom = col_q.selectbox("Qui", MEMBRES_EQUIPE, key="a_n")
            a_jour = col_j.selectbox("Jour", JOURS_FR, key="a_j")
            a_stat = col_s.selectbox("Statut", ["Télétravail", "Fermeture", "Présent"], key="a_s")
            if st.button("Générer l'année"):
                all_d = []
                curr = date(2026, 1, 1)
                while curr.year == 2026:
                    if JOURS_FR[curr.weekday()] == a_jour:
                        all_d.append([curr.strftime("%Y-%m-%d"), a_nom, a_stat])
                    curr += timedelta(days=1)
                planning_sheet.append_rows(all_d)
                st.success("Automatisations ajoutées !"); st.rerun()

        with t_val:
            demandes = conges_sheet.get_all_records()
            for i, d in enumerate(demandes):
                with st.expander(f"Demande : {d['nom']} ({d['type']})"):
                    st.write(f"Dates: {d['debut']} au {d['fin']}")
                    if st.button("✅ Valider", key=f"v{i}"):
                        start = datetime.strptime(d['debut'], "%Y-%m-%d").date()
                        end = datetime.strptime(d['fin'], "%Y-%m-%d").date()
                        st_net = d['type'].split(' ')[0]
                        rows = [[(start + timedelta(days=x)).strftime("%Y-%m-%d"), d['nom'], st_net, "Validé"] for x in range((end-start).days + 1)]
                        planning_sheet.append_rows(rows)
                        conges_sheet.delete_rows(i + 2)
                        st.rerun()
