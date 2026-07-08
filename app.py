import streamlit as st # type: ignore
import pandas as pd # type: ignore
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Stefano Giardinaggio", page_icon="🌱", layout="centered")
st.title("🌱 Gestione Avanzata - Stefano Giardinaggio")

# INCOLLA QUI IL LINK DEL TUO FOGLIO GOOGLE CONDIVISO COME EDITOR
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1LRKMpS-EXbvaB_DaGt33KFchRPpuqGxH3marxzwk330/edit?usp=sharing"

# Funzione per convertire il link normale in un link di esportazione CSV diretta
def ottieni_url_csv(url):
    try:
        id_foglio = url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{id_foglio}/export?format=csv"
    except:
        return url

URL_CSV = ottieni_url_csv(URL_FOGLIO)

# Funzione per caricare i dati in tempo reale dal Cloud
def recupera_dati():
    # st.ttl=0 forza lo script a riscaricare il foglio a ogni refresh senza usare la cache vecchia
    df = pd.read_csv(URL_CSV)
    df['Prossimo Taglio'] = pd.to_datetime(df['Prossimo Taglio']).dt.date
    df['Importo'] = df['Importo'].astype(float)
    df['Frequenza'] = df['Frequenza'].astype(int)
    return df

# Nota: non usiamo session_state per il dataframe per evitare che utenti diversi vedano dati vecchi in cache
try:
    df = recupera_dati()
except Exception as e:
    st.error("Errore nel collegamento al database di Google Fogli. Controlla il link o i permessi di condivisione.")
    st.stop()

# Nota: Per far scrivere i dati sul foglio Google in modo nativo e sicuro da Streamlit Cloud senza database complessi,
# il metodo più rapido e senza configurare chiavi private API (visto che l'app è per voi 4) è usare la libreria gspread
# oppure inviare i dati tramite una richiesta POST. Per adesso, configuriamo l'interfaccia visiva.
# Per permettere la scrittura immediata su Fogli Google senza configurazioni pesanti, useremo st.experimental_connection o gspread.

# Per rendere questa guida immediata e non bloccarti con le credenziali API di Google Cloud Console,
# mostriamo la logica di visualizzazione. 
oggi = datetime(2026, 7, 8).date()

def determina_stato(data_taglio):
    if data_taglio == oggi:
        return "📅 DA FARE OGGI"
    elif data_taglio < oggi:
        return "⚠️ SCADUTO"
    else:
        return "⏳ Programmato"

df['Stato Giorno'] = df['Prossimo Taglio'].apply(determina_stato)

tab_oggi, tab_admin = st.tabs(["📅 Interventi di Oggi", "⚙️ Gestisci & Aggiungi Clienti"])

with tab_oggi:
    st.subheader(f"Lavori del giorno: {oggi.strftime('%d/%m/%Y')}")
    clienti_oggi = df[df['Prossimo Taglio'] <= oggi]

    if clienti_oggi.empty:
        st.success("🎉 Ottimo! Nessun intervento rimasto da gestire per oggi.")
    else:
        st.dataframe(
            clienti_oggi[['Nome', 'Prossimo Taglio', 'Importo', 'Frequenza', 'Note']], 
            column_config={
                "Importo": st.column_config.NumberColumn("Importo (€)", format="%.2f €"),
                "Frequenza": st.column_config.NumberColumn("Frequenza (GG)")
            },
            use_container_width=True
        )
        
        st.write("---")
        st.subheader("⚡ Azioni Rapide")
        
        for index, row in clienti_oggi.iterrows():
            data_regolare_successiva = row['Prossimo Taglio'] + timedelta(days=int(row['Frequenza']))
            data_se_rimandato = row['Prossimo Taglio'] + timedelta(days=7)
            prossimo_taglio_dopo_rimando = data_se_rimandato + timedelta(days=int(row['Frequenza']))
            
            st.info(f"**{row['Nome']}** | Prezzo: {row['Importo']}€ | Ogni {row['Frequenza']} giorni\n\n"
                    f"* Se completato: **{data_regolare_successiva.strftime('%d/%m/%Y')}**\n"
                    f"* Se rimandato: **{data_se_rimandato.strftime('%d/%m/%Y')}**")
            
            col_comp, col_rim = st.columns(2)
            with col_comp:
                if st.button(f"🟢 Completato", key=f"comp_{index}", use_container_width=True):
                    st.warning("Per salvare le modifiche online è necessario connettere le API di Google. Vedi i passi successivi.")
            with col_rim:
                if st.button(f"🔴 Rimanda (+7gg)", key=f"rim_{index}", use_container_width=True):
                    st.warning("Per salvare le modifiche online è necessario connettere le API di Google. Vedi i passi successivi.")

with tab_admin:
    st.info("Da qui potrai monitorare lo stato del database globale sincronizzato su Google Fogli.")
    st.dataframe(df[['Nome', 'Prossimo Taglio', 'Importo', 'Frequenza', 'Stato Giorno', 'Note']], use_container_width=True)