"""
grafo.py
--------
Base de conocimiento (hechos) y construcción del grafo de bibliotecas de Bogotá.

- Los NODOS son las bibliotecas (con su localidad, dirección y coordenadas reales).
- Las ARISTAS (qué biblioteca se conecta con cuál) se deciden con la distancia
  en línea recta (Haversine): cada nodo se une a sus K vecinas más cercanas,
  y se agrega un Árbol de Expansión Mínima (Prim) para garantizar que el
  grafo sea conexo. Haversine aquí SOLO decide la estructura del grafo.
- El COSTO de cada arista (lo que usará UCS) es la DISTANCIA REAL RECORRIDA
  POR CALLE, obtenida de OSRM (routing real, no línea recta). Los resultados
  se guardan en cache_distancias_reales.json para no tener que volver a
  consultar internet cada vez que se corre el programa.

Requisitos:
    pip install requests

Uso normal (ya con la cache generada):
    from grafo import construir_grafo, NODOS
    grafo = construir_grafo()

La primera vez que se corre (o si agregas una arista nueva) sí necesita
internet para consultar OSRM; las siguientes veces usa la cache y es
instantáneo.
"""

import json
import math
import os
from collections import defaultdict

import requests

# -----------------------------------------------------------------------
# 1) BASE DE CONOCIMIENTO: hechos sobre las bibliotecas (nodos del problema)
# -----------------------------------------------------------------------
BIBLIOTECAS = [
    {"id": "B01", "nombre": "Manuel Zapata Olivella - El Tintal", "localidad": "Kennedy", "lat": 4.6430923, "lon": -74.1547938},
    {"id": "B02", "nombre": "Biblioteca Publica Bosa", "localidad": "Bosa", "lat": 4.6329853, "lon": -74.2010831},
    {"id": "B03", "nombre": "Lago Timiza", "localidad": "Kennedy", "lat": 4.6099925, "lon": -74.1584356},
    {"id": "B04", "nombre": "Venecia", "localidad": "Tunjuelito", "lat": 4.5927985, "lon": -74.1409248},
    {"id": "B05", "nombre": "Carlos E. Restrepo", "localidad": "Antonio Narino", "lat": 4.58434, "lon": -74.10322},
    {"id": "B06", "nombre": "La Pena", "localidad": "Santa Fe", "lat": 4.5875052, "lon": -74.0669076},
    {"id": "B07", "nombre": "La Victoria", "localidad": "San Cristobal", "lat": 4.553765, "lon": -74.094151},
    {"id": "B08", "nombre": "Nestor Forero Alcala - Puente Aranda", "localidad": "Puente Aranda", "lat": 4.6059411, "lon": -74.1034333},
    {"id": "B09", "nombre": "Rafael Uribe Uribe", "localidad": "Rafael Uribe Uribe", "lat": 4.5752057, "lon": -74.1117096},
    {"id": "B10", "nombre": "Gabriel Garcia Marquez - El Tunal", "localidad": "Tunjuelito", "lat": 4.5720711, "lon": -74.1299145},
    {"id": "B11", "nombre": "Soledad Lamprea - Perdomo", "localidad": "Ciudad Bolivar", "lat": 4.5879068, "lon": -74.1681723},
    {"id": "B12", "nombre": "Arborizadora Alta", "localidad": "Ciudad Bolivar", "lat": 4.5682051, "lon": -74.1593714},
    {"id": "B13", "nombre": "Publico Escolar Sumapaz", "localidad": "Sumapaz", "lat": 3.9856253, "lon": -74.3635808},
    {"id": "B14", "nombre": "Julio Mario Santo Domingo", "localidad": "Suba", "lat": 4.7566969, "lon": -74.0626953},
    {"id": "B15", "nombre": "Francisco Jose de Caldas - Suba", "localidad": "Suba", "lat": 4.74131, "lon": -74.08487},
    {"id": "B16", "nombre": "Usaquen - Servita", "localidad": "Usaquen", "lat": 4.7424075, "lon": -74.0240014},
    {"id": "B17", "nombre": "Virgilio Barco", "localidad": "Teusaquillo", "lat": 4.6570563, "lon": -74.0884676},
    {"id": "B18", "nombre": "Del Deporte", "localidad": "Chapinero", "lat": 4.6458367, "lon": -74.0783189},
    {"id": "B19", "nombre": "Las Ferias", "localidad": "Engativa", "lat": 4.6838037, "lon": -74.0892408},
    {"id": "B20", "nombre": "Publico Escolar La Marichuela", "localidad": "Usme", "lat": 4.5121741, "lon": -74.1176695},
    {"id": "B21", "nombre": "El Parque", "localidad": "Santa Fe", "lat": 4.622997, "lon": -74.0636059},
    {"id": "B22", "nombre": "Publico Escolar Pasquilla", "localidad": "Ciudad Bolivar", "lat": 4.4422499, "lon": -74.15722},
    {"id": "B23", "nombre": "De la Participacion Ciudadana", "localidad": "Barrios Unidos", "lat": 4.653634949779767, "lon": -74.06893921534338},
    {"id": "B24", "nombre": "El Mirador", "localidad": "Ciudad Bolivar", "lat": 4.55031, "lon": -74.15894},
    {"id": "B25", "nombre": "FUGA", "localidad": "La Candelaria", "lat": 4.595548710554031, "lon": -74.07265310465851},
    {"id": "B26", "nombre": "CEFE Fontanar del Rio", "localidad": "Suba", "lat": 4.754302677147163, "lon": -74.11082754883668},
    {"id": "B27", "nombre": "CEFE Cometas", "localidad": "Suba", "lat": 4.714476743302042, "lon": -74.08661441534338},
    {"id": "B28", "nombre": "Fontibon", "localidad": "Fontibon", "lat": 4.67357, "lon": -74.14423},
]
NODOS = {b["id"]: b for b in BIBLIOTECAS}

CACHE_ARCHIVO = "cache_distancias_reales.json"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


# -----------------------------------------------------------------------
# 2) ESTRUCTURA DEL GRAFO: Haversine solo decide qué nodos se conectan
# -----------------------------------------------------------------------
def distancia_haversine(lat1, lon1, lat2, lon2):
    """Distancia en línea recta (km). Se usa SOLO para elegir vecinos
    cercanos, NUNCA como el costo final de la arista."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _todas_las_distancias_lineales():
    ids = list(NODOS.keys())
    dist = {}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            d = distancia_haversine(NODOS[a]["lat"], NODOS[a]["lon"], NODOS[b]["lat"], NODOS[b]["lon"])
            dist[(a, b)] = d
            dist[(b, a)] = d
    return dist


def _mst_prim(dist, ids):
    """Árbol de Expansión Mínima (Prim) -> garantiza que el grafo sea conexo."""
    visitados = {ids[0]}
    aristas = set()
    restantes = set(ids[1:])
    while restantes:
        mejor = None
        for u in visitados:
            for v in restantes:
                d = dist[(u, v)]
                if mejor is None or d < mejor[2]:
                    mejor = (u, v, d)
        u, v, d = mejor
        aristas.add(tuple(sorted((u, v))))
        visitados.add(v)
        restantes.remove(v)
    return aristas


def _estructura_del_grafo(k_vecinos=3):
    """Decide QUÉ conexiones existen (no sus pesos), combinando MST + KNN
    sobre distancia en línea recta."""
    ids = list(NODOS.keys())
    dist = _todas_las_distancias_lineales()
    aristas = set(_mst_prim(dist, ids))
    for u in ids:
        vecinos = sorted((v for v in ids if v != u), key=lambda v: dist[(u, v)])
        for v in vecinos[:k_vecinos]:
            aristas.add(tuple(sorted((u, v))))
    return aristas


# -----------------------------------------------------------------------
# 3) COSTO DE CADA ARISTA: distancia REAL por calle (OSRM), con cache
# -----------------------------------------------------------------------
def _cargar_cache():
    if os.path.exists(CACHE_ARCHIVO):
        with open(CACHE_ARCHIVO, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _guardar_cache(cache):
    with open(CACHE_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _distancia_real_osrm(a, b):
    """Consulta OSRM (routing real por calles) y devuelve la distancia en km."""
    na, nb = NODOS[a], NODOS[b]
    url = f"{OSRM_URL}/{na['lon']},{na['lat']};{nb['lon']},{nb['lat']}?overview=false"
    headers = {"User-Agent": "proyecto-mapa-ia-bogota/1.0 (uso academico)"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    metros = resp.json()["routes"][0]["distance"]
    return round(metros / 1000, 2)


def _costo_real(a, b, cache):
    """Devuelve la distancia real por calle entre a y b, usando cache si
    ya existe; si no, consulta OSRM y guarda el resultado."""
    clave = f"{a}-{b}"
    clave_inversa = f"{b}-{a}"
    if clave in cache:
        return cache[clave]
    if clave_inversa in cache:
        return cache[clave_inversa]

    try:
        d = _distancia_real_osrm(a, b)
    except Exception as e:
        # Si OSRM falla (sin internet, servidor caído, etc.) usamos la
        # distancia en línea recta como respaldo, avisando en consola.
        d = round(distancia_haversine(NODOS[a]["lat"], NODOS[a]["lon"], NODOS[b]["lat"], NODOS[b]["lon"]), 2)
        print(f"  [!] OSRM fallo para {a}-{b} ({e}); uso linea recta como respaldo: {d} km")

    cache[clave] = d
    return d


# -----------------------------------------------------------------------
# 4) CONSTRUIR EL GRAFO FINAL: estructura (Haversine) + costo (real)
# -----------------------------------------------------------------------
def construir_grafo(k_vecinos=3):
    """
    Devuelve el grafo como diccionario de adyacencia:
        grafo["B01"] = [("B03", 4.82), ("B04", 6.10), ...]
    donde el número es la distancia REAL por calle en km.
    """
    aristas = _estructura_del_grafo(k_vecinos)
    cache = _cargar_cache()

    faltantes = [par for par in aristas if f"{par[0]}-{par[1]}" not in cache and f"{par[1]}-{par[0]}" not in cache]
    if faltantes:
        print(f"Consultando distancia real por calle para {len(faltantes)} conexiones nuevas...")

    grafo = defaultdict(list)
    for u, v in aristas:
        d = _costo_real(u, v, cache)
        grafo[u].append((v, d))
        grafo[v].append((u, d))

    if faltantes:
        _guardar_cache(cache)

    for u in grafo:
        grafo[u].sort(key=lambda par: par[0])

    return dict(grafo)


def cargar_desde_excel(ruta="bibliotecas_bogota_final.xlsx"):
    """Opcional: regenera la base de conocimiento leyendo el Excel original."""
    import openpyxl
    wb = openpyxl.load_workbook(ruta, data_only=True)
    ws = wb["Bibliotecas Bogota"]
    filas = list(ws.iter_rows(min_row=2, values_only=True))
    nuevos = []
    for fila in filas:
        idb, nombre, localidad, direccion, tipo, estado, lat, lon = fila
        nuevos.append({"id": idb, "nombre": nombre, "localidad": localidad, "lat": lat, "lon": lon})
    return nuevos


if __name__ == "__main__":
    g = construir_grafo()
    total_aristas = sum(len(v) for v in g.values()) // 2
    print(f"\nNodos (bibliotecas): {len(NODOS)}")
    print(f"Aristas (conexiones con distancia real por calle): {total_aristas}")
    for nodo, vecinos in g.items():
        print(nodo, "->", vecinos)