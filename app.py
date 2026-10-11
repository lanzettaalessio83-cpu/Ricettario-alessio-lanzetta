import streamlit as st
from supabase import create_client, Client

st.title("👨‍🍳 Ricettario Personale")

try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
except Exception as e:
    st.error("⚠️ Configurazione Secrets mancante. Aggiungi la sezione [supabase] nel pannello di Streamlit Cloud.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Errore di connessione a Supabase: {e}")
    st.stop()

tab1, tab2 = st.tabs(["➕ Aggiungi Ricetta", "📖 Le Mie Ricette"])

with tab1:
    st.header("Nuova Ricetta")
    with st.form("recipe_form", clear_on_submit=True):
        title = st.text_input("Titolo della Ricetta")
        category = st.selectbox(
            "Categoria", 
            ["Antipasti", "Primi Piatti", "Secondi Piatti", "Contorni", "Salse e Condimenti", "Dolci"]
        )
        ingredients = st.text_area("Ingredienti (uno per riga)")
        instructions = st.text_area("Procedimento")
        
        submitted = st.form_submit_button("💾 Salva Ricetta")
        
        if submitted:
            if not title or not ingredients or not instructions:
                st.warning("Per favore, compila tutti i campi.")
            else:
                try:
                    data = {
                        "title": title,
                        "category": category,
                        "ingredients": ingredients,
                        "instructions": instructions
                    }
                    supabase.table("recipes").insert(data).execute()
                    st.success(f"Ricetta '{title}' salvata con successo!")
                except Exception as e:
                    st.error(f"Errore durante il salvataggio: {e}")

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
                    st.write(recipe.get('ingredients'))
                    st.subheader("Procedimento")
                    st.write(recipe.get('instructions'))
    except Exception as e:
        st.error(f"Errore nel recupero delle ricette: {e}")

