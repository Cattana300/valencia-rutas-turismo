import streamlit as st
import pandas as pd
from src.data_loader import load_monuments

def get_user_inputs():
    st.sidebar.header("📝 Datos para tu ruta personalizada")

    # 1. Horario
    col1, col2 = st.sidebar.columns(2)
    hora_inicio = col1.time_input("Hora de inicio", value=pd.to_datetime("09:00").time())
    hora_fin = col2.time_input("Hora de fin", value=pd.to_datetime("18:00").time())

    if hora_inicio >= hora_fin:
        st.sidebar.error("La hora de inicio debe ser anterior a la de fin")

    # 2. Dirección alojamiento
    direccion = st.sidebar.text_input("📍 Dirección del alojamiento", placeholder="Calle X, Valencia")

    # 3. Transporte permitido
    transporte = st.sidebar.radio("🚊 Transporte público permitido", ["Ninguno", "Bus", "Metro", "Ambos"], index=3)

    # 4. Monumentos imprescindibles (máx 3)
    monuments_gdf = load_monuments()
    monument_names = sorted(monuments_gdf["nombre"].dropna().unique())
    monumentos_imprescindibles = st.sidebar.multiselect("🏛️ Monumentos imprescindibles (máx 3)", 
                                                        options=monument_names, max_selections=3)

    # 5. Preferencias de monumentos
    preferencias = st.sidebar.multiselect("🎯 Preferencias de tipo de monumento", 
                                          ["Jardines", "Iglesias", "Edificios históricos", 
                                           "Arte urbano", "Museos", "Plazas"])

    return {
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "direccion": direccion,
        "transporte": transporte,
        "monumentos_imprescindibles": monumentos_imprescindibles,
        "preferencias": preferencias
    }
