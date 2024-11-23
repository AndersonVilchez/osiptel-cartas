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
            "Fecha de Respuesta": "",
            "Carta de Respuesta": ""
        }

        # Guardar en Google Sheets
        worksheet = obtener_hoja_de_calculo()
        if worksheet:
            worksheet.append_row([
                nueva_carta["ID"], nueva_carta["Responsable"], nueva_carta["Nombre de la Carta"],
                nueva_carta["Fecha de Notificación"].strftime("%Y-%m-%d"), nueva_carta["Días Hábiles"],
                nueva_carta["FECHA LÍMITE"].strftime("%Y-%m-%d"), nueva_carta["STATUS"],
                nueva_carta["Fecha de Respuesta"], nueva_carta["Carta de Respuesta"]
            ])
        st.success("Carta registrada correctamente.")

# --- Sección 2: Actualizar Estado ---
st.header("✅ Actualizar Estado de Carta")

if not datos.empty and "Nombre de la Carta" in datos.columns:
    with st.form("actualizar_estado_form"):
        # Crear un filtro basado en el "Nombre de la Carta"
        nombres_cartas = datos["Nombre de la Carta"].unique()
        carta_seleccionada = st.selectbox("Seleccionar Nombre de la Carta", nombres_cartas)

        # Filtrar la carta seleccionada para mostrar datos actuales
        carta_filtrada = datos[datos["Nombre de la Carta"] == carta_seleccionada]
        if not carta_filtrada.empty:
            # Mostrar los datos actuales de la carta seleccionada
            st.write("### Datos Actuales de la Carta")
            st.write(carta_filtrada[["Nombre de la Carta", "Estado", "Carta de Respuesta", "Fecha de Respuesta"]])

            # Nuevo estado
            nuevo_estado = st.selectbox("Nuevo Estado", ["Pendiente", "Respondida", "Archivada"], 
                                        index=["Pendiente", "Respondida", "Archivada"].index(carta_filtrada["Estado"].values[0]))

            # Nueva carta de respuesta
            nueva_carta_respuesta = st.text_input(
                "Nueva Carta de Respuesta (Opcional)",
                value=str(carta_filtrada["Carta de Respuesta"].values[0]) if pd.notna(carta_filtrada["Carta de Respuesta"].values[0]) else ""
            )

            # Validación estricta para la fecha de respuesta
            try:
                if pd.notna(carta_filtrada["Fecha de Respuesta"].values[0]):
                    fecha_actual = pd.to_datetime(carta_filtrada["Fecha de Respuesta"].values[0]).date()
                else:
                    fecha_actual = dt.date.today()  # Fecha predeterminada
            except Exception:
                fecha_actual = dt.date.today()  # En caso de error, usar la fecha actual
            
            nueva_fecha_respuesta = st.date_input("Nueva Fecha de Respuesta (Opcional)", value=fecha_actual)

            # Botón de envío
            submit_button = st.form_submit_button("Actualizar Estado")
            if submit_button:
                # Actualizar datos en Google Sheets
                worksheet = obtener_hoja_de_calculo()
                if worksheet:
                    filas = worksheet.get_all_values()  # Todas las filas
                    for idx, fila in enumerate(filas):
                        if idx == 0:  # Ignorar encabezados
                            continue
                        if fila[2] == carta_seleccionada:  # Comparar por 'Nombre de la Carta'
                            worksheet.update_cell(idx + 1, 7, nuevo_estado)  # Columna 'Estado'
                            worksheet.update_cell(idx + 1, 9, nueva_carta_respuesta)  # Columna 'Carta de Respuesta'
                            worksheet.update_cell(idx + 1, 8, nueva_fecha_respuesta.strftime("%Y-%m-%d"))  # Columna 'Fecha de Respuesta'
                            break
                st.success(f"Estado de la carta '{carta_seleccionada}' actualizado correctamente.")
else:
    st.warning("No hay datos disponibles o la columna 'Nombre de la Carta' no está presente en los datos.")

