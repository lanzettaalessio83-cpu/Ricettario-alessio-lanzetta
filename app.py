import streamlit as st
from supabase import create_client, Client

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Il Mio Ricettario",
    page_icon="📖",
    layout="centered"
)

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
menu = st.sidebar.radio("Seleziona", ["Aggiungi Ricetta", "Elenco Ricette"])

# ---------------------------------------------------------
# SEZIONE 1: AGGIUNGI UNA NUOVA RICETTA
# ---------------------------------------------------------
if menu == "Aggiungi Ricetta":
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
                    # Inserimento dei dati nella tabella 'recipes' di Supabase
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
# SEZIONE 2: ELENCO RICETTE
# ---------------------------------------------------------
elif menu == "Elenco Ricette":
    st.header("Elenco delle Ricette")
    
    try:
        # Recupero delle ricette dal database Supabase
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
        st.error(f"Impossibile caricare le ricette da Supabase. Verifica che la tabella esista. Errore: {e}")
