import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Configuración de Google Sheets ---
def obtener_hoja_de_calculo():
    # Usa las credenciales del archivo de Streamlit Secrets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread_creds"], scope)
    client = gspread.authorize(creds)
    
    # Abre tu hoja de cálculo en Google Sheets (asegúrate de que el archivo ya existe)
    spreadsheet = client.open("Hoja 1")
    worksheet = spreadsheet.sheet1  # O puedes seleccionar otro sheet si es necesario
    return worksheet

# Inicialización de la base de datos en la sesión
if "cartas_db" not in st.session_state:
    st.session_state.cartas_db = pd.DataFrame(columns=[
        "ID", "Trabajador", "Nombre_Carta", "Fecha_Notificación", 
        "Días_Hábiles", "Fecha_Límite", "Estatus", 
        "Fecha_Respuesta", "Número_Carta_Respuesta"
    ])

# Función para calcular la fecha límite (excluye fines de semana)
def calcular_fecha_limite(fecha_inicio, dias_habiles):
    fecha = fecha_inicio
    while dias_habiles > 0:
        fecha += dt.timedelta(days=1)
        if fecha.weekday() < 5:  # Excluye sábados (5) y domingos (6)
            dias_habiles -= 1
    return fecha

# Título principal
st.title("Gestión de Cartas de OSIPTEL")

# --- Sección 1: Ingresar nueva carta ---
st.header("📩 Ingresar Nueva Carta")
with st.form("nueva_carta_form"):
    trabajador = st.selectbox("Responsable", ["Britcia", "Rosaly", "Anderson", "Renato", "Marisol"])
    nombre_carta = st.text_input("Nombre de la Carta")
    fecha_notificacion = st.date_input("Fecha de Notificación")
    dias_habiles = st.number_input("Días Hábiles para Responder", min_value=1, step=1)
    
    if st.form_submit_button("Registrar Carta"):
        fecha_limite = calcular_fecha_limite(fecha_notificacion, dias_habiles)
        nueva_carta = {
            "ID": len(st.session_state.cartas_db) + 1,
            "Trabajador": trabajador,
            "Nombre_Carta": nombre_carta,
            "Fecha_Notificación": fecha_notificacion,
            "Días_Hábiles": dias_habiles,
            "Fecha_Límite": fecha_limite,
            "Estatus": "Pendiente",
            "Fecha_Respuesta": None,
            "Número_Carta_Respuesta": None
        }
        st.session_state.cartas_db = pd.concat(
            [st.session_state.cartas_db, pd.DataFrame([nueva_carta])],
            ignore_index=True
        )

        # Guardar la carta en Google Sheets
        worksheet = obtener_hoja_de_calculo()
        worksheet.append_row([nueva_carta["ID"], nueva_carta["Trabajador"], nueva_carta["Nombre_Carta"],
                              nueva_carta["Fecha_Notificación"].strftime("%Y-%m-%d"), nueva_carta["Días_Hábiles"],
                              nueva_carta["Fecha_Límite"].strftime("%Y-%m-%d"), nueva_carta["Estatus"],
                              nueva_carta["Fecha_Respuesta"], nueva_carta["Número_Carta_Respuesta"]])
        
        st.success("Carta registrada correctamente.")

# --- Sección 2: Actualizar estado ---
st.header("✅ Actualizar Estado de Carta")
if not st.session_state.cartas_db.empty:
    with st.form("actualizar_estado_form"):
        opciones_carta = st.session_state.cartas_db["ID"].astype(str) + " - " + st.session_state.cartas_db["Nombre_Carta"]
        id_carta = st.selectbox("Seleccionar Carta (ID - Nombre)", opciones_carta)
        id_carta = int(id_carta.split(" - ")[0])
        estatus = st.selectbox("Estatus", ["Pendiente", "Atendida"])
        numero_respuesta = st.text_input("Número de Carta de Respuesta (Opcional)")
        fecha_respuesta = st.date_input("Fecha de Respuesta (Opcional)", dt.date.today())
        
        if st.form_submit_button("Actualizar Carta"):
            index = st.session_state.cartas_db.index[st.session_state.cartas_db["ID"] == id_carta][0]
            st.session_state.cartas_db.loc[index, "Estatus"] = estatus
            st.session_state.cartas_db.loc[index, "Número_Carta_Respuesta"] = numero_respuesta
            st.session_state.cartas_db.loc[index, "Fecha_Respuesta"] = fecha_respuesta
            st.success("Carta actualizada correctamente.")
            
            # Guardar los cambios en Google Sheets
            worksheet = obtener_hoja_de_calculo()
            row = worksheet.findall(str(id_carta))[0].row  # Encontrar la fila por ID
            worksheet.update(f"B{row}:I{row}", [[estatus, numero_respuesta, fecha_respuesta]])
else:
    st.warning("No hay cartas registradas para actualizar.")

# --- Sección 3: Visualización ---
st.header("📊 Visualización de Datos")
if not st.session_state.cartas_db.empty:
    # Mostrar tabla completa
    st.subheader("Base de Datos de Cartas")
    st.dataframe(st.session_state.cartas_db)
    
    # Gráfico de evolución de cartas por mes
    st.subheader("Evolución Mensual de Cartas")
    cartas_db = st.session_state.cartas_db.copy()
    cartas_db["Mes"] = pd.to_datetime(cartas_db["Fecha_Notificación"]).dt.to_period("M")
    cartas_por_mes = cartas_db.groupby("Mes").size().reset_index(name="Cantidad")
    fig = px.bar(cartas_por_mes, x="Mes", y="Cantidad", title="Evolución Mensual de Cartas")
    st.plotly_chart(fig)
