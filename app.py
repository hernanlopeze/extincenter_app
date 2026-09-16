import streamlit as st
from theme import inject_theme, app_header
from tab_banco import mostrar_tab_banco
from tab_mayor import mostrar_tab_mayor

st.set_page_config(page_title="Pre-Match", page_icon="🔗", layout="wide")
inject_theme()
app_header("Banco + Mayor")

# Crear tabs
tab1, tab2 = st.tabs(["Archivos de Banco", "Mayor Contable"])

with tab1:
    mostrar_tab_banco()

with tab2:
    mostrar_tab_mayor()
