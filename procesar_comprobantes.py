
import os
import pandas as pd
import zipfile
import re

raw_dir = 'data\\raw'
files = os.listdir(raw_dir)

#Descomprime archivos
csv_files = os.listdir(raw_dir)
csv_files_zip = [file for file in csv_files if file.endswith('.zip')]
for zip_file in csv_files_zip:
    zip_path = os.path.join(raw_dir, zip_file)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(raw_dir)
        print(f'Extracted: {zip_file} into {raw_dir}')

#Procesa CSV descomprimidos
csv_files = os.listdir(raw_dir)
csv_files = [file for file in csv_files if file.endswith('.csv')]
comprobantes_dfs = []
error_log = []  # List to store problematic files
for csv_file in csv_files:
    try:
        # Try reading with default engine, fallback to python engine if error
        try:
            data = pd.read_csv(
                os.path.join(raw_dir, csv_file),
                sep=";",
                on_bad_lines='skip'  # Skip bad lines
            )
        except pd.errors.ParserError:
            data = pd.read_csv(
                os.path.join(raw_dir, csv_file),
                sep=";",
                engine="python",
                on_bad_lines='skip'  # Skip bad lines
            )
        # No company matching, just keep the data flow
        if 'emitidos' in csv_file.lower():
            data['Base'] = 'Emitidos'
        elif 'recibidos' in csv_file.lower():
            data['Base'] = 'Recibidos'
        comprobantes_dfs.append(data)
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        error_log.append(csv_file)

# Log problematic files to a text file for further inspection
if error_log:
    with open('data/error_log.txt', 'w') as log_file:
        log_file.write("\n".join(error_log))

comprobantes = pd.concat(comprobantes_dfs, ignore_index=True)
comprobantes['Empresa'] = comprobantes['Denominación Receptor'].fillna(comprobantes['Denominación Emisor']).str.strip().str.title().fillna("-")

def format_number(x):
    return str(x).replace(",", ".") if pd.notnull(x) else x

for column in ['Imp. Neto Gravado', 'Imp. Neto No Gravado', 'Imp. Op. Exentas', 'IVA', 'Tipo Cambio', 'Imp. Total']:
    comprobantes[column] = comprobantes[column].apply(format_number).astype(float).fillna(0).round(0).astype(int)
comprobantes['Neto'] = comprobantes['Imp. Neto Gravado'] + comprobantes['Imp. Neto No Gravado'] + comprobantes['Imp. Op. Exentas'] 

comprobantes = comprobantes[['Fecha de Emisión', 'Base', 'Tipo de Comprobante', 
    'Número Desde', 'Tipo Cambio', 'Moneda', 'Imp. Neto Gravado', 'Imp. Neto No Gravado',
    'Imp. Op. Exentas', 'IVA', 'Imp. Total', 'Empresa']]

# Notas de credito
comprobantes.loc[comprobantes['Tipo de Comprobante'] == 3, ['Imp. Neto Gravado', 'Imp. Neto No Gravado', 'Imp. Op. Exentas', 'IVA']] *= -1
comprobantes.loc[comprobantes['Tipo de Comprobante'] == 8, ['Imp. Neto Gravado', 'Imp. Neto No Gravado', 'Imp. Op. Exentas', 'IVA']] *= -1
# Factura C
comprobantes.loc[comprobantes['Tipo de Comprobante'] == 11, 'Imp. Neto No Gravado'] = comprobantes.loc[comprobantes['Tipo de Comprobante'] == 11, 'Imp. Total']

for column in ['Imp. Neto Gravado', 'Imp. Neto No Gravado', 'Imp. Op. Exentas', 'IVA']:
    comprobantes.loc[comprobantes['Moneda'].str.contains('USD|DOL'), column] *= comprobantes.loc[comprobantes['Moneda'].str.contains('USD|DOL'), 'Tipo Cambio']

comprobantes['Neto'] = comprobantes['Imp. Neto Gravado'] + comprobantes['Imp. Neto No Gravado'] + comprobantes['Imp. Op. Exentas']

comprobantes['Empresa'] = comprobantes['Empresa'].fillna("-")

# Normaliza fechas con formato DD/MM/YYYY o D/M/YYYY a YYYY-MM-DD
def normalize_fecha_emision(fecha):
    if pd.isnull(fecha):
        return fecha
    # Si ya está en formato YYYY-MM-DD, no cambia
    if re.match(r'^\d{4}-\d{2}-\d{2}$', str(fecha)):
        return fecha
    # Si está en formato D/M/YYYY o DD/MM/YYYY
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', str(fecha))
    if match:
        d, m, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    return fecha

comprobantes['Fecha de Emisión'] = comprobantes['Fecha de Emisión'].apply(normalize_fecha_emision)
comprobantes['Fecha de Emisión'] = pd.to_datetime(comprobantes['Fecha de Emisión'], format='%Y-%m-%d', errors='coerce')
comprobantes['Mes'] = comprobantes['Fecha de Emisión'].dt.strftime('%Y-%m')
comprobantes['Fecha'] = comprobantes['Fecha de Emisión'].dt.strftime('%d/%m/%Y')

codigos_tipos_comprobante = pd.read_excel('codigos_tipos_comprobante.xls')
codigos_tipos_comprobante['Descripción'] = codigos_tipos_comprobante['Descripción'].str.title()
codigos_tipos_comprobante = codigos_tipos_comprobante.rename(columns={'Código': 'Tipo de Comprobante', 'Descripción': 'Tipo'})

# Reemplaza los valores de 'Tipo de Comprobante' por la descripción usando 'Código' como clave
comprobantes = comprobantes.merge(
    codigos_tipos_comprobante,
    on='Tipo de Comprobante',
    how='left'
)

comprobantes = comprobantes[['Fecha', 'Empresa', 'Tipo', 'Número Desde',
        'Imp. Neto Gravado', 'Imp. Neto No Gravado', 'Imp. Op. Exentas', 'IVA',
       'Neto', 'Mes',  'Base']]

comprobantes = comprobantes.rename(columns={
    'Número Desde': 'Nro.',
    'Imp. Neto Gravado': 'Neto Gravado',
    'Imp. Neto No Gravado': 'Neto No Gravado',
    'Imp. Op. Exentas': 'Op. Exentas',})

emitidos_historico = comprobantes[comprobantes['Base'] == 'Emitidos'].drop(columns=['Base'])
recibidos_historico = comprobantes[comprobantes['Base'] == 'Recibidos'].drop(columns=['Base'])

### Sacar datos para graficos

ventas= emitidos_historico.groupby(['Mes']).agg({
    'Neto': 'sum', 
    'IVA': 'sum'
}).reset_index()

ventas_por_cliente = emitidos_historico.groupby(['Empresa', 'Mes']).agg({
    'Neto': 'sum', 
    'IVA': 'sum'
}).reset_index()

compras = recibidos_historico.groupby(['Mes']).agg({
    'Neto': 'sum', 
    'IVA': 'sum'
}).reset_index()

compras_por_proveedor = recibidos_historico.groupby([ 'Empresa', 'Mes']).agg({
    'Neto': 'sum', 
    'IVA': 'sum'
}).reset_index()

comprobantes_historico = ventas.merge(compras, on=['Mes'], how='left', suffixes=(' Ventas', ' Compras'))
# Round and convert numeric columns to integers
numeric_columns = ['Neto Ventas', 'IVA Ventas', 'Neto Compras', 'IVA Compras']
comprobantes_historico[numeric_columns] = comprobantes_historico[numeric_columns].fillna(0).round(0).astype(int)
comprobantes_historico['Saldo IVA'] = comprobantes_historico['IVA Ventas'] - comprobantes_historico['IVA Compras']

# Melt the DataFrame to reshape it
comprobantes_historicos = comprobantes_historico.melt(
    id_vars=['Mes'], 
    value_vars=['Neto Ventas', 'IVA Ventas', 'Neto Compras', 'IVA Compras', 'Saldo IVA'],
    var_name='Variable', 
    value_name='Monto'
)

emitidos_historico.to_csv('data/emitidos_historico.csv', index=False)
recibidos_historico.to_csv('data/recibidos_historico.csv', index=False)
comprobantes_historicos.to_csv('data/comprobantes_historicos.csv', index=False)
ventas.to_csv('data/ventas_historico_mensual.csv', index=False)
compras.to_csv('data/compras_historico_mensual.csv', index=False)
ventas_por_cliente.to_csv('data/ventas_historico_cliente.csv', index=False)
compras_por_proveedor.to_csv('data/compras_historico_proveedor.csv', index=False)


"""
MES PASADO
"""
from datetime import datetime
import pandas as pd
from datetime import datetime, timedelta
today = datetime.today()
first_day_this_month = today.replace(day=1)
last_month = first_day_this_month - timedelta(days=1)
mes = last_month.strftime("%m/%Y")  
print(f"Procesando datos para el mes: {mes}")
#Abro datos

emitidos = emitidos_historico.copy()
emitidos = emitidos[emitidos['Fecha'].str.endswith(mes)]
recibidos = recibidos_historico.copy()
recibidos = recibidos[recibidos['Fecha'].str.endswith(mes)]

emitidos = emitidos[['Fecha', 'Tipo', 'Nro.', 'Empresa', 'Neto', 'IVA']]
emitidos.to_csv('data/emitidos_mes_vencido.csv', index=False)

emitidos_por_empresa = emitidos.groupby(['Empresa']).agg({
    'Neto': 'sum', 
    'IVA': 'sum', 
}).reset_index()
emitidos_por_empresa['Imp. Total'] = emitidos_por_empresa['Neto'] + emitidos_por_empresa['IVA']
emitidos_por_empresa = emitidos_por_empresa.sort_values('Neto', ascending=False)
emitidos_por_empresa.to_csv('data/emitidos_por_empresa_mes_vencido.csv', index=False)

#Recibidos por Proveedor
recibidos['Neto'] = recibidos['Neto Gravado'] + recibidos['Neto No Gravado'] + recibidos['Op. Exentas']
recibidos = recibidos[['Fecha', 'Tipo', 'Nro.', 'Empresa', 'Neto', 'IVA']]
recibidos.to_csv('data/recibidos_mes_vencido.csv', index=False)
recibidos_por_empresa = recibidos.groupby(['Empresa']).agg({
    'Neto': 'sum', 
    'IVA': 'sum', 
}).reset_index()
recibidos_por_empresa['Imp. Total'] = recibidos_por_empresa['Neto'] + recibidos_por_empresa['IVA']
recibidos_por_empresa = recibidos_por_empresa.sort_values('Imp. Total', ascending=False)
recibidos_por_empresa.to_csv('data/recibidos_por_empresa_mes_vencido.csv', index=False)

# Medidas
ventas_netas= emitidos['Neto'].sum()
compras_netas = recibidos['Neto'].sum()
iva_ventas = emitidos['IVA'].sum()
iva_compras = recibidos['IVA'].sum()
saldo_iva = iva_compras - iva_ventas

# Combine all indicators into a single DataFrame
indicators = pd.DataFrame([{
    'Ventas Netas': ventas_netas,
    'Compras Netas': compras_netas,
    'IVA Ventas': iva_ventas,
    'IVA Compras': iva_compras,
    'Saldo IVA': saldo_iva,
}])

indicators.to_csv('data/resumen_contable_mes_vencido.csv', index=False)

with open('data/leyenda_resumen_contable_mes_vencido.txt', 'w', encoding='utf-8') as file:
    file.write(f"Resumen Contable para el mes: {mes}")