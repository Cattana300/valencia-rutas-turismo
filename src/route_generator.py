# src/route_generator.py
"""Módulo principal que genera la ruta turística personalizada.

Contiene la lógica para:
1. Filtrar y priorizar monumentos según preferencias.
2. Calcular distancias y estimar tiempos a pie.
3. Decidir si conviene transporte público (>1km).
4. Insertar pausa de comida de 13:30-14:30 (1h).
5. Devolver un itinerario ordenado con tiempos y modo de transporte.
"""

from __future__ import annotations

import math
import datetime as dt
from typing import List, Dict, Tuple, Literal

import pandas as pd  # <–– añadido para concat y dataframe
import geopandas as gpd
from shapely.geometry import Point
import streamlit as st



best_dist = None
best_line = None
best_mode = None

# ------------------------
# Constantes de configuración
# ------------------------
WALK_SPEED_KMH = 4.0  # velocidad media a pie
TP_SPEED_KMH = 30.0 # velocidad media en transporte público
VISIT_DURATION_MIN = 25  # minutos por monumento

# ------------------------
# Funciones auxiliares
# ------------------------

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Devuelve la distancia entre dos parejas lat/lon en metros."""
    R = 6371000
    phi1, phi2 = map(math.radians, [lat1, lat2])
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def walking_time_minutes(distance_m: float) -> int:
    km = distance_m / 1000
    return int(km / WALK_SPEED_KMH * 60)

def tp_time_minutes(distance_m: float) -> int:
    km = distance_m / 1000
    return int(km / TP_SPEED_KMH * 60)


def should_use_public_transport(origen, destino, modo_pt) -> Tuple[bool, str, float]:
    """
    Devuelve (usar_tp, modo_str, dist_tp) evaluando si el ahorro supera 900 m.
    """
    dist_walk = haversine_distance(*origen, *destino)
    time_walk_min = walking_time_minutes(dist_walk)
    mejores = []

    modos = []
    if modo_pt == "ambos":
        modos = ["bus", "metro"]
    elif modo_pt in ("bus", "metro"):
        modos = [modo_pt]

    for m in modos:
        time_tp, linea, modo = get_public_transport_time(origen, destino, m, return_line=True)
        if time_tp is not None:
            ahorro = time_walk_min - time_tp
            mejores.append((ahorro, time_tp, linea, m))

    if mejores:
        ahorro, time_tp, linea, m = max(mejores, key=lambda x: x[0])
        if ahorro > 5:  # o el umbral que decidas
            return True, f"{m} línea {linea}", time_tp

    return False, "A pie", time_walk_min



# ------------------------
# Función principal
# ------------------------
TransportOption = Literal["ninguno", "bus", "metro", "ambos"]
# ------------------------------------------------------------
# Rutas básicas de BUS y METRO con los GeoJSON cargados
# ------------------------------------------------------------
import geopandas as gpd
from shapely.ops import nearest_points

# Carga global (hazlo solo una vez)
GDF_BUS = gpd.read_file("data/raw/buses.geojson")     # columnas: lon, lat, lineas (ej. "2,19,99")
GDF_METRO = gpd.read_file("data/raw/metro.geojson")   # columnas: lon, lat, linea  (ej. "1")

def nearest_stop(gdf, lon, lat, max_dist=400):
    """Devuelve la parada/estación más cercana a (lon,lat) dentro de max_dist metros."""
    gdf["dist_temp"] = gdf.geometry.distance(Point(lon, lat))
    sel = gdf.loc[gdf["dist_temp"] <= max_dist]
    if sel.empty:
        return None
    return sel.sort_values("dist_temp").iloc[0]

def get_public_transport_time(origen, destino, modo="ambos", return_line: bool = False):
    best_time = None
    best_line = None
    best_mode = None
    """
    Estima el tiempo total (m) usando bus/metro entre dos coordenadas:
      * origen, destino = (lat, lon)
      * modo = "bus", "metro" o "ambos"
    Devuelve None si no hay ruta directa con una sola línea.
    """
    lat_o, lon_o = origen
    lat_d, lon_d = destino

    # --- METRO -------------------------------------------------
    if modo in {"metro", "ambos"}:
        o_est = nearest_stop(GDF_METRO, lon_o, lat_o)
        d_est = nearest_stop(GDF_METRO, lon_d, lat_d)
        if o_est is not None and d_est is not None:
            if o_est["linea"] == d_est["linea"]:   # misma línea sin transbordo
                walk_in  = haversine_distance(lat_o, lon_o, o_est.geometry.y, o_est.geometry.x)
                walk_in_time = walking_time_minutes(walk_in)
                ride     = haversine_distance(o_est.geometry.y, o_est.geometry.x,
                                              d_est.geometry.y, d_est.geometry.x)
                ride_time=tp_time_minutes(ride)
                walk_out = haversine_distance(lat_d, lon_d, d_est.geometry.y, d_est.geometry.x)
                walk_out_time = walking_time_minutes(walk_out)
                time_metro = walk_in_time + ride_time + walk_out_time
                if best_time is None or time_metro < best_time:
                    best_time = time_metro
                    best_line = o_est["linea"]
                    best_mode = "Metro"


    # --- BUS ---------------------------------------------------
    if modo in {"bus", "ambos"}:
        o_par = nearest_stop(GDF_BUS, lon_o, lat_o)
        if o_par is not None:
            lineas_o = {l.strip() for l in str(o_par["lineas"]).split(",")}
            cand_dest = GDF_BUS[GDF_BUS["lineas"].apply(
                lambda txt: bool(set(str(txt).split(",")).intersection(lineas_o)))]
            d_par = nearest_stop(cand_dest, lon_d, lat_d)
            if d_par is not None:
                common = set(str(d_par["lineas"]).split(",")).intersection(lineas_o)
                if common:
                    walk_in  = haversine_distance(lat_o, lon_o, o_par.geometry.y, o_par.geometry.x)
                    walk_in_time = walking_time_minutes(walk_in)
                    ride     = haversine_distance(o_par.geometry.y, o_par.geometry.x,
                                                  d_par.geometry.y, d_par.geometry.x)
                    ride_time=tp_time_minutes(ride)
                    walk_out = haversine_distance(lat_d, lon_d, d_par.geometry.y, d_par.geometry.x)
                    walk_out_time = walking_time_minutes(walk_out)
                    time_bus = walk_in_time + ride_time + walk_out_time
                    if best_time is None or time_bus < best_time:
                        best_time = time_bus
                        best_line = list(common)[0]
                        best_mode = "Bus"

    if return_line:
        return best_time, best_line, best_mode
    else:
        return best_time


def generar_ruta(
    gdf_monumentos: gpd.GeoDataFrame,
    start_coord: Tuple[float, float],
    inicio_hora: dt.time,
    fin_hora: dt.time,
    imprescindibles: List[str],
    preferencias_tipo: List[str],
    transporte: TransportOption = "ambos",
    incluir_pausa_comida: bool = True,
) -> List[Dict]:
    """Devuelve una lista ordenada de pasos de la ruta."""

    # ---------- prefiltrado ----------
    candidatos = (
        gdf_monumentos[gdf_monumentos["tipo"].isin(preferencias_tipo)]
        if preferencias_tipo else gdf_monumentos.copy()
    )
    imp_df = gdf_monumentos[gdf_monumentos["nombre"].isin(imprescindibles)]
    candidatos = gpd.GeoDataFrame(pd.concat([imp_df, candidatos])).drop_duplicates("nombre")

    # ---------- orden por cercanía al alojamiento ----------
    start_lat, start_lon = start_coord
    inicio_point = Point(start_lon, start_lat)
    candidatos["dist_start"] = candidatos.geometry.distance(inicio_point)
    candidatos = candidatos.sort_values("dist_start").reset_index(drop=True)

    # ---------- estado inicial ----------
    itinerary = []
    current_lat, current_lon = start_coord
    current_time = dt.datetime.combine(dt.date.today(), inicio_hora)
    end_time = dt.datetime.combine(dt.date.today(), fin_hora)
    time_budget = (end_time - current_time).total_seconds() / 60

    visitados: set[str] = set()
    faltan_imp: list[str] = [n for n in imprescindibles if n]  # copia editable

    # ---------- bucle principal ----------
    while time_budget > 0 and len(visitados) < len(candidatos):
        # Distancia actual a cada POI
        candidatos["dist_now"] = candidatos.apply(
            lambda row: haversine_distance(current_lat, current_lon,
                                           row.geometry.y, row.geometry.x),
            axis=1
        )

        # Si quedan imprescindibles, prioriza acercarse al primero pendiente
        if faltan_imp:
            proximo_imp = gdf_monumentos[gdf_monumentos["nombre"] == faltan_imp[0]].iloc[0]
            candidatos["dist_to_next_imp"] = candidatos.apply(
                lambda r: haversine_distance(r.geometry.y, r.geometry.x,
                                             proximo_imp.geometry.y, proximo_imp.geometry.x),
                axis=1
            )
            ordenados = (candidatos[~candidatos["nombre"].isin(visitados)]
                         .sort_values(["dist_to_next_imp", "dist_now"]))
        else:
            ordenados = candidatos[~candidatos["nombre"].isin(visitados)].sort_values("dist_now")

        if ordenados.empty:
            break

        # Elige el primer POI que cabe en el tiempo
        elegido = None
        tramo_usar = 0
        modo_usar = "A pie"
        for _, poi in ordenados.iterrows():
            origen = (current_lat, current_lon)
            destino = (poi.geometry.y, poi.geometry.x)

            # evaluamos transporte público
            usar_tp, modo_tp, tramo_min = should_use_public_transport(
                origen, destino, transporte
            )

            if time_budget >= tramo_min + VISIT_DURATION_MIN:
                elegido = poi
                tramo_usar = tramo_min
                modo_usar = modo_tp if usar_tp else "A pie"
                break

        if elegido is None:
            break  # no cabe ningún candidato

        # ---------- añadir tramo ----------
        itinerary.append({
            "nombre": f"Tramo hacia {elegido['nombre']}",
            "tipo": modo_usar,
            "llegada": current_time.strftime("%H:%M"),
            "salida": (current_time + dt.timedelta(minutes=tramo_usar)).strftime("%H:%M"),
            "lat": current_lat,
            "lon": current_lon,
        })
        current_time += dt.timedelta(minutes=tramo_usar)
        time_budget -= tramo_usar

        # ---------- pausa comida ----------
        if incluir_pausa_comida and dt.time(13, 30) <= current_time.time() <= dt.time(14, 30):
            itinerary.append({
                "nombre": "Pausa comida",
                "tipo": "Pausa",
                "llegada": current_time.strftime("%H:%M"),
                "salida": (current_time + dt.timedelta(hours=1)).strftime("%H:%M"),
                "lat": current_lat,
                "lon": current_lon,
            })
            current_time += dt.timedelta(hours=1)
            time_budget -= 60
            incluir_pausa_comida = False

        # ---------- visita POI ----------
        itinerary.append({
            "nombre": elegido["nombre"],
            "tipo": elegido["tipo"],
            "llegada": current_time.strftime("%H:%M"),
            "salida": (current_time + dt.timedelta(minutes=VISIT_DURATION_MIN)).strftime("%H:%M"),
            "lat": elegido.geometry.y,
            "lon": elegido.geometry.x,
        })
        current_time += dt.timedelta(minutes=VISIT_DURATION_MIN)
        time_budget -= VISIT_DURATION_MIN
        current_lat, current_lon = elegido.geometry.y, elegido.geometry.x
        visitados.add(elegido["nombre"])
        if elegido["nombre"] in faltan_imp:
            faltan_imp.remove(elegido["nombre"])

    # ---------- retorno al alojamiento ----------
    dist_back_walk = haversine_distance(current_lat, current_lon, start_lat, start_lon)
    modo_vuelta = "A pie"
    dist_back = dist_back_walk

    if transporte != "ninguno":
        time_tp_back, linea_back, modo_back = get_public_transport_time(
            (current_lat, current_lon), (start_lat, start_lon), transporte, return_line=True
        )
        if time_tp_back is not None and (dist_back_walk - time_tp_back) >= 900:
            dist_back = time_tp_back + 200  # sumamos accesos estimados
            modo_vuelta = f"{modo_back} línea {linea_back}"

    time_back = walking_time_minutes(dist_back)
    if time_budget >= time_back:
        itinerary.append({
            "nombre": "Retorno al alojamiento",
            "tipo": modo_vuelta,
            "llegada": current_time.strftime("%H:%M"),
            "salida": (current_time + dt.timedelta(minutes=time_back)).strftime("%H:%M"),
            "lat": start_lat,
            "lon": start_lon,
        })

    return itinerary

    




















