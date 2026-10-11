import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai

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

# Menu di navigazione tra le sezioni (incluso l'Assistente IA)
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
# SEZIONE 2: AGGIUNGI UNA NUOVA RICETTA
# ---------------------------------------------------------
elif menu == "Aggiungi Ricetta":
    st.header("Aggiungi una nuova ricetta")
    
    with st.form("form_ricetta"):
        titolo = st.text_input("Titolo della ricetta")
        
        categoria = st.selectbox(
            "Categoria",
            [
                "Salse fredde", 
                "Salse calde", 
                "Primi piatti", 
                "Secondi piatti", 
                "Primi piatti caldi", 
                "Primi piatti freddi", 
                "Dolci", 
                "Contorni"
            ]
        )
        
        ingredienti = st.text_area("Ingredienti (uno per riga o separati da virgola)")
        istruzioni = st.text_area("Istruzioni / Procedimento")
        
        submit_button = st.form_submit_button(label="Salva Ricetta")
        
        if submit_button:
            if titolo.strip() == "" or ingredienti.strip() == "" or istruzioni.strip() == "":
                st.warning("Per favore, compila tutti i campi obbligatori prima di salvare.")
            else:
                try:
                    response = supabase.table("recipes").insert({
                        "title": titolo,
                        "category": categoria,
                        "ingredients": ingredienti,
                        "instructions": istruzioni
                    }).execute()
                    
                    st.success(f"Ricetta '{titolo}' salvata con successo!")
                except Exception as e:
                    st.error(f"Errore durante il salvataggio su Supabase: {e}")

# ---------------------------------------------------------
# SEZIONE 3: ASSISTENTE CHEF IA
# ---------------------------------------------------------
elif menu == "Assistente Chef IA 🤖":
    st.header("Assistente Chef IA")
    st.write("Chiedi consigli di cucina, abbinamenti, conversioni di dosi o idee per i tuoi piatti.")
    
    if model is None:
        st.warning("La chiave API di Gemini non è configurata correttamente nei Secrets.")
    else:
        prompt_utente = st.text_input("Cosa vuoi chiedere allo Chef IA?")
        if st.button("Chiedi all'IA"):
            if prompt_utente.strip():
                with st.spinner("Lo chef sta pensando..."):
                    try:
                        risposta = model.generate_content(f"Agisci come uno chef professionista di alto livello. Rispondi a questa richiesta culinaria: {prompt_utente}")
                        st.markdown("### Risposta dello Chef:")
                        st.write(risposta.text)
                    except Exception as e:
                        st.error(f"Errore nella generazione della risposta: {e}")
            else:
                st.warning("Scrivi una domanda prima di inviare.")
