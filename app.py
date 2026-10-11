import streamlit as st
from supabase import create_client, Client

# --- INIZIALIZZAZIONE SUPABASE ---
# Recupero sicuro delle credenziali dai secrets di Streamlit
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- INTERFACCIA STREAMLIT ---
st.title("📖 Il Mio Ricettario")

tab1, tab2 = st.tabs(["Aggiungi Ricetta", "Elenco Ricette"])

# TAB 1: Inserimento nuova ricetta
with tab1:
    st.header("Aggiungi una nuova ricetta")
    
    with st.form("recipe_form", clear_on_submit=True):
        title = st.text_input("Titolo della ricetta")
        category = st.selectbox(
            "Categoria", 
            ["Salse fredde", "Salse calde", "Antipasti", "Primi piatti", "Secondi piatti", "Dolci", "Contorni"]
        )
        ingredients = st.text_area("Ingredienti (uno per riga o separati da virgola)")
        instructions = st.text_area("Istruzioni / Procedimento")
        
        submitted = st.form_submit_button("Salva Ricetta")
        
        if submitted:
            if not title.strip():
                st.warning("Inserisci almeno il titolo della ricetta!")
            else:
                data = {
                    "title": title,
                    "category": category,
                    "ingredients": ingredients,
                    "instructions": instructions
                }
                
                try:
                    # Inserimento dati nella tabella 'recipes' di Supabase
                    supabase.table("recipes").insert(data).execute()
                    st.success(f"Ricetta '{title}' salvata con successo!")
                except Exception as e:
                    st.error(f"Errore durante il salvataggio: {e}")

# TAB 2: Visualizzazione elenco ricette
with tab2:
    st.header("Elenco Ricette")
    
    try:
        # Recupero di tutte le ricette ordinate per titolo
        response = supabase.table("recipes").select("*").order("title").execute()
        recipes = response.data
        
        if not recipes:
            st.info("Nessuna ricetta presente nel database.")
        else:
            # Filtro per categoria
            categories = ["Tutte"] + list(set(r.get("category", "") for r in recipes if r.get("category")))
            selected_cat = st.selectbox("Filtra per categoria", categories)
            
            for recipe in recipes:
                if selected_cat == "Tutte" or recipe.get("category") == selected_cat:
                    with st.expander(f"📌 {recipe.get('title', 'Senza titolo')} ({recipe.get('category', 'Generale')})"):
                        st.subheader("Ingredienti")
                        st.write(recipe.get("ingredients", "Nessun ingrediente specificato."))
                        
                        st.subheader("Istruzioni")
                        st.write(recipe.get("instructions", "Nessuna istruzione fornita."))
                        
    except Exception as e:
        st.error(f"Errore nel caricamento delle ricette: {e}")