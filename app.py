import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
from PIL import Image

st.title("👨‍🍳 Ricettario Personale con IA")

# --- LETTURA SICURA DEI SECRETS (SUPPORTA QUALSIASI FORMATO) ---
SUPABASE_URL = None
SUPABASE_KEY = None
GEMINI_API_KEY = None

try:
    if "SUPABASE_URL" in st.secrets:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
    elif "supabase" in st.secrets:
        SUPABASE_URL = st.secrets["supabase"].get("url")

    if "SUPABASE_KEY" in st.secrets:
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    elif "supabase" in st.secrets:
        SUPABASE_KEY = st.secrets["supabase"].get("key")

    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    elif "gemini" in st.secrets:
        GEMINI_API_KEY = st.secrets["gemini"].get("api_key")
except Exception:
    pass

# Configurazione opzionale di Gemini se presente
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Controllo connessione Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Impossibile trovare le credenziali di Supabase nei Secrets. Verifica che siano impostate correttamente.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Errore di connessione a Supabase: {e}")
    st.stop()

def analyze_recipe_with_ai(content, is_image=False):
    if not GEMINI_API_KEY:
        return "ERRORE: Chiave Gemini non configurata."
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """
    Analizza il contenuto fornito ed estrai le informazioni in modo strutturato:
    - TITOLO: Nome della ricetta
    - CATEGORIA: Scegli una tra (Antipasti, Primi Piatti, Secondi Piatti, Contorni, Salse e Condimenti, Dolci)
    - INGREDIENTI: Elenco degli ingredienti (uno per riga)
    - PROCEDIMENTO: Passaggi dettagliati
    
    Rispondi esattamente in questo formato:
    TITOLO: [Titolo]
    CATEGORIA: [Categoria]
    INGREDIENTI:
    [ingredienti]
    PROCEDIMENTO:
    [procedimento]
    """
    if is_image:
        response = model.generate_content([prompt, content])
    else:
        response = model.generate_content(f"{prompt}\n\nContenuto:\n{content}")
    return response.text

def parse_ai_response(ai_text):
    try:
        lines = ai_text.split('\n')
        title, category, ingredients, instructions = "", "Primi Piatti", "", ""
        mode = None
        ing_lines = []
        inst_lines = []
        for line in lines:
            if line.startswith("TITOLO:"):
                title = line.replace("TITOLO:", "").strip()
                mode = None
            elif line.startswith("CATEGORIA:"):
                category = line.replace("CATEGORIA:", "").strip()
                mode = None
            elif line.startswith("INGREDIENTI:"):
                mode = "ing"
                continue
            elif line.startswith("PROCEDIMENTO:"):
                mode = "inst"
                continue
            if mode == "ing":
                ing_lines.append(line)
            elif mode == "inst":
                inst_lines.append(line)
        return title, category, "\n".join(ing_lines).strip(), "\n".join(inst_lines).strip()
    except Exception:
        return "", "Primi Piatti", "", ""

tab1, tab2 = st.tabs(["➕ Aggiungi Ricetta (Manuale & IA)", "📖 Le Mie Ricette"])

with tab1:
    st.header("Nuova Ricetta")
    
    input_mode = st.selectbox(
        "Scegli la modalità di inserimento",
        [
            "✏️ Inserimento Manuale",
            "🤖 IA: Genera da Testo/Descrizione",
            "🖼️ IA: Carica Foto Ricetta (Galleria)",
            "📸 IA: Scatta Foto Ricetta (Fotocamera)"
        ]
    )
    
    form_title = ""
    form_category = "Primi Piatti"
    form_ingredients = ""
    form_instructions = ""
    
    if input_mode == "🤖 IA: Genera da Testo/Descrizione":
        st.info("Scrivi una descrizione grezza e l'IA formatterà la ricetta.")
        raw_text = st.text_area("Descrizione o appunti")
        if st.button("🪄 Elabora con IA"):
            if raw_text:
                with st.spinner("Elaborazione in corso..."):
                    ai_res = analyze_recipe_with_ai(raw_text, is_image=False)
                    form_title, form_category, form_ingredients, form_instructions = parse_ai_response(ai_res)
                    st.success("Fatto! Controlla i campi sotto.")
            else:
                st.warning("Inserisci del testo.")
                
    elif input_mode == "🖼️ IA: Carica Foto Ricetta (Galleria)":
        st.info("Carica l'immagine di un libro o di un foglio.")
        uploaded_file = st.file_uploader("Scegli un'immagine", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Immagine caricata", use_column_width=True)
            if st.button("🪄 Estrai Ricetta da Foto"):
                with st.spinner("Analisi in corso..."):
                    ai_res = analyze_recipe_with_ai(image, is_image=True)
                    form_title, form_category, form_ingredients, form_instructions = parse_ai_response(ai_res)
                    st.success("Fatto! Controlla i campi sotto.")

    elif input_mode == "📸 IA: Scatta Foto Ricetta (Fotocamera)":
        st.info("Scatta una foto con la fotocamera.")
        camera_file = st.camera_input("Scatta una foto")
        if camera_file is not None:
            image = Image.open(camera_file)
            if st.button("🪄 Estrai Ricetta da Fotocamera"):
                with st.spinner("Analisi dello scatto..."):
                    ai_res = analyze_recipe_with_ai(image, is_image=True)
                    form_title, form_category, form_ingredients, form_instructions = parse_ai_response(ai_res)
                    st.success("Fatto! Controlla i campi sotto.")

    categories_list = ["Antipasti", "Primi Piatti", "Secondi Piatti", "Contorni", "Salse e Condimenti", "Dolci"]
    cat_index = categories_list.index(form_category) if form_category in categories_list else 1

    with st.form("recipe_form", clear_on_submit=True):
        title = st.text_input("Titolo della Ricetta", value=form_title)
        category = st.selectbox("Categoria", categories_list, index=cat_index)
        ingredients = st.text_area("Ingredienti (uno per riga)", value=form_ingredients)
        instructions = st.text_area("Procedimento", value=form_instructions)
        
        submitted = st.form_submit_button("💾 Salva Ricetta nel Database")
        
        if submitted:
            if not title or not ingredients or not instructions:
                st.warning("Compila tutti i campi obbligatori.")
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
                    st.error(f"Errore: {e}")

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
        st.error(f"Errore: {e}")