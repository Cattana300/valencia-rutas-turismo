# 🗺️ Valencia Smart Routes

Generador de rutas turísticas inteligentes y personalizadas para la ciudad de València. Esta aplicación permite a los usuarios planificar recorridos según sus preferencias, monumentos imprescindibles, horarios, y transporte disponible. Muestra mapas interactivos con monumentos, fuentes, paradas de metro/bus, y genera rutas eficientes optimizadas en tiempo.

## 🚀 Características

- Selección de horario y punto de alojamiento
- Monumentos imprescindibles y preferencias de tipo (iglesias, plazas, arte urbano, etc.)
- Inclusión de pausa para comer
- Transporte público inteligente (bus y metro) solo si ahorra más de 900m andando
- Cálculo realista con red peatonal de OSM
- Mapas interactivos y tabla del itinerario

---

## 📁 Estructura del Proyecto

```
valencia-smart-routes/
├── app/
│   └── streamlit_app.py             # Aplicación principal en Streamlit
├── src/
│   ├── route_generator.py           # Lógica de generación de rutas
│   ├── data_loader.py               # Carga de datos desde archivos
│   ├── geocoding.py                 # Geocodificación de direcciones
│   └── route_form.py                # Formulario de entrada de usuario
├── data/
│   ├── walk_graph.graphml           # Red peatonal de València (descargada previamente)
│   └── raw/
│       ├── monuments.geojson        # Monumentos turísticos
│       ├── metro.geojson            # Estaciones de metro/FGV
│       ├── buses.geojson            # Paradas EMT
│       └── fonts.geojson            # Fuentes de agua
├── requirements.txt                 # Dependencias del proyecto
└── README.md                        # Este archivo
```

---

## 🧑‍💻 Ejecución Local

1. Clona el repositorio:

```bash
git clone https://github.com/tu_usuario/valencia-smart-routes.git
cd valencia-smart-routes
```

2. Crea un entorno virtual y activa:

```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
```

3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecuta la app:

```bash
streamlit run app/streamlit_app.py
```

---

## ☁️ Despliegue en Streamlit Cloud

1. Sube el proyecto a un repositorio de GitHub.
2. Entra en [streamlit.io/cloud](https://streamlit.io/cloud) y vincula tu cuenta de GitHub.
3. Selecciona el repositorio y define el archivo principal como:
```
app/streamlit_app.py
```
4. Define las variables de entorno si fuese necesario (ej: API keys).

---

## ✅ Requisitos

- Python >= 3.8
- Requiere archivos en `data/raw/` y `data/walk_graph.graphml` previamente descargados

---

## 📍 Créditos

Proyecto desarrollado como parte de un trabajo académico para la asignatura "Evaluación, Despliegue y Monitorización de Modelos", Universitat de València.