import streamlit as st
import pandas as pd
import datetime as dt
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

# Inicializar `st.session_state` si no está definido
if "cartas_db" not in st.session_state:
    st.session_state.cartas_db = pd.DataFrame(columns=[
        "ID", "Responsable", "Nombre de la Carta", "Fecha de Notificación",
        "Días Hábiles", "FECHA LÍMITE", "STATUS", "Fecha de Respuesta", "Carta de Respuesta"
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

# Función para cargar los datos desde la hoja de Google Sheets
def cargar_datos():
    worksheet = obtener_hoja_de_calculo()
    if worksheet:
        datos = worksheet.get_all_records()
        return pd.DataFrame(datos)
    else:
        return pd.DataFrame(columns=[
            "ID", "Responsable", "Nombre de la Carta", "Fecha de Notificación",
            "Días Hábiles", "FECHA LÍMITE", "STATUS", "Fecha de Respuesta", "Carta de Respuesta"
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

# --- Dashboard ---
st.header("📊 Dashboard de Estadísticas")
datos = cargar_datos()

if not datos.empty:
    if "STATUS" in datos.columns:
        # Gráfica: Número de cartas por estatus
        st.subheader("Número de Cartas por Estatus")
        fig1, ax1 = plt.subplots()
        datos["STATUS"].value_counts().plot(kind="bar", ax=ax1, color="skyblue")
        ax1.set_title("Número de Cartas por Estatus")
        ax1.set_xlabel("STATUS")
        ax1.set_ylabel("Cantidad")
        st.pyplot(fig1)
    else:
        st.warning("La columna 'STATUS' no está presente en los datos.")

    if "Responsable" in datos.columns:
        # Gráfica: Número de cartas por responsable
        st.subheader("Número de Cartas por Responsable")
        fig2, ax2 = plt.subplots()
        datos["Responsable"].value_counts().plot(kind="bar", ax=ax2, color="orange")
        ax2.set_title("Número de Cartas por Responsable")
        ax2.set_xlabel("Responsable")
        ax2.set_ylabel("Cantidad")
        st.pyplot(fig2)
    else:
        st.warning("La columna 'Responsable' no está presente en los datos.")

    # Tabla de datos
    st.subheader("📋 Base de Datos Completa")
    st.dataframe(datos)
else:
    st.warning("No hay datos para mostrar en el dashboard. Por favor, ingresa nuevas cartas.")

# --- Sección 1: Ingresar nueva carta ---
st.header("📩 Ingresar Nueva Carta")
with st.form("nueva_carta_form"):
    responsable = st.selectbox("Responsable", ["Anderson", "Renato", "Marisol"])
    nombre_carta = st.text_input("Nombre de la Carta")
    fecha_notificacion = st.date_input("Fecha de Notificación")
    dias_habiles = st.number_input("Días Hábiles para Responder", min_value=1, step=1)

    if st.form_submit_button("Registrar Carta"):
        fecha_limite = calcular_fecha_limite(fecha_notificacion, dias_habiles)

        nueva_carta = {
            "ID": len(datos) + 1,
            "Responsable": responsable,
            "Nombre de la Carta": nombre_carta,
            "Fecha de Notificación": fecha_notificacion,
            "Días Hábiles": dias_habiles,
            "FECHA LÍMITE": fecha_limite,
            "STATUS": "Pendiente",
            "Fecha de Respuesta": None,
            "Carta de Respuesta": None
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
                nueva_carta["ID"], nueva_carta["Responsable"], nueva_carta["Nombre de la Carta"],
                nueva_carta["Fecha de Notificación"].strftime("%Y-%m-%d"), nueva_carta["Días Hábiles"],
                nueva_carta["FECHA LÍMITE"].strftime("%Y-%m-%d"), nueva_carta["STATUS"],
                None, None  # Inicializamos Fecha de Respuesta y Carta de Respuesta como vacíos
            ])

# --- Sección 2: Actualizar estado ---
st.header("✅ Actualizar Estado de Carta")
if not datos.empty:
    with st.form("actualizar_estado_form"):
        opciones_carta = datos["ID"].astype(str) + " - " + datos["Nombre de la Carta"]
        carta_seleccionada = st.selectbox("Seleccionar Carta", opciones_carta)
        nuevo_estado = st.selectbox("Nuevo Estado", ["Pendiente", "Respondida", "Archivada"])
        carta_respuesta = st.text_input("Actualizar Carta de Respuesta (Opcional)")
        fecha_respuesta = st.date_input("Actualizar Fecha de Respuesta (Opcional)", value=None)

        if st.form_submit_button("Actualizar Estado"):
            # Obtener ID de la carta seleccionada
            carta_id = int(carta_seleccionada.split(" - ")[0])

            # Reflejar los cambios en la hoja de Google Sheets
            worksheet = obtener_hoja_de_calculo()
            if worksheet:
                filas = worksheet.get_all_values()  # Obtiene todas las filas incluyendo encabezados
                for idx, fila in enumerate(filas):
                    if idx == 0:  # Salta la fila de encabezados
                        continue
                    if int(fila[0]) == carta_id:  # Compara con la columna 'ID'
                        worksheet.update_cell(idx + 1, 7, nuevo_estado)  # Columna 'STATUS'
                        if carta_respuesta:
                            worksheet.update_cell(idx + 1, 10, carta_respuesta)  # Columna 'Carta de Respuesta'
                        if fecha_respuesta:
                            worksheet.update_cell(idx + 1, 9, fecha_respuesta.strftime("%Y-%m-%d"))  # Columna 'Fecha de Respuesta'
                        break
            st.success(f"Estado de la carta {carta_id} actualizado correctamente.")
