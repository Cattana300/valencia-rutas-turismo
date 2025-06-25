import geopandas as gpd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

def load_monuments():
    gdf = gpd.read_file(DATA_DIR / "monuments.geojson")
    gdf = _ensure_latlon(gdf)
    return gdf

def load_buses():
    gdf = gpd.read_file(DATA_DIR / "buses.geojson")
    gdf = _ensure_latlon(gdf)
    return gdf

def load_metro():
    gdf = gpd.read_file(DATA_DIR / "metro.geojson")
    gdf = _ensure_latlon(gdf)
    return gdf

def load_fonts():
    gdf = gpd.read_file(DATA_DIR / "fonts.geojson")
    gdf = _ensure_latlon(gdf)
    return gdf

def _ensure_latlon(gdf):
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y
    return gdf

