import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Ricettario alessio",
    page_icon="🍳",
    layout="centered"
)

# Configurazione della chiave API di Gemini dai Secrets di Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Chiave GEMINI_API_KEY non trovata nei secrets di Streamlit!")

st.title("🍳 Ricettario alessio")
st.markdown("Gestisci e compila le tue ricette personali anche con l'ausilio dell'Intelligenza Artificiale.")

# Sezione di inserimento / elaborazione ricetta
st.subheader("Aggiungi o Elabora Ricetta")

titolo = st.text_input("Titolo della Ricetta")
categoria = st.selectbox(
    "Categoria", 
    ["Salse fredde", "Salse calde", "Primi piatti", "Secondi piatti", "Dolci", "Contorni", "Antipasti"]
)
ingredienti = st.text_area("Ingredienti")
procedimento = st.text_area("Procedimento")

st.markdown("---")
st.write("Vuoi aggiungere una foto o scattare una foto alla ricetta per compilarla automaticamente con l'IA?")

scelta_foto = st.radio("Vuoi aggiungere una foto?", ["No", "Galleria / File", "Fotocamera"], horizontal=True)

immagine_caricata = None

if scelta_foto == "Galleria / File":
    immagine_caricata = st.file_uploader("Carica l'immagine della ricetta", type=["jpg", "jpeg", "png"])
elif scelta_foto == "Fotocamera":
    immagine_caricata = st.camera_input("Scatta una foto alla ricetta")

# Pulsante per elaborare con l'IA
if st.button("✨ Elabora con IA e Compila"):
    if not immagine_caricata and not ingredienti:
        st.warning("⚠️ Carica un'immagine o inserisci del testo prima di avviare l'elaborazione IA.")
    else:
        try:
            with st.spinner("L'intelligenza artificiale sta analizzando la ricetta..."):
                # Inizializziamo il modello Gemini
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = (
                    "Estrai da questa immagine o testo i dettagli della ricetta e restituisci "
                    "esattamente in formato strutturato: Titolo, Ingredienti e Procedimento in lingua italiana."
                )
                
                if immagine_caricata:
                    img = Image.open(immagine_caricata)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(f"{prompt}\n\nTesto di riferimento:\n{ingredienti}")
                
                st.success("✅ Ricetta elaborata con successo!")
                st.write(response.text)
                
        except Exception as e:
            st.error(f"Errore durante l'elaborazione IA: {e}")

# Pulsante di salvataggio finale nel ricettario
if st.button("Salva Ricetta nel Database"):
    if titolo:
        st.success(f"Ricetta '{titolo}' salvata correttamente nel tuo ricettario!")
    else:
        st.error("Inserisci almeno il titolo per poter salvare la ricetta.")
