import streamlit as st
import pandas as pd
import re
from io import BytesIO
from theme import CB_GREEN_DARK, CB_BLUE, CB_ORANGE, kpi_row, donut_progress

def mostrar_tab_banco():
    st.header("Cargar acreditaciones de valores")

    uploaded_acreditaciones = st.file_uploader("Sube el CSV de acreditaciones de valores", type=["csv"], key="acreditaciones")

    df_acreditaciones = None
    if uploaded_acreditaciones is not None:
        df_acreditaciones = pd.read_csv(uploaded_acreditaciones, sep=";")
        df_acreditaciones = df_acreditaciones[["FECINGCHQ", "FECVALOR", "NROCHEQUE", "IMPORTE"]]
        df_acreditaciones = df_acreditaciones.dropna(how="all")
        df_acreditaciones["FECINGCHQ"] = pd.to_datetime(df_acreditaciones["FECINGCHQ"], format="%Y%m%d", errors="coerce")
        df_acreditaciones["FECVALOR"] = pd.to_datetime(df_acreditaciones["FECVALOR"], format="%Y%m%d", errors="coerce")

        kpi_row([
            {"label": "Acreditaciones", "value": f"{len(df_acreditaciones)}", "color": CB_BLUE},
            {"label": "Importe total", "value": f"${df_acreditaciones['IMPORTE'].sum():,.2f}", "color": CB_GREEN_DARK},
        ])

        st.subheader("Vista previa de acreditaciones de valores")
        st.dataframe(df_acreditaciones.head(20))

        # Exportar con FECINGCHQ y FECVALOR en formato fecha
        def to_excel_acreditaciones(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Acreditaciones")
                workbook = writer.book
                worksheet = writer.sheets["Acreditaciones"]
                date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})
                for col in ["FECINGCHQ", "FECVALOR"]:
                    col_idx = df.columns.get_loc(col)
                    worksheet.set_column(col_idx, col_idx, 12, date_format)
            return output.getvalue()

        st.download_button(
            label="📥 Descargar Excel procesado",
            data=to_excel_acreditaciones(df_acreditaciones),
            file_name="acreditaciones_valores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("---")
    st.header("Cargar movimientos bancarios")

    uploaded_file = st.file_uploader("Sube el archivo Excel con los movimientos", type=["xlsx", "xls"], key="banco")

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df = df.drop(columns=["Unnamed: 0"], errors="ignore")
        df = df.dropna(how="all")
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")

        # --- Extracción de Cheque ---
        def extraer_cheque(row):
            concepto = str(row.get("Concepto", ""))
            combte = row.get("Nro.Cpbte.", None)
            if "Valores" in concepto and "Ch:" in concepto:
                match = re.search(r"Ch:\s*(\d+)", concepto)
                if match:
                    return int(match.group(1))
            if "cheque" in concepto.lower():
                try:
                    return int(combte)
                except (ValueError, TypeError):
                    return None
            return None
        df["Cheque"] = df.apply(extraer_cheque, axis=1)

        # --- Extracción de CUIT ---
        def extraer_cuit(concepto):
            if pd.isna(concepto):
                return None
            match = re.search(r"\b(20\d{9}|23\d{9}|27\d{9}|30\d{9}|33\d{9})\b", str(concepto))
            if match:
                return int(match.group(1))
            return None
        df["CUIT"] = df["Concepto"].apply(extraer_cuit).astype("Int64")

        # --- Movimiento (Crédito - Débito) ---
        df["Movimiento"] = df["Crédito"].fillna(0) - df["Débito"].fillna(0)

        # --- Completado de Cheque con acreditaciones de valores ---
        if df_acreditaciones is not None:
            df = df.reset_index(drop=True)
            mask_valores = df["Cód."].isin(["REGUV", "AVGUV"])
            suma_banco = df.loc[mask_valores, "Movimiento"].sum()
            suma_acreditaciones = df_acreditaciones["IMPORTE"].sum()

            def filas_desde_acreditaciones(acreditaciones):
                filas = []
                for _, row in acreditaciones.iterrows():
                    nuevo = {col: "" for col in df.columns}
                    nuevo["Fecha"] = row["FECVALOR"]
                    nuevo["Movimiento"] = row["IMPORTE"]
                    nuevo["Cheque"] = row["NROCHEQUE"]
                    nuevo["Concepto"] = "Acreditacion de valores" if row["IMPORTE"] > 0 else "Cheque rechazado"
                    filas.append(nuevo)
                return filas

            nuevas_filas = []
            if abs(suma_banco - suma_acreditaciones) < 0.01:
                df.loc[mask_valores, "Movimiento"] = 0
                nuevas_filas = filas_desde_acreditaciones(df_acreditaciones)
            else:
                fechas = sorted(set(df.loc[mask_valores, "Fecha"].dropna()) | set(df_acreditaciones["FECVALOR"].dropna()))
                for fecha in fechas:
                    mask_dia = mask_valores & (df["Fecha"] == fecha)
                    acreditaciones_dia = df_acreditaciones[df_acreditaciones["FECVALOR"] == fecha]
                    suma_banco_dia = df.loc[mask_dia, "Movimiento"].sum()
                    suma_acreditaciones_dia = acreditaciones_dia["IMPORTE"].sum()

                    if abs(suma_banco_dia - suma_acreditaciones_dia) < 0.01:
                        df.loc[mask_dia, "Movimiento"] = 0
                        nuevas_filas.extend(filas_desde_acreditaciones(acreditaciones_dia))
                    else:
                        st.warning(
                            f"⚠️ Diferencia en acreditaciones de valores para el {fecha.strftime('%d/%m/%Y')}: "
                            f"banco {suma_banco_dia:.2f} vs csv {suma_acreditaciones_dia:.2f}"
                        )

            if nuevas_filas:
                df = pd.concat([df, pd.DataFrame(nuevas_filas)], ignore_index=True)
                df = df.sort_values("Fecha", kind="stable").reset_index(drop=True)

        cheques_detectados = df["Cheque"].notna().sum()
        cuits_detectados = df["CUIT"].notna().sum()
        pct_cuit = 100.0 * cuits_detectados / len(df) if len(df) else 0.0

        kpi_row([
            {"label": "Movimientos", "value": f"{len(df)}", "color": CB_BLUE},
            {"label": "Cheques detectados", "value": f"{cheques_detectados}", "color": CB_BLUE},
            {"label": "CUIT identificados", "value": f"{cuits_detectados}", "color": CB_GREEN_DARK},
            {"label": "Total Movimiento", "value": f"${df['Movimiento'].sum():,.2f}", "color": CB_ORANGE},
        ])
        donut_progress(pct_cuit, "Movimientos con CUIT identificado")

        st.dataframe(df.head(20))

        # Exportar con Fecha en formato fecha
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Movimientos")
                workbook = writer.book
                worksheet = writer.sheets["Movimientos"]
                date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})
                fecha_col_idx = df.columns.get_loc("Fecha")
                worksheet.set_column(fecha_col_idx, fecha_col_idx, 12, date_format)
            return output.getvalue()

        st.download_button(
            label="📥 Descargar Excel procesado",
            data=to_excel(df),
            file_name="movimientos_banco.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
