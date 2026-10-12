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
            json.
