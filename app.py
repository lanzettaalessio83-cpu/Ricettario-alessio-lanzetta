import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

# Configurazione pagina Streamlit
st.set_page_config(page_title="Assistente & Ricettario Digitale", page_icon="🍳", layout="centered")

# Legge  credenziali dai Secrets di Streamlit Cloud
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

# Configurazione Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.8-flash')
else:
    model = None

# Configurazione Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase = None

st.title("🍳 Assistente & Ricettario Digitale")

tab1, tab2 = st.tabs(["📖 Consulta Ricettario", "➕ Aggiungi con IA"])

# TAB 1: CONSULTA RICETTARIO
with tab1:
    st.header("Elenco Ricette")
    if not supabase:
        st.warning("⚠️ Supabase non è connesso. Verifica di aver inserito l'URL e la Key corretti nei Secrets.")
    else:
        try:
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
            st.error(f"Errore nel caricamento delle ricette da Supabase: {e}")

# TAB 2: AGGIUNGI CON IA
with tab2:
    st.header("Inserisci una ricetta o un appunto grezzo")
    raw_text = st.text_area("Incolla qui i tuoi appunti o il procedimento libero:", height=150)
    
    if st.button("🪄 Elabora e Salva con IA", type="primary"):
        if not raw_text.strip():
            st.warning("Inserisci prima del testo per elaborare la ricetta!")
        elif not model:
            st.error("Chiave GEMINI_API_KEY non configurata nei Secrets.")
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
                    
                    if supabase:
                        # Salvataggio su Supabase
                        supabase.table("recipes").insert({
                            "title": data.get("title", "Nuova Ricetta"),
                            "category": data.get("category", "Generale"),
                            "ingredients": data.get("ingredients", []),
                            "instructions": data.get("instructions", "")
                        }).execute()
                        st.success(f"Ricetta '{data.get('title')}' salvata con successo!")
                        st.rerun()
                    else:
                        st.success(f"Ricetta elaborata: {data.get('title')}")
                        st.json(data)
                except Exception as e:
                    st.error(f"Errore durante l'elaborazione o il salvataggio: {e}")