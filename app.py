import streamlit as st
import google.generativeai as genai
from PIL import Image

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Ricettario alessio",
    page_icon="🍳",
    layout="wide"
)

# Configurazione della chiave API di Gemini dai Secrets di Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Chiave GEMINI_API_KEY non trovata nei secrets di Streamlit!")

# Inizializzazione dello stato per memorizzare le ricette nella sessione
if "ricette" not in st.session_state:
    st.session_state.ricette = []

st.title("🍳 Ricettario alessio")

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
                    # Modello aggiornato a gemini-2.5-flash
                    model = genai.GenerativeModel('gemini-2.5-flash')
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
            st.success(f"🎉 Ricetta '{titolo}' salvata con successo nel tuo ricettario!")
            st.session_state.temp_titolo = ""
            st.session_state.temp_ingredienti = ""
            st.session_state.temp_procedimento = ""

with tab1:
    st.subheader("📖 Consulta il tuo Ricettario Personale")
    
    if len(st.session_state.ricette) == 0:
        st.info("Il tuo ricettario è ancora vuoto. Aggiungi la tua prima ricetta dal tab a fianco!")
    else:
        categorie_presenti = list(set(r["categoria"] for r in st.session_state.ricette))
        filtro_cat = st.selectbox("Filtra per categoria", ["Tutte"] + categorie_presenti)
        
        for idx, r in enumerate(st.session_state.ricette):
            if filtro_cat == "T
