import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
from PIL import Image
import json

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Il Mio Ricettario",
    page_icon="📖",
    layout="centered"
)

# Configurazione di Gemini IA usando i secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception:
    model = None

# Inizializzazione della connessione a Supabase usando i secrets configurati
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Titolo principale dell'applicazione
st.title("📖 Il Mio Ricettario")

# Menu di navigazione tra le sezioni
menu = st.sidebar.radio("Seleziona", ["Elenco Ricette", "Aggiungi Ricetta", "Assistente Chef IA 🤖"])

# ---------------------------------------------------------
# SEZIONE 1: ELENCO RICETTE
# ---------------------------------------------------------
if menu == "Elenco Ricette":
    st.header("Elenco delle Ricette")
    
    try:
        response = supabase.table("recipes").select("*").execute()
        ricette = response.data
        
        if not ricette:
            st.info("Nessuna ricetta presente nel database. Inizia ad aggiungerne una!")
        else:
            for ricetta in ricette:
                with st.expander(f"🍽️ {ricetta.get('title')} ({ricetta.get('category', 'Generale')})"):
                    st.markdown(f"**Ingredienti:**\n{ricetta.get('ingredients')}")
                    st.markdown(f"**Procedimento:**\n{ricetta.get('instructions')}")
    except Exception as e:
        st.error(f"Impossibile caricare le ricette da Supabase. Errore: {e}")

# ---------------------------------------------------------
# SEZIONE 2: AGGIUNGI UNA NUOVA RICETTA (CON ASSISTENTE IA)
# ---------------------------------------------------------
elif menu == "Aggiungi Ricetta":
    st.header("Aggiungi una nuova ricetta")
    
    # Inizializzazione dello stato per i campi se non esistono
    if "titolo_auto" not in st.session_state:
        st.session_state.titolo_auto = ""
    if "categoria_auto" not in st.session_state:
        st.session_state.categoria_auto = "Primi piatti"
    if "ingredienti_auto" not in st.session_state:
        st.session_state.ingredienti_auto = ""
    if "istruzioni_auto" not in st.session_state:
        st.session_state.istruzioni_auto = ""

    # SEZIONE IA PER ANALISI TESTO O FOTO
    st.subheader("🤖 Genera o Formattta con l'IA")
    st.write("Puoi scrivere la ricetta in modo grezzo oppure caricare un'immagine/foto di una ricetta per compilarla in automatico!")

    testo_grezzo = st.text_area("Inserisci testo grezzo della ricetta (opzionale)")
    
    # Opzione per scattare una foto o caricare dalla galleria
    fonte_immagine = st.radio("Metodo inserimento foto", ["Disattivo", "Galleria / File", "Fotocamera"], horizontal=True)
    
    immagine_caricata = None
    if fonte_immagine == "Galleria / File":
        immagine_caricata = st.file_uploader("Scegli un'immagine dalla galleria", type=["jpg", "jpeg", "png", "webp"])
    elif fonte_immagine == "Fotocamera":
        immagine_caricata = st.camera_input("Scatta una foto della ricetta")

    if st.button("✨ Formatta / Estrai con IA"):
        
