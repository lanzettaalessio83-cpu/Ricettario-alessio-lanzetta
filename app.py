with tab1:
    st.subheader("📖 Consulta il tuo Ricettario Personale")
    
    if len(st.session_state.ricette) == 0:
        st.info("Il tuo ricettario è ancora vuoto. Aggiungi la tua prima ricetta dal tab a fianco!")
    else:
        categorie_presenti = list(set(r["categoria"] for r in st.session_state.ricette))
        filtro_cat = st.selectbox("Filtra per categoria", ["Tutte"] + categorie_presenti)
        
        for idx, r in enumerate(st.session_state.ricette):
            if filtro_cat == "Tutte" or r["categoria"] == filtro_cat:
                with st.expander(f"📌 {r['titolo']} ({r['categoria']})"):
                    st.markdown(f"**Categoria:** {r['categoria']}")
                    st.markdown("### 🛒 Ingredienti")
                    st.text(r['ingredienti'])
                    st.markdown("### 🍳 Procedimento")
                    st.text(r['procedimento'])
                    
                    if st.button(f"🗑️ Elimina ricetta", key=f"del_{idx}"):
                        st.session_state.ricette.pop(idx)
                        st.rerun()
