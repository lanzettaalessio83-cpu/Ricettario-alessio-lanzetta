import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

st.set_page_config(page_title="Assistente & Ricettario Digitale", page_icon="🍳", layout="centered")

# Configurazione chiavi
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
SUPABASE_URL = "https://ullqbitfscvlleblcym.supabase.co"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.8-flash')
else:
    model = None

st.title("🍳 Assistente & Ricettario Digitale")

# Struttura a 3 Tab
tab1, tab2, tab3 = st.tabs(["📖 Consulta Ricettario", "➕ Aggiungi con IA", "✍️ Inserimento Diretto"])

# TAB 1: CONSULTA RICETTARIO
with tab1:
    st.header("Elenco Ricette")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("recipes").select("*").order("created_at", desc=True).execute()
        recipes = response.data
        
        if not recipes:
            st.info("Nessuna ricetta salvata al momento.")
        else:
            for recipe in recipes:
                with st.expander(f"📌 {recipe.get('title', 'Senza Titolo')} ({recipe.get('category', 'Generale')})"):
                    st.subheader("Ingredienti")
                    ingredients = recipe.get('ingredients', [])
                    if isinstance(ingredients, list):
                        for ing in ingredients:
                            st.write(f"- {ing}")
                    else:
                        st.write(ingredients)
                        
                    st.subheader("Procedimento")
                    st.write(recipe.get('instructions', 'Nessuna istruzione inserita.'))
    except Exception as e:
        st.info("💡 Impossibile caricare l'elenco da Supabase in questo momento. Usa le schede di inserimento per aggiungere nuove ricette.")

# TAB 2: AGGIUNGI CON IA
with tab2:
    st.header("Inserisci una ricetta o un appunto grezzo")
    raw_text = st.text_area("Incolla qui i tuoi appunti o il procedimento libero:", height=150, key="ai_text")
    
    if st.button("🪄 Elabora e Salva con IA", type="primary"):
        if not raw_text.strip():
            st.warning("Inserisci prima del testo per elaborare la ricetta!")
        elif not model:
            st.error("Chiave GEMINI_API_KEY non configurata.")
        else:
            with st.spinner("Elaborazione in corso con Gemini..."):
                try:
                    prompt = f"""
                    Estrai le informazioni strutturate dal seguente testo grezzo di una ricetta.
                    Rispondi ESCLUSIVAMENTE con un oggetto JSON valido con queste chiavi:
                    - "title": stringa con il nome della ricetta
                    - "category": stringa con la categoria (es. Antipasti, Primi, Secondi, Dolci, Salse)
                    - "ingredients": lista di stringhe con ingredienti e dosi
                    - "instructions": stringa con il procedimento dettagliato passo dopo passo

                    Testo grezzo:
                    {raw_text}
                    """
                    
                    res = model.generate_content(prompt)
                    clean_res = res.text.strip().removeprefix("```json").removesuffix("```").strip()
                    data = json.loads(clean_res)
                    
                    # Salvataggio su Supabase
                    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                    supabase.table("recipes").insert({
                        "title": data.get("title", "Nuova Ricetta"),
                        "category": data.get("category", "Generale"),
                        "ingredients": data.get("ingredients", []),
                        "instructions": data.get("instructions", "")
                    }).execute()
                    
                    st.success(f"Ricetta '{data.get('title')}' elaborata e salvata con successo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante l'elaborazione o il salvataggio: {e}")

# TAB 3: INSERIMENTO DIRETTO (MANUALE)
with tab3:
    st.header("Inserimento Manuale Rapido")
    with st.form("manual_recipe_form"):
        manual_title = st.text_input("Titolo della Ricetta")
        manual_category = st.selectbox("Categoria", ["Antipasti", "Primi Piatti", "Secondi Piatti", "Dolci", "Salse e Condimenti", "Contorni", "Generale"])
        manual_ingredients = st.text_area("Ingredienti (uno per riga)", placeholder="es.\n500g parmigiano\n200ml brodo vegetale")
        manual_instructions = st.text_area("Procedimento", placeholder="Descrivi i passaggi...")
        
        submitted = st.form_submit_button("💾 Salva Ricetta Diretta", type="primary")
        
        if submitted:
            if not manual_title.strip():
                st.warning("Inserisci almeno il titolo della ricetta!")
            else:
                try:
                    ingredients_list = [line.strip() for line in manual_ingredients.split("\n") if line.strip()]
                    
                    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                    supabase.table("recipes").insert({
                        "title": manual_title,
                        "category": manual_category,
                        "ingredients": ingredients_list,
                        "instructions": manual_instructions
                    }).execute()
                    
                    st.success(f"Ricetta '{manual_title}' salvata con successo nel ricettario!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante il salvataggio diretto: {e}")
