import streamlit as st
import pandas as pd
import datetime as dt
import gspread
from google.oauth2.service_account import Credentials

# Inicializar `st.session_state` si no está definido
if "cartas_db" not in st.session_state:
    st.session_state.cartas_db = pd.DataFrame(columns=[
        "ID", "Trabajador", "Nombre_Carta", "Fecha_Notificación", 
        "Días_Hábiles", "Fecha_Límite", "Estatus", 
        "Fecha_Respuesta", "Número_Carta_Respuesta"
    ])

# Función para conectarse a Google Sheets usando las credenciales
def obtener_hoja_de_calculo():
    try:
        # Definir el alcance de la API de Google Sheets y Google Drive
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Cargar las credenciales de Streamlit Secrets
        creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)

        # Autenticación con las credenciales
        client = gspread.authorize(creds)

        # Abre la hoja de cálculo de Google Sheets por su ID
        spreadsheet = client.open_by_key("1Ke5AF0EuMr2Q2QBWym9gQ2lbQ_6-JUknQN9Kdysp86w")
        worksheet = spreadsheet.sheet1  # Accede a la primera hoja
        return worksheet
    except Exception as e:
        st.error(f"Error al obtener la hoja de cálculo: {e}")
        return None

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

        # Guardar en Google Sheets
        worksheet = obtener_hoja_de_calculo()
        if worksheet:
            worksheet.append_row([
                nueva_carta["ID"], nueva_carta["Trabajador"], nueva_carta["Nombre_Carta"],
                nueva_carta["Fecha_Notificación"].strftime("%Y-%m-%d"), nueva_carta["Días_Hábiles"],
                nueva_carta["Fecha_Límite"].strftime("%Y-%m-%d"), nueva_carta["Estatus"],
                nueva_carta["Fecha_Respuesta"], nueva_carta["Número_Carta_Respuesta"]
            ])

# --- Sección 2: Actualizar estado ---
st.header("✅ Actualizar Estado de Carta")
if not st.session_state.cartas_db.empty:
    with st.form("actualizar_estado_form"):
        opciones_carta = st.session_state.cartas_db["ID"].astype(str) + " - " + st.session_state.cartas_db["Nombre_Carta"]
        carta_seleccionada = st.selectbox("Seleccionar Carta", opciones_carta)
        nuevo_estado = st.selectbox("Nuevo Estado", ["Pendiente", "Respondida", "Archivada"])

        if st.form_submit_button("Actualizar Estado"):
            # Obtener ID de la carta seleccionada
            carta_id = int(carta_seleccionada.split(" - ")[0])
            
            # Actualizar el estado en la base de datos local
            st.session_state.cartas_db.loc[st.session_state.cartas_db["ID"] == carta_id, "Estatus"] = nuevo_estado
            
            # Reflejar los cambios en la hoja de Google Sheets
            worksheet = obtener_hoja_de_calculo()
            if worksheet:
                filas = worksheet.get_all_values()  # Obtiene todas las filas incluyendo encabezados
                for idx, fila in enumerate(filas):
                    if idx == 0:  # Salta la fila de encabezados
                        continue
                    if int(fila[0]) == carta_id:  # Compara con la columna 'ID' (índice 0)
                        worksheet.update_cell(idx + 1, 7, nuevo_estado)  # Columna 'STATUS' (índice 7 en hoja = columna G)
                        break
            st.success(f"Estado de la carta {carta_id} actualizado a '{nuevo_estado}' en la hoja de cálculo.")
