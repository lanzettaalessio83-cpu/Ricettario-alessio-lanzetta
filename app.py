import json
from groq import Groq
import streamlit as st
from supabase import Client, create_client

# Configurazione della pagina
st.set_page_config (
)

    page_title="Il Mio Ricettario IA", layout="wide", page_icon="📒"
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
st.sidebar.header("📂 Reparti Ricettario")
categorie = [
    "Tutte",
    "Salse fredde",
    "Salse calde",
    "Primi piatti caldi",
    "Primi piatti freddi",
    "Secondi piatti",
    "Dolci",
    "Contorni",
]
categoria_scelta = st.sidebar.selectbox("Filtra per Categoria:", categorie)

# Struttura ad Aste (Tab 1: Consultazione | Tab 2: Inserimento)
tab1, tab2 = st.tabs(["📖 Consulta Ricettario", "➕ Aggiungi con IA"])

with tab2:
  st.subheader("Inserisci una ricetta o un appunto grezzo")
  testo_grezzo = st.text_area(
      "Incolla qui i tuoi appunti o il procedimento libero:",
      height=180,
      placeholder=(
          "Es. Ho fatto 500g maionese con 4 tuorli, olio di semi a filo, limone"
          " 20g, sale, montato ad immersione..."
      ),
  )

  if st.button("🪄 Elabora e Salva con IA", type="primary"):
    if testo_grezzo:
      with st.spinner("L'assistente sta organizzando la scheda tecnica..."):
        prompt = f"""
                Sei un assistente di cucina professionale. Prendi il seguente testo ed estrai le informazioni organizzandole in un JSON valido con esattamente queste chiavi:
                "titolo": nome della ricetta,
                "categoria": scegli esattamente una tra ["Salse fredde", "Salse calde", "Primi piatti caldi", "Primi piatti freddi", "Secondi piatti", "Dolci", "Contorni"],
                "ingredienti": elenco dettagliato di ingredienti e grammature/dosi,
                "procedimento": passaggi ordinati e numerati della preparazione,
                "note_tecniche": eventuali consigli, temperature, attrezzature o note di conservazione.

                Testo di partenza: {testo_grezzo}
                Rispondi ESCLUSIVAMENTE con il codice JSON, senza testo aggiuntivo o markdown prima e dopo.
                """

        try:
          response = groq_client.chat.completions.create(
              messages=[{"role": "user", "content": prompt}],
              model="llama-3.3-70b-versatile",
          )

          # Cleaning risposta JSON
          raw_text = response.choices[0].message.content.strip()
          if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
          if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

          dati = json.loads(raw_text.strip())

          # Inserimento su Supabase
          supabase.table("ricette").insert(dati).execute()
          st.success(
              f"✅ Ricetta '{dati['titolo']}' salvata con successo nel reparto"
              f" '{dati['categoria']}'!"
          )
        except Exception as e:
          st.error(f"Errore durante l'elaborazione o il salvataggio: {e}")
    else:
        st.warning("Inserisci prima del testo da elaborare.")

with tab1:
  st.subheader("Le Tue Ricette")

  # Query al database
  if categoria_scelta == "Tutte":
    query = (
        supabase.table("ricette")
        .select("*")
        .order("id", desc=True)
        .execute()
    )
  else:
    query = (
        supabase.table("ricette")
        .select("*")
        .eq("categoria", categoria_scelta)
        .order("id", desc=True)
        .execute()
    )

  ricette = query.data

  if not ricette:
    st.info("Nessuna ricetta trovata in questa sezione.")
  else:
    for r in ricette:
      with st.expander(f"📌 {r['titolo']} — ({r['categoria']})"):
        col1, col2 = st.columns(2)
        with col1:
          st.markdown("**🧂 Ingredienti:**")
          st.write(r["ingredienti"])
        with col2:
          st.markdown("**👨‍🍳 Procedimento:**")
          st.write(r["procedimento"])
        if r.get("note_tecniche"):
          st.info(f"💡 **Note Tecniche:** {r['note_tecniche']}")
