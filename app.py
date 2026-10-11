import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
from PIL import Image
import json

st.set_page_config(page_title="Il Mio Ricettario", page_icon="📖", layout="centered")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception:
    model = None

@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

st.title("📖 Il Mio Ricettario")

# Menu pulito con sole due voci: niente chat o assistenti separati
menu = st.sidebar.radio("Seleziona", ["Elenco Ricette", "Aggiungi Ricetta"])

if menu == "Elenco Ricette":
    st.header("Elenco delle Ricette")
    try:
        response = supabase.table("recipes").select("*").execute()
        ricette = response.data
        if not ricette:
            st.info("Nessuna ricetta presente nel database.")
        else:
            for r in ricette:
                with st.expander(f"🍽️ {r.get('title')} ({r.get('category', 'Generale')})"):
                    st.markdown(f"**Ingredienti:**\n{r.get('ingredients')}")
                    st.markdown(f"**Procedimento:**\n{r.get('instructions')}")
    except Exception as e:
        st.error(f"Errore: {e}")

elif menu == "Aggiungi Ricetta":
    st.header("Aggiungi una nuova ricetta")
    
    if "t" not in st.session_state: st.session_state.t = ""
    if "c" not in st.session_state: st.session_state.c = "Primi piatti"
    if "i" not in st.session_state: st.session_state.i = ""
    if "p" not in st.session_state: st.session_state.p = ""

    st.subheader("📸 Inserimento intelligente con IA (Foto o Testo)")
    
    testo = st.text_area("Incolla qui il testo grezzo della ricetta (opzionale)")
    fonte = st.radio("Vuoi aggiungere una foto?", ["No", "Galleria / File", "Fotocamera"], horizontal=True)
    
    img_file = None
    if fonte == "Galleria / File":
        img_file = st.file_uploader("Scegli immagine", type=["jpg", "jpeg", "png", "webp"])
    elif fonte == "Fotocamera":
        img_file = st.camera_input("Scatta foto")

    if st.button("✨ Elabora con IA e Compila"):
        if model is None:
            st.error("Chiave Gemini non configurata nei Secrets.")
        elif not testo.strip() and img_file is None:
            st.warning("Inserisci del testo o carica/scatta una foto.")
        else:
            with st.spinner("L'IA sta leggendo e sistemando la ricetta..."):
                try:
                    prompt = """
                    Analizza il testo o l'immagine fornita ed estrai la ricetta.
                    Rispondi ESCLUSIVAMENTE in formato JSON con queste chiavi:
                    {
                      "title": "Titolo della ricetta",
                      "category": "Una tra: Salse fredde, Salse calde, Primi piatti, Secondi piatti, Primi piatti caldi, Primi piatti freddi, Dolci, Contorni",
                      "ingredients": "- Ingrediente 1\\n- Ingrediente 2",
                      "instructions": "1. Passaggio...\\n2. Passaggio..."
                    }
                    """
                    cont = [prompt]
                    if testo.strip(): cont.append(testo)
                    if img_file: cont.append(Image.open(img_file))
                    
                    res = model.generate_content(cont)
                    txt = res.text.strip().replace("```json", "").replace("```", "").strip()
                    data = json.loads(txt)
                    
                    st.session_state.t = data.get("title", "")
                    st.session_state.c = data.get("category", "Primi piatti")
                    st.session_state.i = data.get("ingredients", "")
                    st.session_state.p = data.get("instructions", "")
                    st.success("Fatto! I campi qui sotto sono stati compilati dall'IA. Controlla e salva.")
                except Exception as e:
                    st.error(f"Errore durante l'elaborazione IA: {e}")

    st.divider()

    cats = ["Salse fredde", "Salse calde", "Primi piatti", "Secondi piatti", "Primi piatti caldi", "Primi piatti freddi", "Dolci", "Contorni"]
    idx = cats.index(st.session_state.c) if st.session_state.c in cats else 0

    with st.form("f"):
        tit = st.text_input("Titolo della ricetta", value=st.session_state.t)
        cat = st.selectbox("Categoria", cats, index=idx)
        ing = st.text_area("Ingredienti", value=st.session_state.i, height=150)
        ins = st.text_area("Procedimento", value=st.session_state.p, height=200)
        
        if st.form_submit_button("💾 Salva sul Database"):
            if not tit or not ing or not ins:
                st.warning("Compila tutti i campi.")
            else:
                try:
                    supabase.table("recipes").insert({
                        "title": tit, 
                        "category": cat, 
                        "ingredients": ing, 
                        "instructions": ins
                    }).execute()
                    
                    st.success(f"Ricetta '{tit|titolo if 'tit' in locals() else 'salvata'}' salvata con successo!")
                    st.session_state.t = ""
                    st.session_state.i = ""
                    st.session_state.p = ""
                except Exception as e:
                    st.error(f"Errore di salvataggio: {e}")
