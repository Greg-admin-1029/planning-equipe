import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import smtplib
from email.mime.text import MIMEText

# ==========================================
# 1. CONNEXION GOOGLE SHEETS & CONFIG
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
    st.error(f"Erreur de connexion Google Sheets : {e}")
    st.stop()

# ==========================================
# 2. STYLE CSS
# ==========================================
st.set_page_config(page_title="Planning 2026", layout="wide")
st.markdown("""
    <style>
    .recap-container { padding: 10px; border-radius: 5px; background-color: #f0f2f6; margin-bottom: 10px; border-left: 5px solid #2c3e50; color: #000; }
    .week-header { background-color: #1e1e1e; color: #ffffff; padding: 10px; border-radius: 5px; margin: 20px 0 5px 0; font-weight: bold; border: 1px solid #333; }
    table { width: 100%; background-color: #0e1117 !important; color: white !important; }
    th { background-color: #1e1e1e !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FONCTIONS UTILES
# ==========================================
def load_planning_data():
    records = planning_sheet.get_all_records()
    plan_dict = {}
    for r in records:
        d = str(r['date'])
        if d not in plan_dict: plan_dict[d] = {}
        plan_dict[d][r['membre']] = {"statut": r['statut'], "note": r['note']}
    return plan_dict

def get_stats(data):
    stats = {m: {"fermetures": 0, "vacances": 0, "absences": 0, "samedis": 0} for m in MEMBRES_EQUIPE}
    for d_key, membres in data.items():
        for m, info in membres.items():
            if m in stats:
                s = info["statut"]
                if s == "Fermeture": stats[m]["fermetures"] += 1
                elif s == "Vacances": stats[m]["vacances"] += 1
                elif s == "Absent": stats[m]["absences"] += 1
                elif s == "Travail Samedi": stats[m]["samedis"] += 1
    return stats

def envoyer_email_notification(nom, type_c, debut, fin, motif):
    try:
        conf = st.secrets["email"]
        msg = MIMEText(f"Demande de: {nom}\nType: {type_c}\nDu: {debut}\nAu: {fin}\nMotif: {motif}")
        msg['Subject'] = f"🚨 Nouvelle demande : {nom}"
        msg['From'], msg['To'] = conf["emetteur"], conf["destinataire"]
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(conf["emetteur"], conf["mot_de_passe"])
            server.send_message(msg)
    except: pass

data_planning = load_planning_data()

# ==========================================
# 4. NAVIGATION SIDEBAR
# ==========================================
with st.sidebar:
    st.title("Menu")
    page = st.radio("Navigation", ["📅 Planning", "✉️ Congés", "🔒 Manager"])
    st.markdown("---")
    current_stats = get_stats(data_planning)
    for m in MEMBRES_EQUIPE:
        s = current_stats[m]
        st.markdown(f'<div class="recap-container"><b>{m}</b><br><small>🔑 {s["fermetures"]} | ✈️ {s["vacances"]} | 🚫 {s["absences"]} | 🛠️ {s["samedis"]}</small></div>', unsafe_allow_html=True)

# ==========================================
# 5. PAGE PLANNING
# ==========================================
if page == "📅 Planning":
    st.header("Planning Équipe 2026")
    mois_sel = st.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: MOIS_FR[x-1])
    
    start_date = date(2026, mois_sel, 1)
    # Correction de la ligne 102 (la parenthèse manquante)
    if mois_sel < 12:
        end_date = date(2026, mois_sel + 1, 1) - timedelta(days=1)
    else:
        end_date = date(2027, 1, 1) - timedelta(days=1)
    
    jours_sem = {}
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 6:
            sn = curr.isocalendar()[1]
            jours_sem.setdefault(sn, []).append(curr)
        curr += timedelta(days=1)

    icones = {"Présent":"✅","Télétravail":"🏠","Absent":"🚫","Fermeture":"🔑","Vacances":"✈️","Travail Samedi":"🛠️"}

    for num, jours in jours_sem.items():
        st.markdown(f'<div class="week-header">Semaine {num}</div>', unsafe_allow_html=True)
        
        # Format de date JJ/MM/AAAA
        indices_dates = [f"{JOURS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}" for d in jours]
        df = pd.DataFrame(index=indices_dates, columns=MEMBRES_EQUIPE + ["Total"])
        
        for d in jours:
            ds = d.strftime("%Y-%m-%d")
            row_label = f"{JOURS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}"
            pres = len(MEMBRES_EQUIPE)
            
            for m in MEMBRES_EQUIPE:
                val = data_planning.get(ds, {}).get(m, {"statut": "Présent", "note": ""})
                if val["statut"] in ["Absent", "Vacances"]: pres -= 1
                
                icone = icones.get(val["statut"], "✅")
                df.at[row_label, m] = f"{val['note']} {icone}" if val['note'] else icone
            
            df.at[row_label, "Total"] = f"{'🚨' if pres < 3 else '👥'} {pres}"
        
        st.table(df.style.apply(lambda r: ['background-color: #333; color: white; font-weight: bold']*len(r) if "Samedi" in r.name else ['background-color: #0e1117; color: white']*len(r), axis=1))

# ==========================================
# 6. PAGE CONGÉS
# ==========================================
elif page == "✉️ Congés":
    st.header("Demande de Congés")
    with st.form("f_conges"):
        nom = st.selectbox("Nom", MEMBRES_EQUIPE)
        type_c = st.selectbox("Type", ["Vacances ✈️", "Absence 🚫", "Télétravail 🏠"])
        
        # Format de date européen ici
        d1 = st.date_input("Du", format="DD/MM/YYYY")
        d2 = st.date_input("Au", format="DD/MM/YYYY")
        
        mot = st.text_area("Motif")
        if st.form_submit_button("Envoyer"):
            conges_sheet.append_row([nom, type_c, str(d1), str(d2), mot, datetime.now().strftime("%d/%m/%Y %H:%M")])
            envoyer_email_notification(nom, type_c, str(d1), str(d2), mot)
            st.success("Demande enregistrée !")

# ==========================================
# 7. PAGE MANAGER
# ==========================================
elif page == "🔒 Manager":
    pwd = st.text_input("Mot de passe", type="password")
    if pwd == MANAGER_PASSWORD:
        t1, t2 = st.tabs(["Saisie Manuelle", "📥 Validation"])
        
        with t1:
            u_m = st.selectbox("Qui", MEMB
