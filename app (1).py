
import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px

# Inicialización de la base de datos
if "cartas_db" not in st.session_state:
    st.session_state.cartas_db = pd.DataFrame(columns=[
        "ID", "Trabajador", "Nombre_Carta", "Fecha_Notificación", 
        "Días_Hábiles", "Fecha_Límite", "Estatus", 
        "Fecha_Respuesta", "Número_Carta_Respuesta"
    ])

# Función para calcular la fecha límite (sumando días hábiles)
def calcular_fecha_limite(fecha_inicio, dias_habiles):
    fecha = fecha_inicio
    while dias_habiles > 0:
        fecha += dt.timedelta(days=1)
        if fecha.weekday() < 5:  # Excluye sábados y domingos
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

# --- Sección 2: Actualizar estado ---
st.header("✅ Actualizar Estado de Carta")
if not st.session_state.cartas_db.empty:
    with st.form("actualizar_estado_form"):
        id_carta = st.selectbox("Seleccionar Carta (ID - Nombre)", 
                                st.session_state.cartas_db["ID"].astype(str) + " - " +
                                st.session_state.cartas_db["Nombre_Carta"])
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
    st.session_state.cartas_db["Mes"] = pd.to_datetime(
        st.session_state.cartas_db["Fecha_Notificación"]
    ).dt.to_period("M")
    grafico_mensual = st.session_state.cartas_db.groupby("Mes").size().reset_index(name="Cantidad")
    fig = px.line(grafico_mensual, x="Mes", y="Cantidad", title="Evolución Mensual de Cartas")
    st.plotly_chart(fig)

    # Gráfico de cartas por trabajador
    st.subheader("Cartas por Trabajador")
    grafico_trabajador = st.session_state.cartas_db.groupby(["Trabajador", "Estatus"]).size().reset_index(name="Cantidad")
    fig = px.bar(grafico_trabajador, x="Trabajador", y="Cantidad", color="Estatus", title="Cartas por Trabajador")
    st.plotly_chart(fig)
else:
    st.warning("No hay datos para visualizar.")
