import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pydeck as pdk

from src.route_generator import generar_ruta
import geopandas as gpd
import datetime as dt
import pandas as pd

from src.route_form import get_user_inputs
from src.geocode import geocode_location
from src.data_loader import load_monuments, load_buses, load_metro, load_fonts

# al comienzo de streamlit_app.py
import osmnx as ox
import networkx as nx
import streamlit as st

GRAPH_PATH = "data/walk_graph.graphml"

@st.cache_resource(show_spinner="Cargando red peatonal …")
def load_walk_graph():
    if os.path.exists(GRAPH_PATH):
        return ox.load_graphml(GRAPH_PATH)
    G = ox.graph_from_place("Valencia, Spain", network_type="walk", simplify=True)
    ox.save_graphml(G, GRAPH_PATH)          # guarda para futuros arranques
    return G

G = load_walk_graph()

def shortest_walk_path(coord1, coord2):
    """Devuelve la lista [[lon, lat], …] que sigue la calle a pie entre dos puntos."""
    orig = ox.nearest_nodes(G, coord1[0], coord1[1])  # lon, lat
    dest = ox.nearest_nodes(G, coord2[0], coord2[1])
    nodes = nx.shortest_path(G, orig, dest, weight="length")
    return [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in nodes]




st.set_page_config(page_title="Rutas Turísticas València", layout="wide")

st.title("🗺️ Generador de rutas turísticas personalizadas en València")
st.markdown("Planifica tus rutas según tus gustos, tiempo y ritmo de viaje. Visualiza monumentos, fuentes, transporte público y más.")

# Sidebar para selección de capas
st.sidebar.header("🔍 Selecciona qué mostrar en el mapa")
show_monuments = st.sidebar.checkbox("🏛️ Monumentos turísticos", value=True)
show_buses = st.sidebar.checkbox("🚌 Paradas EMT", value=False)
show_metro = st.sidebar.checkbox("🚇 Estaciones Metro/FGV", value=False)
show_fonts = st.sidebar.checkbox("💧 Fuentes de agua", value=False)

# Obtener inputs del usuario
user_inputs = get_user_inputs()

# Geocodificar dirección
location = None
if user_inputs["direccion"]:
    location = geocode_location(user_inputs["direccion"])

# Inicializar capas
layers = []

# Cargar el GeoJSON definitivo con la columna "tipo"
gdf_monumentos = gpd.read_file("data/raw/monuments.geojson")

if st.sidebar.button("✨ Generar ruta"):
    
    if not location:
        st.error("Debes introducir una dirección de alojamiento válida antes de generar la ruta.")
    else:
        start_coord = (location[0], location[1])  # lat, lon
        itin = generar_ruta(
            gdf_monumentos=gdf_monumentos,
            start_coord=start_coord,
            inicio_hora=user_inputs["hora_inicio"],
            fin_hora=user_inputs["hora_fin"],
            imprescindibles=user_inputs["monumentos_imprescindibles"],
            preferencias_tipo=user_inputs["preferencias"],
            transporte=user_inputs["transporte"].lower(),  # “ninguno”, “bus”, “metro”, “ambos”
            incluir_pausa_comida=True,
        )

        # ------------------------------------------------------------------
        # 2) MOSTRAR ITINERARIO EN TABLA
        # ------------------------------------------------------------------
        st.subheader("📋 Itinerario propuesto")
        st.dataframe(pd.DataFrame(itin))
        
        # ------------------------------------------------------------------
        # 3) DIBUJAR RUTA EN EL MAPA
        # ------------------------------------------------------------------
        
        itin_pd=pd.DataFrame(itin)

        COLOR_MAP = {
        "a":       [128, 128, 128],  # gris
        "bus":         [255, 165,   0],  # naranja
        "metro":       [  0,   0, 255],  # azul
        }

        TRANSPORT_MODES = {"bus", "metro"}
        def pick_color(tipo: str):
            first = tipo.split()[0].lower()
            if first in TRANSPORT_MODES:
                return COLOR_MAP[first]
            # para cualquier otro 'tipo' (museo, iglesia, edificio, etc.)
            return COLOR_MAP["a"]

        itin_pd["color"] = itin_pd["tipo"].apply(pick_color)
        itin_coords = [
        (row.lon, row.lat)
        for _, row in itin_pd.iterrows()
        if pd.notnull(row.lat) and pd.notnull(row.lon)
        ]
        
        full_path = []
        if len(itin_coords) > 1:
            for p1, p2 in zip(itin_coords[:-1], itin_coords[1:]):
                seg = shortest_walk_path(p1, p2)  # lista [lon, lat]
                full_path.extend(seg if not full_path else seg[1:])
        
            path_layer = pdk.Layer(
                "PathLayer",
                data=[{"path": full_path}],
                get_path="path",
                get_width=6,
                get_color="color",
                pickable=False,
            )
            layers.append(path_layer)
        
        # Puntos del itinerario (siempre)
        itin_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{"lon": p["lon"], "lat": p["lat"], "tooltip": p["nombre"]} for p in itin],
            get_position=["lon", "lat"],
            get_color=[30, 144, 255],
            get_radius=45,
            pickable=True,
        )
        layers.append(itin_layer)



# Añadir capa de alojamiento si hay dirección válida
if location:
    lat, lon = location
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=[{"lat": lat, "lon": lon, "tooltip": "🏠 Alojamiento"}],
        get_position=["lon", "lat"],
        get_color=[0, 0, 0],
        get_radius=40,
        pickable=True
    ))

# Añadir capas según selección
if show_monuments:
    gdf = load_monuments()
    gdf["tooltip"] = gdf["nombre"]
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=gdf,
        get_position=["lon", "lat"],
        get_color=[255, 100, 100],
        get_radius=20,
        pickable=True
    ))

if show_buses:
    gdf = load_buses()
    gdf["tooltip"] = "Parada EMT"
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=gdf,
        get_position=["lon", "lat"],
        get_color=[0, 100, 255],
        get_radius=15,
        pickable=True
    ))

if show_metro:
    gdf = load_metro()
    gdf["tooltip"] = gdf["nombre"]
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=gdf,
        get_position=["lon", "lat"],
        get_color=[160, 32, 240],
        get_radius=20,
        pickable=True
    ))

if show_fonts:
    gdf = load_fonts()
    gdf["tooltip"] = "Fuente de agua"
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=gdf,
        get_position=["lon", "lat"],
        get_color=[0, 255, 0],
        get_radius=10,
        pickable=True
    ))

# Configurar vista del mapa
if location:
    view_lat, view_lon = location
    zoom_level = 13
    st.success(f"Alojamiento localizado en lat: {view_lat:.5f}, lon: {view_lon:.5f}")
else:
    view_lat, view_lon = 39.47, -0.376
    zoom_level = 12
    if user_inputs["direccion"]:
        st.warning("No se pudo localizar la dirección proporcionada.")

# Mostrar el mapa
if layers:
    st.subheader("🗺️ Mapa interactivo de València")
    st.pydeck_chart(pdk.Deck(
        map_style="road",
        initial_view_state=pdk.ViewState(
            latitude=view_lat,
            longitude=view_lon,
            zoom=zoom_level
        ),
        layers=layers,
        tooltip={"text": "{tooltip}"}
    ))
else:
    st.info("Activa al menos una capa en el menú lateral para ver el mapa.")
