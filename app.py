import streamlit as st
import pandas as pd
import datetime as dt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Función para conectarse a Google Sheets usando las credenciales de Streamlit Secrets
def obtener_hoja_de_calculo():
    # Definir el alcance de la API de Google Sheets y Google Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Usar las credenciales de Streamlit Secrets
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread_creds"], scope)
    client = gspread.authorize(creds)
    
    # Abre la hoja de cálculo de Google Sheets por su ID (en lugar de usar su nombre)
    spreadsheet = client.open_by_key("1Ke5AF0EuMr2Q2QBWym9gQ2lbQ_6-JUknQN9Kdysp86w")
    worksheet = spreadsheet.sheet1  # Accede a la primera hoja
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
        st.success("Carta registrada correctamente.")

        # Guardar en Google Sheets después de registrar la carta
        worksheet = obtener_hoja_de_calculo()
        worksheet.append_row([nueva_carta["ID"], nueva_carta["Trabajador"], nueva_carta["Nombre_Carta"],
                              nueva_carta["Fecha_Notificación"].strftime("%Y-%m-%d"), nueva_carta["Días_Hábiles"],
                              nueva_carta["Fecha_Límite"].strftime("%Y-%m-%d"), nueva_carta["Estatus"],
                              nueva_carta["Fecha_Respuesta"], nueva_carta["Número_Carta_Respuesta"]])

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

            # Actualizar la hoja de Google Sheets
            worksheet = obtener_hoja_de_calculo()
            row = [id_carta, trabajador, nombre_carta, fecha_notificacion.strftime("%Y-%m-%d"),
                   dias_habiles, fecha_limite.strftime("%Y-%m-%d"), estatus, fecha_respuesta, numero_respuesta]
            worksheet.update_row(index+2, row)

else:
    st.warning("No hay cartas registradas para actualizar.")
