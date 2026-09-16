import streamlit as st
import pandas as pd
from io import BytesIO
from theme import CB_GREEN_DARK, CB_BLUE, CB_ORANGE, kpi_row, donut_progress

def mostrar_tab_mayor():
    st.header("Cargar mayor contable")
    
    # Uploader de mayor contable
    uploaded_file = st.file_uploader("Sube el archivo Excel del mayor contable", type=["xlsx", "xls"], key="mayor")
    
    df_mayor = None
    if uploaded_file is not None:
        df_mayor = pd.read_excel(uploaded_file)
        df_mayor.columns = df_mayor.columns.str.strip()
        df_mayor = df_mayor.dropna(subset=["Fecha"])

        # --- Cheque (Numero solo para Comprobante == "Cheque propio") ---
        df_mayor["Cheque"] = df_mayor["Numero"].where(df_mayor["Comprobante"] == "Cheque propio", "")

        st.subheader("Vista previa del mayor contable")
        st.dataframe(df_mayor.head(20))
        st.caption(f"Columnas: {list(df_mayor.columns)}")
    
    st.markdown("---")
    st.header("Cargar operaciones diarias (Tesorería)")

    uploaded_cheques = st.file_uploader("Sube el archivo Excel de Operaciones Diarias", type=["xlsx", "xls"], key="cheques")
    df_cheques = None
    if uploaded_cheques is not None and df_mayor is not None:
        df_cheques = pd.read_excel(uploaded_cheques)
        df_cheques = df_cheques[df_cheques["Comprobante"] == "1Boleta Deposito"]

        fechas_mayor = df_mayor.loc[df_mayor["Comprobante"] == "1Boleta Deposito", "Fecha"].unique()
        df_cheques = df_cheques[df_cheques["Fecha"].isin(fechas_mayor)]

        df_cheques = df_cheques[["Numero", "Egreso", "Documento"]]

        st.subheader("Vista previa de boletas de depósito")
        st.dataframe(df_cheques.head(20))
    
    st.markdown("---")
    st.header("Cargar listado de proveedores")
    
    uploaded_prov = st.file_uploader("Sube el archivo Excel de proveedores", type=["xlsx", "xls"], key="proveedores")
    
    if uploaded_prov is not None and df_mayor is not None:
        df_prov = pd.read_excel(uploaded_prov)
        columnas_necesarias = ["ProveedorCodigo", "ProveedorRazonSocial", "Cuit"]
        df_prov = df_prov[columnas_necesarias]
        df_prov["Cuit"] = df_prov["Cuit"].astype(str).str.replace("-", "", regex=False)
        
        st.subheader("Vista previa de proveedores")
        st.dataframe(df_prov.head(20))
        
        dict_prov = dict(zip(df_prov["ProveedorRazonSocial"], df_prov["Cuit"]))
        df_mayor["CUIT Proveedor"] = df_mayor["Razon_Social"].map(dict_prov).fillna("")
    
    st.markdown("---")
    st.header("Cargar IVA Ventas")

    uploaded_cli = st.file_uploader("Sube el archivo Excel de IVA Ventas", type=["xlsx", "xls"], key="iva_ventas")

    if uploaded_cli is not None and df_mayor is not None:
        df_cli = pd.read_excel(uploaded_cli)
        columnas_necesarias = ["Razón Social", "CUIT"]
        df_cli = df_cli[columnas_necesarias]
        df_cli["CUIT"] = df_cli["CUIT"].astype(str).str.replace("-", "", regex=False)

        st.subheader("Vista previa de IVA Ventas")
        st.dataframe(df_cli.head(20))

        dict_cli = dict(zip(df_cli["Razón Social"], df_cli["CUIT"]))
        df_mayor["CUIT Cliente"] = df_mayor["Razon_Social"].map(dict_cli).fillna("")
    
    # 🔗 Cruce con cheques depositados
    if df_mayor is not None and df_cheques is not None:
        st.markdown("### 🔗 Cruce con cheques depositados")
        
        nuevos_movimientos = []
        
        for idx, row in df_mayor[df_mayor["Comprobante"] == "1Boleta Deposito"].iterrows():
            numero_mayor = row["Numero"]
            numero_mayor_str = str(int(numero_mayor)) if pd.notna(numero_mayor) else ""  # 🔥 elimina .0

            # Buscar coincidencias con cheques
            cheques_match = df_cheques[df_cheques["Numero"] == numero_mayor]

            if not cheques_match.empty:
                # Modificar debe a 0
                df_mayor.at[idx, "Debe"] = 0

                # Crear nuevas filas
                for _, chq in cheques_match.iterrows():
                    nuevo = {col: "" for col in df_mayor.columns}  # columnas vacías por defecto
                    nuevo["Fecha"] = row["Fecha"]
                    nuevo["Cheque"] = pd.to_numeric(chq["Documento"], errors="coerce")
                    nuevo["Concepto"] = f"Cheque Depositado {numero_mayor_str}"  # ✅ sin .0
                    nuevo["Debe"] = chq["Egreso"]
                    nuevos_movimientos.append(nuevo)
        
        if nuevos_movimientos:
            df_mayor = pd.concat([df_mayor, pd.DataFrame(nuevos_movimientos)], ignore_index=True)
        
        st.subheader("Mayor contable actualizado con cheques depositados")
        st.dataframe(df_mayor.tail(20))  # mostramos los últimos movimientos
    
    # 🔗 Crear columna unificada CUIT (robusta)
    if df_mayor is not None:
        cuit_prov = df_mayor["CUIT Proveedor"] if "CUIT Proveedor" in df_mayor.columns else pd.Series("", index=df_mayor.index)
        cuit_cli = df_mayor["CUIT Cliente"] if "CUIT Cliente" in df_mayor.columns else pd.Series("", index=df_mayor.index)
        df_mayor["CUIT"] = cuit_prov.replace("", pd.NA).fillna(cuit_cli).fillna("")
        df_mayor["CUIT"] = pd.to_numeric(df_mayor["CUIT"], errors="coerce").astype(float).fillna("")

        # --- Movimiento (Debe - Haber) ---
        df_mayor["Movimiento"] = pd.to_numeric(df_mayor["Debe"], errors="coerce").fillna(0) - pd.to_numeric(df_mayor["Haber"], errors="coerce").fillna(0)


    # 📥 Exportar mayor final
    if df_mayor is not None:
        cuits_identificados = (df_mayor["CUIT"] != "").sum() if "CUIT" in df_mayor.columns else 0
        cheques_identificados = (df_mayor["Cheque"] != "").sum() if "Cheque" in df_mayor.columns else 0
        pct_cuit = 100.0 * cuits_identificados / len(df_mayor) if len(df_mayor) else 0.0

        kpi_row([
            {"label": "Filas del mayor", "value": f"{len(df_mayor)}", "color": CB_BLUE},
            {"label": "CUIT identificados", "value": f"{cuits_identificados}", "color": CB_GREEN_DARK},
            {"label": "Cheques identificados", "value": f"{cheques_identificados}", "color": CB_BLUE},
            {"label": "Total Movimiento", "value": f"${df_mayor['Movimiento'].sum():,.2f}", "color": CB_ORANGE},
        ])
        donut_progress(pct_cuit, "Filas con CUIT identificado")

        st.subheader("📊 Mayor contable final con CUIT unificado")
        st.dataframe(df_mayor.head(20))
        
        def to_excel_mayor(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Mayor")
            return output.getvalue()
        
        st.download_button(
            label="📥 Descargar Mayor procesado",
            data=to_excel_mayor(df_mayor),
            file_name="mayor_procesado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
