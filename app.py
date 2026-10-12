import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os

# ==============================================================================
# 🎨 PERSONALIZZA QUI TITOLO E ICONE
# ==============================================================================
TITOLO_APP = "ricettario personale alessio🔪📒"
ICONA_PAGINA = "Logo.jpg"    # Icona visibile nella scheda del browser (punta all'immagine caricata)
ICONA_TITOLO = ""      # Icona visibile accanto al titolo (già presente nel titolo)
# ==============================================================================

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title=TITOLO_APP,
    page_icon=ICONA_PAGINA,
    layout="wide"
)

# Configurazione della barra laterale con il logo
with st.sidebar:
    if os.path.exists("Logo.jpg"):
        st.image("Logo.jpg", use_container_width=True)
    st.markdown("---")

# Configurazione della chiave API di Gemini dai Secrets di Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Chiave GEMINI_API_KEY non trovata nei secrets di Streamlit!")

# File per la persistenza dei dati
FILE_RICETTE = "ricette.json"

def carica_ricette():
    if os.path.exists(FILE_RICETTE):
        try:
            with open(FILE_RICETTE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def salva_ricette(ricette):
    try:
        with open(FILE_RICETTE, "w", encoding="utf-8") as f:
            json.dump(ricette, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Errore durante il salvataggio su file: {e}")

# Inizializzazione dello stato con i dati caricati dal file permanente
if "ricette" not in st.session_state:
    st.session_state.ricette = carica_ricette()

# Titolo principale
st.title(f"{TITOLO_APP}")

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
    
    # Stato temporaneo per i campi compilati
    if "temp_titolo" not in st.session_state:
        st.session_state.temp_titolo = ""
    if "temp_categoria" not in st.session_state:
        st.session_state.temp_categoria = "Primi piatti"
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
                        "Analizza la ricetta e restituisci la risposta divisa esattamente in questo formato:\n"
                        "TITOLO: [Nome della ricetta]\n"
                        "CATEGORIA: [Scegli tra: Salse fredde, Salse calde, Primi piatti, Secondi piatti, Dolci, Contorni, Antipasti]\n"
                        "INGREDIENTI:\n[Elenco ingredienti]\n"
                        "PROCEDIMENTO:\n[Passaggi del procedimento]"
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
        ["Salse fredde", "Salse calde", "Primi piatti", "Secondi piatti", "Dolci", "Contorni", "Antipasti"],
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
            st.success(f"🎉 Ricetta '{titolo}' salvata con successo e memorizzata in modo permanente!")
            st.session_state.temp_titolo = ""
            st.session_state.temp_ingredienti = ""
            st.session_state.temp_procedimento = ""

with tab1:
    st.subheader("📖 Consulta il tuo Ricettario Personale")
    
    if len(st.session_state.ricette) == 0:
        st.info("Il tuo ricettario è ancora vuoto. Aggiungi la tua prima ricetta dal tab a fianco!")
    else:
        # Aggiunta della barra di ricerca e del filtro per categoria affiancati
        col1, col2 = st.columns([2, 1])
        with col1:
            ricerca_query = st.text_input("🔍 Cerca ricetta (per nome o ingrediente):", "").lower()
        with col2:
            categorie_presenti = list(set(r["categoria"] for r in st.session_state.ricette))
            filtro_cat = st.selectbox("Filtra per categoria", ["Tutte"] + categorie_presenti)
        
        # Filtriamo le ricette in base alla ricerca e alla categoria selezionata
        ricette_filtrate = []
        for r in st.session_state.ricette:
            match_categoria = (filtro_cat == "Tutte" or r["categoria"] == filtro_cat)
            match_query = (
                ricerca_query in r["titolo"].lower() or 
                ricerca_query in r["ingredienti"].lower() or 
                ricerca_query in r["procedimento"].lower()
            )
            if match_categoria and match_query:
                ricette_filtrate.append(r)
        
        if len(ricette_filtrate) == 0:
            st.warning("Nessuna ricetta corrisponde alla ricerca o al filtro selezionato.")
        else:
            for idx, r in enumerate(st.session_state.ricette):
                # Mostriamo solo quelle che passano il filtro
                if r in ricette_filtrate:
                    with st.expander(f"📌 {r['titolo']} ({r['categoria']})"):
                        st.markdown(f"**Categoria:** {r['categoria']}")
                        st.markdown("### 🛒 Ingredienti")
                        st.text(r['ingredienti'])
                        st.markdown("### 🍳 Procedimento")
                        st.text(r['procedimento'])
                        
                        if st.button(f"🗑️ Elimina ricetta", key=f"del_{idx}"):
                            st.session_state.ricette.pop(idx)
                            salva_ricette(st.session_state.ricette)
                            st.rerun()
