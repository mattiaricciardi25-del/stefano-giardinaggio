import streamlit as st # type: ignore
import pandas as pd # type: ignore
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection # type: ignore

# Configurazione della pagina
st.set_page_config(page_title="Stefano Giardinaggio", page_icon="🌱", layout="centered")
st.title("🌱 Gestione Avanzata - Stefano Giardinaggio")

# ==============================================================================
# INCOLLA QUI SOTTO IL TUO LINK DI GOOGLE FOGLI (IMPOSTATO COME EDITOR)
# ==============================================================================
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1LRKMpS-EXbvaB_DaGt33KFchRPpuqGxH3marxzwk330/edit?usp=sharing"

# Connessione nativa al Foglio Google
conn = st.connection("gsheets", type=GSheetsConnection)

# Carichiamo i dati aggiornati dal cloud
try:
    df = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
    df['Prossimo Taglio'] = pd.to_datetime(df['Prossimo Taglio']).dt.date
    df['Importo'] = df['Importo'].astype(float)
    df['Frequenza'] = df['Frequenza'].astype(int)
    df['Note'] = df['Note'].fillna("")
except Exception as e:
    st.error("Errore nel caricamento dei dati da Google Fogli. Controlla il link.")
    st.stop()

oggi = datetime(2026, 7, 8).date()

# Creazione delle schede
tab_oggi, tab_admin = st.tabs(["📅 Interventi di Oggi", "📝 Modifica Database Excel"])

# ---------------------------------------------------------
# SCHEDA 1: INTERVENTI DI OGGI (Per i ragazzi sul campo)
# ---------------------------------------------------------
with tab_oggi:
    st.subheader(f"Lavori del giorno: {oggi.strftime('%d/%m/%Y')}")
    clienti_oggi = df[df['Prossimo Taglio'] <= oggi]

    if clienti_oggi.empty:
        st.success("🎉 Ottimo! Nessun intervento rimasto da gestire per oggi.")
    else:
        for index, row in clienti_oggi.iterrows():
            data_regolare = row['Prossimo Taglio'] + timedelta(days=int(row['Frequenza']))
            data_rimandato = row['Prossimo Taglio'] + timedelta(days=7)
            
            st.info(f"**{row['Nome']}** | Prezzo: {row['Importo']}€ | Ogni {row['Frequenza']} giorni\n\n"
                    f"* Se completato oggi, slitta a: **{data_regolare.strftime('%d/%m/%Y')}**\n"
                    f"* Se rimandi oggi, slitta a: **{data_rimandato.strftime('%d/%m/%Y')}**")
            
            col_comp, col_rim = st.columns(2)
            
            with col_comp:
                if st.button(f"🟢 Completato", key=f"comp_{index}", use_container_width=True):
                    df.at[index, 'Prossimo Taglio'] = data_regolare
                    conn.update(spreadsheet=URL_FOGLIO, data=df)
                    st.toast(f"✅ Taglio salvato online per {row['Nome']}!")
                    st.rerun()
                    
            with col_rim:
                if st.button(f"🔴 Rimanda (+7gg)", key=f"rim_{index}", use_container_width=True):
                    df.at[index, 'Prossimo Taglio'] = data_rimandato
                    conn.update(spreadsheet=URL_FOGLIO, data=df)
                    st.toast(f"🔴 Rimandato di una settimana su Google Fogli!")
                    st.rerun()
            st.write("")

# ---------------------------------------------------------
# SCHEDA 2: DATABASE INTERATTIVO (Aggiungi, Modifica, Elimina)
# ---------------------------------------------------------
with tab_admin:
    st.subheader("📝 Modifica Libera del Database")
    st.markdown("""
    * **Modificare:** Fai doppio clic su una cella qualsiasi per cambiare nome, data, importo o note.
    * **Aggiungere:** Scorri fino in fondo alla tabella e scrivi nella riga vuota per creare un nuovo cliente.
    * **Eliminare:** Seleziona la casellina a sinistra di una riga e premi il tasto "Canc" (o Delete) sulla tastiera.
    """)
    
    # Crea la tabella completamente modificabile
    df_modificato = st.data_editor(
        df,
        num_rows="dynamic", # Questa magia permette di aggiungere/eliminare righe
        use_container_width=True,
        hide_index=True,
        column_config={
            "Prossimo Taglio": st.column_config.DateColumn("Prossimo Taglio", format="YYYY-MM-DD"),
            "Importo": st.column_config.NumberColumn("Importo (€)", format="%.2f", step=1.0),
            "Frequenza": st.column_config.NumberColumn("Frequenza (Giorni)", step=1)
        }
    )
    
    # Pulsantone per salvare tutto su Google Fogli in un colpo solo
    if st.button("💾 Salva Modifiche Online", type="primary", use_container_width=True):
        conn.update(spreadsheet=URL_FOGLIO, data=df_modificato)
        st.success("✅ Database su Google Fogli aggiornato con successo!")
        st.rerun()