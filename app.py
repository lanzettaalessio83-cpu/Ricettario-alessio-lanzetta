import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os

# ==============================================================================
# 🎨 CONFIGURAZIONE PAGINA
# ==============================================================================
st.set_page_config(
    page_title="Ricettario - Alessio Lanzetta",
    page_icon="📖",
    layout="wide"
)

# Gestione del logo nella barra laterale
with st.sidebar:
    for nome_file in ["favicon.jpg", "Logo.jpg", "logo.jpg", "logo.png"]:
        if os.path.exists(nome_file):
            try:
                st.image(nome_file, use_container_width=True)
                break
            except Exception:
                pass
    st.markdown("---")

# Configurazione API Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Chiave GEMINI_API_KEY non trovata nei secrets di Streamlit!")

FILE_RICETTE = "ricette.json"

# Le tue ricette base garantite
RICETTE_BASE = [
    {
        "titolo": "Crema di parmigiano 46 mesi",
        "categoria": "Salse calde",
        "ingredienti": "Parmigiano Reggiano 46 mesi, panna fresca / latte, pepe nero q.b.",
        "procedimento": "Sciogliere a bagnomaria o a fuoco bassissimo il Parmigiano grattugiato finemente con la panna, frullare fino ad ottenere una crema liscia ed omogenea."
    },
    {
        "titolo": "Maionese all'aneto",
        "categoria": "Salse fredde",
        "ingredienti": "Tuorli, olio di semi, aneto fresco tritato, succo di limone, sale",
        "procedimento": "Emulsionare i tuorli montando a filo con l'olio di semi. Aggiungere il succo di limone, il sale e infine l'aneto fresco tritato finemente."
    },
    {
        "titolo": "Spuma di patate e provola",
        "categoria": "Salse calde",
        "ingredienti": "Patate lesse, provola affumicata, latte/panna, burro, sale e pepe",
        "procedimento": "Schiacciare le patate calde, sciogliere la provola nel latte caldo e unire il tutto. Frullare e passare al sifone con carica per spuma calda."
    }
]

def carica_ricette():
    ricette_salvate = []
    if os.path.exists(FILE_RICETTE):
        try:
            with open(FILE_RICETTE, "r", encoding="utf-8") as f:
                dati = json.load(f)
                if isinstance(dati, list):
                    ricette_salvate = dati
        except Exception:
            pass

    # Uniamo le ricette base con quelle già presenti nel file senza creare duplicati
    titoli_esistenti = [r.get("titolo", "").lower() for r in ricette_salvate]
    for r_base in RICETTE_BASE:
        if r_base["titolo"].lower() not in titoli_esistenti:
            ricette_salvate.append(r_base)

    salva_ricette(ricette_salvate)
    return ricette_salvate

def salva_ricette(ricette):
    try:
        with open(FILE_RICETTE, "w", encoding="utf-8") as f:
            json.dump(ricette, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Errore durante il salvataggio su file: {e}")

# Inizializzazione dello stato
if "ricette" not in st.session_state:
    st.session_state.ricette = carica_ricette()

# Titolo principale
st.title("Ricettario Personale Alessio Lanzetta 🔪📒")

# Lista completa delle categorie aggiornata
LISTA_CATEGORIE = [
    "Fondi", 
    "Brodi", 
    "Verdure", 
    "Carne", 
    "Pesce", 
    "Base", 
    "Salse fredde", 
    "Salse calde", 
    "Primi piatti", 
    "Secondi piatti", 
    "Dolci", 
    "Contorni", 
    "Antipasti"
]

# Menu a schede
tab1, tab2 = st.tabs(["📖 Il mio Ricettario", "✨ Aggiungi / Modifica Ricetta"])

with tab2:
    st.subheader("Inserisci o compila una ricetta con l'IA")
    
    st.markdown("### 🤖 Assistente IA (Opzionale)")
    scelta_foto = st.radio("Vuoi usare una foto per farti aiutare dall'IA?", ["No", "Galleria / File", "Fotocamera"], horizontal=True)
    
    immagine_caricata = None
    if scelta_foto == "Galleria / File":
        immagine_caricata = st.file_uploader("Carica l'immagine della ricetta", type=["jpg", "jpeg", "png"])
    elif scelta_foto == "Fotocamera":
        immagine_caricata = st.camera_input("Scatta una foto alla ricetta")
        
    testo_input_ia = st.text_area("Oppure scrivi due righe o incolla un testo da far sistemare all'IA:")
    
    if "temp_titolo" not in st.session_state:
        st.session_state.temp_titolo = ""
    if "temp_categoria" not in st.session_state:
        st.session_state.temp_categoria = "Fondi"
    if "temp_ingredienti" not in st.session_state:
        st.session_state.temp_ingredienti = ""
    if "temp_procedimento" not in st.session_state:
        st.session_state.temp_procedimento = ""

    if st.button("✨ Elabora con IA e Compila i campi sotto"):
        if not immagine_caricata and not testo_input_ia.strip():
            st.warning("⚠️ Carica un'immagine o inserisci del testo prima di avviare l'elaborazione IA.")
        else:
            try:
                with st.spinner("L'intelligenza artificiale sta analizzando la ricetta..."):
                    model = genai.GenerativeModel('gemini-3.8-flash')
                    prompt = (
                        f"Analizza la ricetta e restituisci la risposta divisa esattamente in questo formato:\n"
                        f"TITOLO: [Nome della ricetta]\n"
                        f"CATEGORIA: [Scegli una tra queste: {', and '.join(LISTA_CATEGORIE)}]\n"
                        f"INGREDIENTI:\n[Elenco ingredienti]\n"
                        f"PROCEDIMENTO:\n[Passaggi del procedimento]"
                    )
                    
                    if immagine_caricata:
                        img = Image.open(immagine_caricata)
                        response = model.generate_content([prompt, img])
                    else:
                        response = model.generate_content(f"{prompt}\n\nTesto:\n{testo_input_ia}")
                    
                    testo_risposta = response.text
                    st.success("✅ Dati estratti con successo! Controlla e modifica i campi qui sotto prima di salvare.")
                    
                    st.session_state.temp_titolo = testo_risposta.split("TITOLO:")[-1].split("CATEGORIA:")[0].strip() if "TITOLO:" in testo_risposta else ""
                    st.session_state.temp_ingredienti = testo_risposta.split("INGREDIENTI:")[-1].split("PROCEDIMENTO:")[0].strip() if "INGREDIENTI:" in testo_risposta else ""
                    st.session_state.temp_procedimento = testo_risposta.split("PROCEDIMENTO:")[-1].strip() if "PROCEDIMENTO:" in testo_risposta else testo_risposta
            except Exception as e:
                st.error(f"Errore durante l'elaborazione IA: {e}")

    st.markdown("---")
    st.subheader("✏️ Dettagli della Ricetta (Modificabili a mano)")
    
    titolo = st.text_input("Titolo della Ricetta", value=st.session_state.temp_titolo)
    categoria = st.selectbox(
        "Categoria", 
        LISTA_CATEGORIE,
        index=0
    )
    ingredienti = st.text_area("Ingredienti (modificabili liberamente)", value=st.session_state.temp_ingredienti, height=150)
    procedimento = st.text_area("Procedimento (modificabile liberamente)", value=st.session_state.temp_procedimento, height=200)

    if st.button("💾 Salva nel Ricettario"):
        if titolo.strip() == "":
            st.error("⚠️ Inserisci un titolo per poter salvare la ricetta.")
        else:
            nuova_ricetta = {
                "titolo": titolo,
                "categoria": categoria,
                "ingredienti": ingredienti,
                "procedimento": procedimento
            }
            st.session_state.ricette.append(nuova_ricetta)
            salva_ricette(st.session_state.ricette)
            st.success(f"🎉 Ricetta '{titolo}' salvata con successo!")
            st.session_state.temp_titolo = ""
            st.session_state.temp_ingredienti = ""
            st.session_state.temp_procedimento = ""

with tab1:
    st.subheader("📖 Consulta il tuo Ricettario Personale")
    
    ricette_correnti = st.session_state.ricette
    
    if len(ricette_correnti) == 0:
        st.info("Il ricettario è vuoto.")
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            ricerca_query = st.text_input("🔍 Cerca ricetta (per nome o ingrediente):", "").lower()
        with col2:
            categorie_presenti = list(set(r.get("categoria", "Altro") for r in ricette_correnti))
            # Mostriamo nel filtro le categorie presenti nei dati + l'opzione "Tutte"
            filtro_cat = st.selectbox("Filtra per categoria", ["Tutte"] + sorted(categorie_presenti))
        
        ricette_filtrate = []
        for r in ricette_correnti:
            match_categoria = (filtro_cat == "Tutte" or r.get("categoria") == filtro_cat)
            match_query = (
                ricerca_query in r.get("titolo", "").lower() or 
                ricerca_query in r.get("ingredienti", "").lower() or 
                ricerca_query in r.get("procedimento", "").lower()
            )
            if match_categoria and match_query:
                ricette_filtrate.append(r)
        
        if len(ricette_filtrate) == 0:
            st.warning("Nessuna ricetta corrisponde alla ricerca o al filtro selezionato.")
        else:
            for idx, r in enumerate(ricette_correnti):
                if r in ricette_filtrate:
                    with st.expander(f"📌 {r.get('titolo', 'Senza titolo')} ({r.get('categoria', 'Generale')})"):
                        st.markdown(f"**Categoria:** {r.get('categoria', 'Generale')}")
                        st.markdown("### 🛒 Ingredienti")
                        st.text(r.get('ingredienti', ''))
                        st.markdown("### 🍳 Procedimento")
                        st.text(r.get('procedimento', ''))
                        
                        if st.button(f"🗑️ Elimina ricetta", key=f"del_{idx}"):
                            ricette_correnti.pop(idx)
                            st.session_state.ricette = ricette_correnti
                            salva_ricette(ricette_correnti)
                            st.rerun()
