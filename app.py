import json
import streamlit as st
from groq import Groq
from supabase import Client, create_client

# Configurazione della pagina
st.set_page_config(
    page_title="Il Mio Ricettario IA",
    page_icon="📖",
    layout="wide"
)

st.title("🍳 Assistente & Ricettario Digitale")

# Lettura delle chiavi segrete da Streamlit Secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# Inizializzazione dei client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# Menu Laterale - Categorie
st.sidebar.header("📁 Reparti Ricettario")
categorie = [
    "Tutte",
    "Salse fredde",
    "Salse calde",
    "Primi piatti",
    "Secondi piatti",
    "Dolci",
    "Contorni",
    "Antipasti"
]
categoria_scelta = st.sidebar.selectbox("Filtra per reparto:", categorie)

# Struttura a tab per l'applicazione
tab_consulta, tab_aggiungi = st.tabs(["📖 Consulta Ricettario", "➕ Aggiungi con IA"])

with tab_aggiungi:
    st.header("Inserisci una ricetta o un appunto grezzo")
    testo_grezzo = st.text_area("Incolla qui i tuoi appunti o il procedimento libero:")

    if st.button("🪄 Elabora e Salva con IA", type="primary"):
        if not testo_grezzo.strip():
            st.warning("Inserisci del testo prima di procedere.")
        else:
            try:
                prompt = f"""
                Analizza il seguente testo grezzo di una ricetta culinaria e strutturalo in formato JSON con le seguenti chiavi esatte:
                - "titolo": nome della ricetta
                - "categoria": una tra Salse fredde, Salse calde, Primi piatti, Secondi piatti, Dolci, Contorni, Antipasti
                - "ingredienti": lista dettagliata degli ingredienti con dosi
                - "procedimento": passaggi ordinati e numerati della preparazione
                - "note_tecniche": eventuali consigli, temperature, attrezzature o note di conservazione.

                Testo di partenza:
                {testo_grezzo}

                Rispondi ESCLUSIVAMENTE con il codice JSON, senza testo aggiuntivo o markdown prima e dopo.
                """

                response = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                )

                # Pulizia risposta JSON
                raw_text = response.choices[0].message.content.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]

                dati = json.loads(raw_text.strip())

                # Inserimento su Supabase
                supabase.table("ricette").insert(dati).execute()
                st.success("Ricetta elaborata e salvata con successo!")

            except Exception as e:
                st.error(f"Errore durante l'elaborazione o il salvataggio: {e}")

with tab_consulta:
    st.header("Elenco Ricette")
    try:
        query = supabase.table("ricette").select("*")
        if categoria_scelta != "Tutte":
            query = query.eq("categoria", categoria_scelta)
        
        response = query.execute()
        ricette = response.data

        if not ricette:
            st.info("Nessuna ricetta trovata in questo reparto.")
        else:
            for r in ricette:
                with st.expander(f"{r.get('titolo', 'Senza titolo')} ({r.get('categoria', 'Generale')})"):
                    st.markdown("**Ingredienti:**")
                    st.write(r.get('ingredienti', ''))
                    st.markdown("**Procedimento:**")
                    st.write(r.get('procedimento', ''))
                    if r.get('note_tecniche'):
                        st.markdown("**Note Tecniche:**")
                        st.write(r.get('note_tecniche'))
    except Exception as e:
        st.error(f"Errore nel caricamento delle ricette da Supabase: {e}"
)

