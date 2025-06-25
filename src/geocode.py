import requests

def geocode_location(address: str):
    """Convierte una dirección en lat/lon usando Nominatim y la restringe a València."""
    if not address:
        return None

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
        "bounded": 1,
        "viewbox": "-0.5,39.6,-0.3,39.4"  # izquierda, arriba, derecha, abajo (València)
    }

    headers = {"User-Agent": "valencia-smart-routes/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        print(f"Error al geocodificar: {e}")

    return None
