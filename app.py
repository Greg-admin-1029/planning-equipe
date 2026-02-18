import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import smtplib
from email.mime.text import MIMEText

# ==========================================
# 1. CONNEXION & CONFIG
# ==========================================
MEMBRES_EQUIPE = ["William", "Ritchie", "Emmanuel", "Grégory", "Kyle"]
MANAGER_PASSWORD = "admin"
JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

def get_gsheet_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Planning_Data")

try:
    sheet = get_gsheet_connection()
    planning_sheet = sheet.worksheet("planning")
    conges_sheet = sheet.worksheet("conges")
except Exception as e:
    st.error(f"Erreur Google Sheets : {e}")
    st.stop()

# ==========================================
# 2. FONCTIONS DE DONNÉES
# ==========================================
def load_planning_data():
    records = planning_sheet.get_all_records()
    plan_dict = {}
    for r in records:
        d = str(r['date'])
        if d not in plan_dict: plan_dict[d] = {}
        plan_dict[d][r['membre']] = {"statut": r['statut'], "note": r['note']}
    return plan_dict

data_planning = load_planning_data()

# ==========================================
# 3. INTERFACE & NAVIGATION
# ==========================================
st.set_page_config(page_title="Planning Équipe", layout="wide")
with st.sidebar:
    st.title("Menu")
    page = st.radio("Navigation", ["📅 Planning", "✉️ Congés", "🔒 Manager"])

# ==========================================
# 5. PAGE PLANNING (AFFICHAGE FR)
# ==========================================
if page == "📅 Planning":
    st.header("Planning Équipe 2026")
    mois_sel = st.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: MOIS_FR[x-1])
    
    start_date = date(2026, mois_sel, 1)
    end_date = (date(2026, mois_sel+1, 1) if mois_sel < 12 else date(2027, 1, 1)) - timedelta(days=1)
    
    jours_sem = {}
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 6:
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
                val = data_planning.get(ds, {}).get(m, {"statut": "Présent", "note": ""})
                df.at[row_label, m] = f"{val['note']} {icones.get(val['statut'], '✅')}" if val['note'] else icones.get(val['statut'], "✅")
        
        st.table(df)

# ==========================================
# 6. PAGE CONGÉS
# ==========================================
elif page == "✉️ Congés":
    st.header("Demande de Congés")
    with st.form("f_conges"):
        nom = st.selectbox("Collaborateur", MEMBRES_EQUIPE)
        type_c = st.selectbox("Type", ["Vacances ✈️", "Absence 🚫", "Télétravail 🏠"])
        d1 = st.date_input("Du", format="DD/MM/YYYY")
        d2 = st.date_input("Au", format="DD/MM/YYYY")
        mot = st.text_area("Motif")
        if st.form_submit_button("Envoyer la demande"):
            conges_sheet.append_row([nom, type_c, str(d1), str(d2), mot, datetime.now().strftime("%d/%m/%Y %H:%M")])
            st.success("Demande enregistrée !")

# ==========================================
# 7. PAGE MANAGER (RETOUR DES FONCTIONS)
# ==========================================
elif page == "🔒 Manager":
    if st.text_input("Mot de passe", type="password") == MANAGER_PASSWORD:
        tab_period, tab_auto, tab_valid = st.tabs(["📅 Par Période", "⚙️ Automatisations", "📥 Validation"])

        # --- ONGLET 1 : MODIFICATION PAR PÉRIODE ---
        with tab_period:
            st.subheader("Modifier une période spécifique")
            col1, col2 = st.columns(2)
            with col1:
                u_m = st.selectbox("Collaborateur", MEMBRES_EQUIPE, key="u1")
                s_m = st.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"], key="s1")
            with col2:
                d_debut = st.date_input("Date de début", format="DD/MM/YYYY", key="d1")
                d_fin = st.date_input("Date de fin", format="DD/MM/YYYY", key="d2")
            
            n_m = st.text_input("Note particulière (ex: 'Rdv médical')", key="n1")
            
            if st.button("Appliquer à la période"):
                new_rows = []
                delta = (d_fin - d_debut).days
                for i in range(delta + 1):
                    jour = d_debut + timedelta(days=i)
                    new_rows.append([jour.strftime("%Y-%m-%d"), u_m, s_m, n_m])
                planning_sheet.append_rows(new_rows)
                st.success(f"Période mise à jour pour {u_m} !")
                st.rerun()

        # --- ONGLET 2 : AUTOMATISATIONS (Télétravail/Fermeture) ---
        with tab_auto:
            st.subheader("Règles hebdomadaires (Toute l'année)")
            st.info("Exemple : Ritchie en Télétravail tous les Mardis.")
            
            c1, c2, c3 = st.columns(3)
            with c1: auto_nom = st.selectbox("Qui", MEMBRES_EQUIPE)
            with c2: auto_jour = st.selectbox("Quel jour", JOURS_FR)
            with c3: auto_statut = st.selectbox("Statut récurrent", ["Télétravail", "Fermeture", "Présent"])
            
            if st.button("Générer pour l'année 2026"):
                all_dates = []
                curr = date(2026, 1, 1)
                while curr.year == 2026:
                    if JOURS_FR[curr.weekday()] == auto_jour:
                        all_dates.append([curr.strftime("%Y-%m-%d"), auto_nom, auto_statut, "Récurrent"])
                    curr += timedelta(days=1)
                planning_sheet.append_rows(all_dates)
                st.success(f"C'est fait ! {auto_nom} est en {auto_statut} tous les {auto_jour}s.")

        # --- ONGLET 3 : VALIDATION DES DEMANDES ---
        with tab_valid:
            demandes = conges_sheet.get_all_records()
            if not demandes: st.info("Aucune demande en attente.")
            for i, d in enumerate(demandes):
                with st.expander(f"Demande de {d['nom']} ({d['type']})"):
                    st.write(f"Du {d['debut']} au {d['fin']} - Motif: {d['motif']}")
                    col_a, col_r = st.columns(2)
                    if col_a.button("✅ Accepter", key=f"v_{i}"):
                        # Conversion et injection auto
                        start = datetime.strptime(d['debut'], "%Y-%m-%d").date()
                        end = datetime.strptime(d['fin'], "%Y-%m-%d").date()
                        statut = d['type'].split(' ')[0]
                        rows = [[(start + timedelta(days=x)).strftime("%Y-%m-%d"), d['nom'], statut, "Validé"] for x in range((end-start).days+1)]
                        planning_sheet.append_rows(rows)
                        conges_sheet.delete_rows(i + 2)
                        st.rerun()
                    if col_r.button("❌ Refuser", key=f"ref_{i}"):
                        conges_sheet.delete_rows(i + 2)
                        st.rerun()
