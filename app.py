import streamlit as st
from tab_banco import mostrar_tab_banco
from tab_mayor import mostrar_tab_mayor

# Título principal
st.title("Conciliación Bancaria")

# Crear tabs
tab1, tab2 = st.tabs(["Archivos de Banco", "Mayor Contable"])

with tab1:
    mostrar_tab_banco()

with tab2:
    mostrar_tab_mayor()
