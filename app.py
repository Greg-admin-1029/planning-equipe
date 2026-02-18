import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import smtplib
from email.mime.text import MIMEText

# ==========================================
# CONNEXION GOOGLE SHEETS
# ==========================================
def get_gsheet_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # On utilise les secrets configurés dans le dashboard Streamlit
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
# CONFIGURATION & STYLE
# ==========================================
MEMBRES_EQUIPE = ["William", "Ritchie", "Emmanuel", "Grégory", "Kyle"]
MANAGER_PASSWORD = "admin"
JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

st.set_page_config(page_title="Planning 2026", layout="wide")

# (Style CSS identique à la V15 - Dark Mode & Samedi Gris)
st.markdown("""
    <style>
    .recap-container { padding: 10px; border-radius: 5px; background-color: #f0f2f6; margin-bottom: 10px; border-left: 5px solid #2c3e50; color: #000000 !important; }
    .recap-name { font-weight: bold; color: #000000 !important; }
    .recap-stats { font-size: 13px; color: #000000 !important; }
    .week-header { background-color: #1e1e1e; color: #ffffff; padding: 10px 15px; border-radius: 5px; margin-top: 25px; margin-bottom: 5px; font-weight: bold; font-size: 18px; border: 1px solid #333; }
    table { width: 100%; border-collapse: collapse; background-color: #0e1117 !important; color: white !important; }
    th { background-color: #1e1e1e !important; color: white !important; border: 1px solid #333 !important; }
    td { border: 1px solid #333 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FONCTIONS DE DONNÉES
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
        sujet = f"🚨 Nouvelle demande : {nom}"
        corps = f"Collaborateur: {nom}\nType: {type_c}\nDu {debut} au {fin}\nMotif: {motif}"
        msg = MIMEText(corps)
        msg['Subject'], msg['From'], msg['To'] = sujet, conf["emetteur"], conf["destinataire"]
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(conf["emetteur"], conf["mot_de_passe"])
            server.send_message(msg)
        return True
    except: return False

# Chargement initial
data_planning = load_planning_data()

# ==========================================
# NAVIGATION & PAGES
# ==========================================
with st.sidebar:
    st.title("Menu")
    page = st.radio("Navigation", ["📅 Planning", "✉️ Congés", "🔒 Manager"])
    st.markdown("---")
    current_stats = get_stats(data_planning)
    for m in MEMBRES_EQUIPE:
        s = current_stats[m]
        st.markdown(f'<div class="recap-container"><div class="recap-name">{m}</div><div class="recap-stats">🔑 {s["fermetures"]} | ✈️ {s["vacances"]} | 🚫 {s["absences"]} | 🛠️ {s["samedis"]}</div></div>', unsafe_allow_html=True)

if page == "📅 Planning": # <-- C'est ici
    st.header("Planning Équipe 2026")
    mois_actuel = datetime.now().month
    mois_sel = st.selectbox("Mois", range(1, 13), index=mois_sel_index, format_func=lambda x: MOIS_FR[x-1])
    
    # ... (code de calcul des dates) ...

    for num, jours in jours_sem.items():
        st.markdown(f'<div class="week-header">Semaine {num}</div>', unsafe_allow_html=True)
        
        # --- MODIFICATION ICI : Format de date 18/02/2026 ---
        indices_dates = [f"{JOURS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}" for d in jours]
        df = pd.DataFrame(index=indices_dates, columns=MEMBRES_EQUIPE + ["Total"])
        
        for d in jours:
            ds = d.strftime("%Y-%m-%d")
            # --- MODIFICATION ICI : Format de date pour la ligne ---
            row_label = f"{JOURS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}"
            pres = len(MEMBRES_EQUIPE)
            
            for m in MEMBRES_EQUIPE:
                # On récupère les infos depuis Google Sheets
                val = data_planning.get(ds, {}).get(m, {"statut": "Présent", "note": ""})
                statut = val["statut"]
                note = val["note"]
                
                if statut in ["Absent", "Vacances"]: 
                    pres -= 1
                
                # --- MODIFICATION ICI : Dictionnaire d'icônes ---
                icones = {
                    "Présent": "✅",
                    "Télétravail": "🏠",
                    "Absent": "🚫",
                    "Fermeture": "🔑",
                    "Vacances": "✈️",
                    "Travail Samedi": "🛠️"
                }
                
                # Affichage : Icone + Note (si note existe)
                icone_a_afficher = icones.get(statut, "✅")
                df.at[row_label, m] = f"{note} {icone_a_afficher}" if note else icone_a_afficher
            
            df.at[row_label, "Total"] = f"{'🚨' if pres < 3 else '👥'} {pres}"
        
        st.table(df.style.apply(lambda r: ['background-color: #333; color: white; font-weight: bold']*len(r) if "Samedi" in r.name else ['background-color: #0e1117; color: white']*len(r), axis=1))

elif page == "✉️ Congés":
    st.header("Demande de Congés")
    with st.form("f_conges"):
        nom = st.selectbox("Nom", MEMBRES_EQUIPE)
        type_c = st.selectbox("Type", ["Vacances ✈️", "Absence 🚫", "Télétravail 🏠"])
        d1, d2, mot = st.date_input("Du"), st.date_input("Au"), st.text_area("Motif")
        if st.form_submit_button("Envoyer"):
            conges_sheet.append_row([nom, type_c, str(d1), str(d2), mot, datetime.now().strftime("%Y-%m-%d %H:%M")])
            envoyer_email_notification(nom, type_c, str(d1), str(d2), mot)
            st.success("Demande enregistrée dans Google Sheets et Manager notifié !")

elif page == "🔒 Manager":
    if st.text_input("Mot de passe", type="password") == MANAGER_PASSWORD:
        t1, t2 = st.tabs(["Modification Manuelle", "📥 Validation des Demandes"])
        
        with t1:
            # (Votre code actuel de modification manuelle reste ici)
            u_m = st.selectbox("Qui", MEMBRES_EQUIPE)
            s_m = st.selectbox("Statut", ["Présent","Télétravail","Absent","Fermeture","Vacances","Travail Samedi"])
            n_m = st.text_input("Note")
            d_a, d_b = st.date_input("Début"), st.date_input("Fin")
            if st.button("Enregistrer"):
                new_rows = []
                for d in [d_a + timedelta(days=x) for x in range((d_b-d_a).days + 1)]:
                    new_rows.append([d.strftime("%Y-%m-%d"), u_m, s_m, n_m])
                planning_sheet.append_rows(new_rows)
                st.success("Planning mis à jour !"); st.rerun()

        with t2:
            st.subheader("Demandes de congés en attente")
            demandes = conges_sheet.get_all_records()
            
            if not demandes:
                st.info("Aucune demande en attente.")
            
            for i, d in enumerate(demandes):
                # Formatage de l'affichage des dates pour le manager
                try:
                    # On transforme le format YYYY-MM-DD en DD/MM/YYYY pour l'affichage
                    d_debut_fr = datetime.strptime(d['debut'], "%Y-%m-%d").strftime("%d/%m/%Y")
                    d_fin_fr = datetime.strptime(d['fin'], "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    d_debut_fr, d_fin_fr = d['debut'], d['fin']

                with st.expander(f"📌 {d['nom']} - {d['type']} (du {d_debut_fr} au {d_fin_fr})", expanded=True):
                    st.write(f"**Motif :** {d['motif']}")
                    
                    col1, col2 = st.columns([1, 1])
                    
                    if col1.button("✅ Accepter", key=f"acc_{i}"):
                        start = datetime.strptime(d['debut'], "%Y-%m-%d").date()
                        end = datetime.strptime(d['fin'], "%Y-%m-%d").date()
                        
                        # Extraction du statut propre (ex: "Vacances" au lieu de "Vacances ✈️")
                        statut_brut = d['type'].split(' ')[0] 
                        
                        new_planning_rows = []
                        current_d = start
                        while current_d <= end:
                            # IMPORTANT : On enregistre le statut demandé pour que l'icône change !
                            new_planning_rows.append([current_d.strftime("%Y-%m-%d"), d['nom'], statut_brut, "Validé"])
                            current_d += timedelta(days=1)
                        
                        planning_sheet.append_rows(new_planning_rows)
                        conges_sheet.delete_rows(i + 2)
                        st.success(f"Le calendrier a été mis à jour pour {d['nom']} en mode {statut_brut} !")
                        st.rerun()
                    
                    if col2.button("❌ Refuser", key=f"ref_{i}"):
                        conges_sheet.delete_rows(i + 2)
                        st.rerun()
