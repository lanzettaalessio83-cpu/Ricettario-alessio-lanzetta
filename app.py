
import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

st.set_page_config(page_title="Assistente & Ricettario Digitale", page_icon="🍳", layout="centered")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
SUPABASE_URL = "https://ullqbitfscvlleblcym.supabase.co"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.8-flash')
else:
    model = None

st.title("🍳 Assistente & Ricettario Digitale")

tab1, tab2 = st.tabs(["📖 Consulta Ricettario", "➕ Aggiungi con IA"])

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
                    for ing in recipe.get('ingredients', []):
                        st.write(f"- {ing}")
                    st.subheader("Procedimento")
                    st.write(recipe.get('instructions', ''))
    except Exception as e:
        st.info("💡 Il database Supabase non è al momento raggiungibile con questo URL. Puoi comunque usare la scheda 'Aggiungi con IA' per generare e testare le tue ricette.")

with tab2:
    st.header("Inserisci una ricetta o un appunto grezzo")
    raw_text = st.text_area("Incolla qui i tuoi appunti o il procedimento libero:", height=150)
    
    if st.button("🪄 Elabora con IA", type="primary"):
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
                    
                    st.success("Ricetta elaborata con successo dall'IA!")
                    st.subheader(data.get("title"))
                    st.write(f"**Categoria:** {data.get('category')}")
                    st.write("**Ingredienti:**")
                    for ing in data.get("ingredients", []):
                        st.write(f"- {ing}")
                    st.write("**Procedimento:**")
                    st.write(data.get("instructions"))
                    
                    # Prova il salvataggio su Supabase in background
                    try:
                        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                        supabase.table("recipes").insert({
                            "title": data.get("title", "Nuova Ricetta"),
                            "category": data.get("category", "Generale"),
                            "ingredients": data.get("ingredients", []),
                            "instructions": data.get("instructions", "")
                        }).execute()
                        st.success("Salvato anche su Supabase!")
                    except:
                        pass

                except Exception as e:
                    st.error(f"Errore durante l'elaborazione: {e}")
