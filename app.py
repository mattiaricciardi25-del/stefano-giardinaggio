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

# Stile CSS personalizzato per un'interfaccia moderna, pulita e leggibile
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: bold;
    }
    .client-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 5px solid #2e7d32;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌱 Stefano Giardinaggio Pro")
st.caption("Piattaforma Cloud di Gestione Interventi ed Equipaggio")

# ==============================================================================
# INCOLLA QUI SOTTO IL TUO LINK DI GOOGLE FOGLI (IMPOSTATO COME EDITOR)
# ==============================================================================
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/IL_TUO_ID_DEL_FOGLIO/edit?usp=sharing"

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

# TEMPO REALE: Controlla l'orologio internet esatto ad ogni caricamento della pagina
oggi = datetime.now().date()

# Calcolo delle metriche per la dashboard superiore
clienti_oggi = df[df['Prossimo Taglio'] <= oggi]
lavori_totali_oggi = len(clienti_oggi)
incasso_previsto = clienti_oggi['Importo'].sum()

# Dashboard moderna con card riassuntive
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric(label="📋 Lavori di Oggi", value=f"{lavori_totali_oggi} interventi")
with col_m2:
    st.metric(label="💰 Budget Giornaliero", value=f"{incasso_previsto:.2f} €")
with col_m3:
    st.metric(label="📆 Data Odierna", value=oggi.strftime('%d/%m/%Y'))

st.write("---")

# Creazione dei pannelli di navigazione
tab_oggi, tab_admin = st.tabs(["📅 Agenda di Oggi", "📝 Pannello di Controllo Excel"])

# ---------------------------------------------------------
# PANNELLO 1: AGENDA DEL GIORNO (Interfaccia Mobile con Card)
# ---------------------------------------------------------
with tab_oggi:
    st.subheader(f"Mappa interventi del: {oggi.strftime('%d/%m/%Y')}")
    
    if clienti_oggi.empty:
        st.success("🎉 Ottimo lavoro! Tutti gli interventi in scadenza oggi sono stati completati.")
    else:
        st.markdown("### ⚡ Interventi da gestire sul campo:")
        
        for index, row in clienti_oggi.iterrows():
            data_regolare = oggi + timedelta(days=int(row['Frequenza']))
            data_rimandato = oggi + timedelta(days=7)
            
            # Box elegante HTML per mostrare i dettagli del cliente
            st.markdown(f"""
            <div class="client-card">
                <h3 style='margin:0; color:#1e1e1e;'>👤 {row['Nome']}</h3>
                <p style='margin:5px 0; color:#666;'>💵 <b>Prezzo:</b> {row['Importo']:.2f}€ | ⏱️ <b>Frequenza:</b> ogni {row['Frequenza']} giorni</p>
                <p style='margin:5px 0; color:#444; font-style:italic;'>📝 <b>Note:</b> {row['Note'] if row['Note'] != "" else "Nessuna nota"}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Pulsanti d'azione rapidi per chi lavora sul telefono
            col_c, col_r = st.columns(2)
            with col_c:
                if st.button(f"🟢 Completato ({data_regolare.strftime('%d/%m')})", key=f"comp_{index}", use_container_width=True):
                    df.at[index, 'Prossimo Taglio'] = data_regolare
                    conn.update(spreadsheet=URL_FOGLIO, data=df)
                    st.toast(f"✅ Intervento per {row['Nome']} registrato al cloud!")
                    st.rerun()
            with col_r:
                if st.button(f"🔴 Rimanda (+7 giorni)", key=f"rim_{index}", use_container_width=True):
                    df.at[index, 'Prossimo Taglio'] = data_rimandato
                    conn.update(spreadsheet=URL_FOGLIO, data=df)
                    st.toast(f"⚠️ Slittato alla prossima settimana.")
                    st.rerun()
            st.write("")

# ---------------------------------------------------------
# PANNELLO 2: INTERFACCIA EXCEL (Aggiungi, Modifica, Elimina)
# ---------------------------------------------------------
with tab_admin:
    st.subheader("⚙️ Gestione Amministrativa Interattiva")
    st.markdown("""
    * **Modificare:** Fai doppio clic su una cella qualsiasi per aggiornare i dati.
    * **Aggiungere:** Vai in fondo alla tabella e compila la riga vuota per inserire un nuovo cliente.
    * **Eliminare:** Seleziona la riga dalla casellina a sinistra e premi il tasto *Canc* o *Delete* sulla tastiera.
    """)
    
    # Configurazione avanzata dell'editor di tabelle interattivo
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
    
    # Pulsante unico di salvataggio massivo
    if st.button("💾 Salva e Sincronizza modifiche nel Cloud", type="primary", use_container_width=True):
        conn.update(spreadsheet=URL_FOGLIO, data=df_modificato)
        st.success("✅ Database Cloud sincronizzato con successo!")
        st.rerun()