import streamlit as st
import pandas as pd
import re
from io import BytesIO

def mostrar_tab_banco():
    st.header("Cargar movimientos bancarios")
    
    uploaded_file = st.file_uploader("Sube el archivo Excel con los movimientos", type=["xlsx", "xls"], key="banco")
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df["FECHA"] = pd.to_datetime(df["FECHA"], format="%m/%d/%Y", errors="coerce")
        
        # --- Extracción de Cheque ---
        def extraer_cheque(row):
            desc = str(row.get("DESCRIPCION", ""))
            combte = row.get("COMBTE", None)
            if "Valores" in desc and "Ch:" in desc:
                match = re.search(r"Ch:\s*(\d+)", desc)
                if match:
                    return int(match.group(1))
            if "cheque" in desc.lower():
                try:
                    return int(combte)
                except (ValueError, TypeError):
                    return None
            return None
        df["Cheque"] = df.apply(extraer_cheque, axis=1)
        
        # --- Extracción de CUIT ---
        def extraer_cuit(desc):
            if pd.isna(desc):
                return None
            match = re.search(r"\b(20\d{9}|23\d{9}|27\d{9}|30\d{9}|33\d{9})\b", str(desc))
            if match:
                return int(match.group(1))
            return None
        df["CUIT"] = df["DESCRIPCION"].apply(extraer_cuit).astype("Int64")
        
        st.dataframe(df.head(20))
        
        # Exportar con FECHA en formato fecha
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Movimientos")
                workbook = writer.book
                worksheet = writer.sheets["Movimientos"]
                date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})
                fecha_col_idx = df.columns.get_loc("FECHA")
                worksheet.set_column(fecha_col_idx, fecha_col_idx, 12, date_format)
            return output.getvalue()
        
        st.download_button(
            label="📥 Descargar Excel procesado",
            data=to_excel(df),
            file_name="movimientos_banco.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
