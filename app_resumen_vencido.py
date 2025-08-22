import streamlit as st
import pandas as pd
from io import BytesIO
#
def format_currency(x):
    """Format number as Argentine peso currency"""
    return f"${x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") if x >= 0 else f"(${abs(x):,.0f})".replace(",", "X").replace(".", ",").replace("X", ".")

def fetch_data():
    emitidos = pd.read_csv('data/emitidos_mes_vencido.csv')
    emitidos_excel = emitidos.copy()
    for column in ['Neto', 'IVA']:
        emitidos[column] = emitidos[column].apply(format_currency)
    emitidos_por_empresa = emitidos_excel.groupby(['Empresa']).agg({
        'Neto': 'sum', 
        'IVA': 'sum', 
    }).reset_index()
    emitidos_por_empresa = emitidos_por_empresa.sort_values('Neto', ascending=False)
    emitidos_por_empresa_excel = emitidos_por_empresa.copy()
    for column in ['Neto', 'IVA']:
        emitidos_por_empresa[column] = emitidos_por_empresa[column].apply(format_currency)

    recibidos = pd.read_csv('data/recibidos_mes_vencido.csv')
    recibidos_excel = recibidos.copy()
    for column in ['Neto', 'IVA']:
        recibidos[column] = recibidos[column].apply(format_currency)
    recibidos_por_empresa = recibidos_excel.groupby('Empresa').agg({
        'Neto': 'sum', 
        'IVA': 'sum', 
    }).reset_index()
    recibidos_por_empresa = recibidos_por_empresa.sort_values('Neto', ascending=False)
    recibidos_por_empresa_excel = recibidos_por_empresa.copy()
    for column in ['Neto', 'IVA']:
        recibidos_por_empresa[column] = recibidos_por_empresa[column].apply(format_currency)

    resumen_contable = pd.read_csv('data/resumen_contable_mes_vencido.csv')
    for column in ['Ventas Netas', 'Compras Netas', 'IVA Ventas', 'IVA Compras', 'Saldo IVA']:
        resumen_contable[column] = resumen_contable[column].apply(format_currency)
    resumen_contable_excel = pd.read_csv('data/resumen_contable_mes_vencido.csv')

    return (
        emitidos, recibidos, resumen_contable, emitidos_por_empresa, recibidos_por_empresa,
        emitidos_excel, recibidos_excel, resumen_contable_excel, emitidos_por_empresa_excel, recibidos_por_empresa_excel
    )

def to_excel_multiple_sheets(resumen_contable_excel, emitidos_excel, recibidos_excel, emitidos_por_empresa_excel, recibidos_por_empresa_excel):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # Write each dataframe to a different worksheet
    resumen_contable_excel.to_excel(writer, sheet_name='Resumen Contable', index=False)
    emitidos_por_empresa_excel.to_excel(writer, sheet_name='Emitidos por Empresa', index=False)
    recibidos_por_empresa_excel.to_excel(writer, sheet_name='Recibidos por Empresa', index=False)
    emitidos_excel.to_excel(writer, sheet_name='Detalle Emitidos', index=False)
    recibidos_excel.to_excel(writer, sheet_name='Detalle Recibidos', index=False)
    
    # Close the Pandas Excel writer and output the Excel file
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def show_page():
    st.title("Resumen Contable - Mes Vencido (Julio 2025)")
    #st.info("En construcción")
    # Get both formatted data (for display) and raw data (for Excel)
    (
        emitidos, recibidos, resumen_contable, emitidos_por_empresa, recibidos_por_empresa,
        emitidos_excel, recibidos_excel, resumen_contable_excel, emitidos_por_empresa_excel, recibidos_por_empresa_excel
    ) = fetch_data()

    col_title, col_download = st.columns([3, 1])

    
    # Use st.metric for a more visually appealing summary
    st.subheader("Resumen Contable")
    resumen_row = resumen_contable.iloc[0]
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Ventas Netas", resumen_row["Ventas Netas"])
    col2.metric("Compras Netas", resumen_row["Compras Netas"])
    col3.metric("IVA Ventas", resumen_row["IVA Ventas"])
    col4.metric("IVA Compras", resumen_row["IVA Compras"])
    col5.metric("Saldo IVA", resumen_row["Saldo IVA"])

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.header("Comprobantes AFIP")
        st.write("Información descargada desde el sitio de 'Mis Comprobantes' de la AFIP.")
    with col2:
        # Now that razon_social is defined, we can add the download button
        with col_download:
            st.image("data/logo.png")
            # No filtering, just use the full dataframes
            st.download_button(
                label="Descargar informe en Excel",
                data=to_excel_multiple_sheets(
                    resumen_contable_excel,
                    emitidos_excel,
                    recibidos_excel,
                    emitidos_por_empresa_excel,
                    recibidos_por_empresa_excel
                ),
                file_name="resumen_contable_completo.xlsx")
       
    # Removed all filtering by razon_social

    # Show tables with standard styling
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Total mensual Emitidos por Cliente")
        with st.container():
            st.dataframe(emitidos_por_empresa, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Total mensual Recibidos por Proveedor")
        with st.container():
            st.dataframe(recibidos_por_empresa, use_container_width=True, hide_index=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Detalle Comprobantes Emitidos")
        with st.container():
            st.dataframe(emitidos, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Detalle Comprobantes Recibidos")
        with st.container():
            st.dataframe(recibidos, use_container_width=True, hide_index=True)
    with col1:
        st.subheader("Total mensual Emitidos por Cliente")
        with st.container():
            st.dataframe(emitidos_por_empresa, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Total mensual Recibidos por Proveedor")
        with st.container():
            st.dataframe(recibidos_por_empresa, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Detalle Comprobantes Emitidos")
        with st.container():
            st.dataframe(emitidos, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Detalle Comprobantes Recibidos")
        with st.container():
            st.dataframe(recibidos, use_container_width=True, hide_index=True)
