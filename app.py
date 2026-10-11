import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
from PIL import Image
import json

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

# Menu di navigazione tra le sezioni
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
# SEZIONE 2: AGGIUNGI UNA NUOVA RICETTA (CON ASSISTENTE IA)
# ---------------------------------------------------------
elif menu == "Aggiungi Ricetta":
    st.header("Aggiungi una nuova ricetta")
    
    # Inizializzazione dello stato per i campi se non esistono
    if "titolo_auto" not in st.session_state:
        st.session_state.titolo_auto = ""
    if "categoria_auto" not in st.session_state:
        st.session_state.categoria_auto = "Primi piatti"
    if "ingredienti_auto" not in st.session_state:
        st.session_state.ingredienti_auto = ""
    if "istruzioni_auto" not in st.session_state:
        st.session_state.istruzioni_auto = ""

    # SEZIONE IA PER ANALISI TESTO O FOTO
    st.subheader("🤖 Genera o Formattta con l'IA")
    st.write("Puoi scrivere la ricetta in modo grezzo oppure caricare un'immagine/foto di una ricetta per compilarla in automatico!")

    testo_grezzo = st.text_area("Inserisci testo grezzo della ricetta (opzionale)")
    
    # Opzione per scattare una foto o caricare dalla galleria
    fonte_immagine = st.radio("Metodo inserimento foto", ["Disattivo", "Galleria / File", "Fotocamera"], horizontal=True)
    
    immagine_caricata = None
    if fonte_immagine == "Galleria / File":
        immagine_caricata = st.file_uploader("Scegli un'immagine dalla galleria", type=["jpg", "jpeg", "png", "webp"])
    elif fonte_immagine == "Fotocamera":
        immagine_caricata = st.camera_input("Scatta una foto della ricetta")

    if st.button("✨ Formatta / Estrai con IA"):
        if model is None:
            st.error("La chiave API di Gemini non è configurata correttamente nei Secrets.")
        elif not testo_grezzo.strip() and immagine_caricata is None:
            st.warning("Per favore, inserisci del testo o carica un'immagine prima di cliccare.")
        else:
            with st.spinner("L'IA sta elaborando la ricetta..."):
                try:
                    prompt_sistema = """
                    Analizza il contenuto fornito (testo o immagine) ed estrai/formatta la ricetta.
                    Rispondi ESCLUSIVAMENTE in formato JSON valido con la seguente struttura esatta:
                    {
                      "title": "Titolo chiaro e formattato",
                      "category": "Una tra queste: Salse fredde, Salse calde, Primi piatti, Secondi piatti, Primi piatti caldi, Primi piatti freddi, Dolci, Contorni",
                      "ingredients": "- Ingrediente 1\\n- Ingrediente 2",
                      "instructions": "1. Primo passaggio...\\n2. Secondo passaggio..."
                    }
                    Non aggiungere altro testo prima o dopo il JSON.
                    """

                    contenuti = [prompt_sistema]
                    if testo_grezzo.strip():
                        contenuti.append(f"Testo grezzo ricetta: {testo_grezzo}")
                    if immagine_caricata is not None:
                        img = Image.open(immagine_caricata)
                        contenuti.append(img)

                    response = model.generate_content(contenuti)
                    testo_risposta = response.text.strip()
                    
                    # Pulizia da blocchi di codice markdown se presenti
                    if testo_risposta.startswith("```json"):
                        testo_risposta = testo_risposta[7:]
                    if testo_risposta.startswith("```"):
                        testo_risposta = testo_risposta[3:]
                    if testo_risposta.endswith("```"):
                        testo_risposta = testo_risposta[:-3]
                    
                    dati_ricetta = json.loads(testo_risposta.strip())

                    # Salviamo i dati formattati nello stato della sessione
                    st.session_state.titolo_auto = dati_ricetta.get("title", "")
                    st.session_state.categoria_auto = dati_ricetta.get("category", "Primi piatti")
                    st.session_state.ingredienti_auto = dati_ricetta.get("ingredients", "")
                    st.session_state.istruzioni_auto = dati_ricetta.get("instructions", "")

                    st.success("Ricetta elaborata con successo! Verifica i campi sottostanti e salva.")
                except Exception as e:
                    st.error(f"Errore durante l'elaborazione dell'IA: {e}")

    st.divider()

    # FORM FINALE PER REVISIONE E SALVATAGGIO
    st.subheader("📝 Modulo Ricetta (Salvataggio in Supabase)")
    
    categorie_disponibili = [
        "Salse fredde", 
        "Salse calde", 
        "Primi piatti", 
        "Secondi piatti", 
        "Primi piatti caldi", 
        "Primi piatti freddi", 
        "Dolci", 
        "Contorni"
    ]
    
    idx_categoria = 0
    if st.session_state.categoria_auto in categorie_disponibili:
        idx_categoria = categorie_disponibili.index(st.session_state.categoria_auto)

    with st.form("form_ricetta"):
        titolo = st.text_input("Titolo della ricetta", value=st.session_state.titolo_auto)
        categoria = st.selectbox("Categoria", categorie_disponibili, index=idx_categoria)
        ingredienti = st.text_area("Ingredienti", value=st.session_state.ingredienti_auto, height=150)
        istruzioni = st.text_area("Istruzioni / Procedimento", value=st.session_state.istruzioni_auto, height=200)
        
        submit_button = st.form_submit_button(label="💾 Salva su Database")
        
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
                    
                    # Reset campi dopo il salvataggio
                    st.session_state.titolo_auto = ""
                    st.session_state.ingredienti_auto = ""
                    st.session_state.istruzioni_auto = ""
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
                        risposta = model.generate_content(f"Agisci come un commis/chef professionista. Rispondi a questa richiesta culinaria: {prompt_utente}")
                        st.markdown("### Risposta dello Chef:")
                        st.write(risposta.text)
                    except Exception as e:
                        st.error(f"Errore nella generazione della risposta: {e}")
            else:
                st.warning("Scrivi una domanda prima di inviare.")
