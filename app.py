import streamlit as st # type: ignore
import pandas as pd # type: ignore
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection # type: ignore

# Configurazione della pagina con layout ottimizzato per mobile e desktop
st.set_page_config(
    page_title="Stefano Giardinaggio Team", 
    page_icon="🌱", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# STILE CSS DEFINITIVO: Risolve i conflitti di colore e migliora la leggibilità dei testi
st.markdown("""
    <style>
    /* Sfondo generale dell'applicazione leggermente grigio per far risaltare le card */
    .stApp {
        background-color: #f9fbf9 !important;
    }
    
    /* Forza i titoli principali e le scritte a essere visibili (Grigio scuro/Nero) */
    h1, h2, h3, p, span, label, [data-testid="stMetricLabel"] {
        color: #1b2e1b !important;
    }
    
    /* Configurazione per le card dei contatori in alto (KPI) */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #2e7d32 !important; /* Valori numerici in verde scuro */
    }
    
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        border: 1px solid #e1e8e1;
    }
    
    /* Card elegante per ogni singolo cliente sul campo */
    .client-card {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        border-left: 6px solid #2e7d32 !important;
    }
    
    /* Sistema i testi interni alla card dei clienti */
    .client-card h3 {
        margin: 0 0 8px 0 !important; 
        color: #111111 !important;
        font-weight: 600;
    }
    .client-card p {
        margin: 4px 0 !important; 
        color: #445544 !important;
        font-size: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Titoli dell'applicazione con tag espliciti per la formattazione
st.markdown("<h1 style='margin-bottom:0;'>🌱 Stefano Giardinaggio Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='margin-top:0; color:#556655 !important;'>Piattaforma Cloud di Gestione Interventi ed Equipaggio</p>", unsafe_allow_html=True)

# ==============================================================================
# INCOLLA QUI SOTTO IL TUO LINK DI GOOGLE FOGLI (IMPOSTATO COME EDITOR)
# ==============================================================================
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1LRKMpS-EXbvaB_DaGt33KFchRPpuqGxH3marxzwk330/edit?usp=sharing"

# Connessione nativa al Foglio Google tramite i Secrets di Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

# Carichiamo i dati aggiornati in tempo reale dal cloud
try:
    df = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
    df['Prossimo Taglio'] = pd.to_datetime(df['Prossimo Taglio']).dt.date
    df['Importo'] = df['Importo'].astype(float)
    df['Frequenza'] = df['Frequenza'].astype(int)
    df['Note'] = df['Note'].fillna("")
except Exception as e:
    st.error("Errore di connessione al Database Cloud. Controlla il link nel codice o le credenziali nei Secrets.")
    st.stop()

# TEMPO REALE: Prende l'ora e il giorno esatto del server internet corrente
oggi = datetime.now().date()

# Calcolo delle metriche per la dashboard superiore
clienti_oggi = df[df['Prossimo Taglio'] <= oggi]
lavori_totali_oggi = len(clienti_oggi)
incasso_previsto = clienti_oggi['Importo'].sum()

# Dashboard a 3 colonne pulita e visibile
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric(label="📋 Interventi di Oggi", value=f"{lavori_totali_oggi}")
with col_m2:
    st.metric(label="💰 Incasso Previsto", value=f"{incasso_previsto:.2f} €")
with col_m3:
    st.metric(label="📆 Data Odierna", value=oggi.strftime('%d/%m/%Y'))

st.write("---")

# Creazione dei pannelli di navigazione principali
tab_oggi, tab_admin = st.tabs(["📅 Agenda di Oggi", "📝 Pannello di Controllo Excel"])

# ---------------------------------------------------------
# PANNELLO 1: AGENDA DEL GIORNO (Interfaccia Mobile con Card)
# ---------------------------------------------------------
with tab_oggi:
    st.markdown(f"### 📋 Lista del Giorno: {oggi.strftime('%d/%m/%Y')}")
    
    if clienti_oggi.empty:
        st.success("🎉 Ottimo lavoro! Tutti gli interventi in scadenza oggi sono stati completati.")
    else:
        for index, row in clienti_oggi.iterrows():
            data_regolare = oggi + timedelta(days=int(row['Frequenza']))
            data_rimandato = oggi + timedelta(days=7)
            
            # Box visivo pulito per contenere le informazioni del cliente
            note_testo = row['Note'] if row['Note'] != "" else "Nessuna nota presente"
            st.markdown(f"""
            <div class="client-card">
                <h3>👤 {row['Nome']}</h3>
                <p>💵 <b>Prezzo:</b> {row['Importo']:.2f} € | ⏱️ <b>Frequenza:</b> ogni {row['Frequenza']} giorni</p>
                <p style='font-style: italic; color: #667766 !important;'>📝 <b>Note:</b> {note_testo}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Pulsanti di gestione posizionati in modo simmetrico sotto la card
            col_c, col_r = st.columns(2)
            with col_c:
                if st.button(f"🟢 Completato ({data_regolare.strftime('%d/%m')})", key=f"comp_{index}", use_container_width=True):
                    df.at[index, 'Prossimo Taglio'] = data_regolare
                    conn.update(spreadsheet=URL_FOGLIO, data=df)
                    st.toast(f"✅ Registrato: {row['Nome']}")
                    st.rerun()
            with col_r:
                if st.button(f"🔴 Rimanda (+7 gg)", key=f"rim_{index}", use_container_width=True):
                    df.at[index, 'Prossimo Taglio'] = data_rimandato
                    conn.update(spreadsheet=URL_FOGLIO, data=df)
                    st.toast(f"⚠️ Spostato di una settimana")
                    st.rerun()
            st.write("")

# ---------------------------------------------------------
# PANNELLO 2: INTERFACCIA EXCEL (Aggiungi, Modifica, Elimina)
# ---------------------------------------------------------
with tab_admin:
    st.markdown("### ⚙️ Modifica Libera del Database")
    st.markdown("""
    * **Modificare:** Fai doppio clic su una cella qualsiasi per aggiornare i dati.
    * **Aggiungere:** Vai in fondo alla tabella e compila la riga vuota.
    * **Eliminare:** Seleziona la riga dalla casellina a sinistra e premi *Canc* o *Delete* sulla tastiera.
    """)
    
    # Editor avanzato integrato a tutta larghezza
    df_modificato = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nome": st.column_config.TextColumn("Nome Cliente", required=True),
            "Prossimo Taglio": st.column_config.DateColumn("Prossimo Intervento", format="DD/MM/YYYY", required=True),
            "Importo": st.column_config.NumberColumn("Prezzo (€)", format="%.2f €", min_value=0, required=True),
            "Frequenza": st.column_config.NumberColumn("Frequenza (Giorni)", min_value=1, step=1, required=True),
            "Note": st.column_config.TextColumn("Note di Consegna")
        }
    )
    
    # Pulsante unico per effettuare la sincronizzazione di massa su Google Fogli
    if st.button("💾 Salva e Sincronizza modifiche nel Cloud", type="primary", use_container_width=True):
        conn.update(spreadsheet=URL_FOGLIO, data=df_modificato)
        st.success("✅ Database Cloud sincronizzato con successo!")
        st.rerun()