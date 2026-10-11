import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Ricettario Personale", page_icon="👨‍🍳", layout="centered")

# Recupero delle credenziali dai Secrets di Streamlit
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Inizializzazione di Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Inizializzazione del client Supabase una sola volta in cima allo script
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Errore di connessione a Supabase: {e}")
    st.stop()

st.title("👨‍🍳 Ricettario Personale")

# Navigazione tramite schede (Tab)
tab1, tab2 = st.tabs(["➕ Aggiungi Ricetta", "📖 Le Mie Ricette"])

with tab1:
    st.header("Inserimento Diretto")
    
    with st.form("add_recipe_form", clear_on_submit=True):
        manual_title = st.text_input("Titolo della Ricetta")
        manual_category = st.selectbox("Categoria", [
            "Salse e Condimenti", 
            "Primi Piatti", 
            "Secondi Piatti", 
            "Contorni", 
            "Dolci"
        ])
        manual_ingredients = st.text_area("Ingredienti (uno per riga)")
        manual_instructions = st.text_area("Procedimento")
        
        submitted = st.form_submit_button("💾 Salva Ricetta Diretta")
        
        if submitted:
            if manual_title and manual_ingredients and manual_instructions:
                try:
                    # Formattazione lista ingredienti
                    ingredients_list = "\n".join([
                        line.strip() for line in manual_ingredients.split("\n") if line.strip()
                    ])
                    
                    # Inserimento dati nel database Supabase
                    response = supabase.table("recipes").insert({
                        "title": manual_title,
                        "category": manual_category,
                        "ingredients": ingredients_list,
                        "instructions": manual_instructions
                    }).execute()
                    
                    st.success(f"Ricetta '{manual_title}' salvata con successo nel ricettario!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante il salvataggio diretto: {e}")
            else:
                st.warning("Per favore compila tutti i campi obbligatori!")

with tab2:
    st.header("Elenco Ricette")
    
    try:
        response = supabase.table("recipes").select("*").order("created_at", desc=True).execute()
        recipes = response.data
        
        if not recipes:
            st.info("Nessuna ricetta salvata al momento.")
        else:
            for recipe in recipes:
                with st.expander(f"📌 {recipe.get('title')} ({recipe.get('category')})"):
                    st.subheader("Ingredienti")
                    st.text(recipe.get("ingredients"))
                    st.subheader("Procedimento")
                    st.write(recipe.get("instructions"))
    except Exception as e:
        st.error(f"Errore nel recupero delle ricette: {e}")
