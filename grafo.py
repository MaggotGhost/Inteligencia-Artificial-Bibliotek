"""
grafo.py
--------
Base de conocimiento (hechos) y construcción del grafo de bibliotecas de Bogotá.

- Los NODOS son las bibliotecas (con su localidad, dirección y coordenadas reales).
- Las ARISTAS se calculan con la distancia real entre bibliotecas (formula de
  Haversine, en kilómetros) y representan el COSTO de moverse de una biblioteca
  a otra. El grafo se construye conectando cada biblioteca con sus vecinas más
  cercanas (K-Nearest Neighbors) y garantizando que sea conexo con un Árbol de
  Expansión Mínima (Prim), tal como se pide: "tengo que poner las distancias y
  base de conocimiento".

Este módulo NO depende del Excel para funcionar (los datos están embebidos como
base de conocimiento), pero incluye una función opcional para regenerarlos desde
el archivo bibliotecas_bogota_final.xlsx si el usuario actualiza la información.
"""

import math
from collections import defaultdict

# ---------------------------------------------------------------------------
# 1) BASE DE CONOCIMIENTO: hechos sobre las bibliotecas (nodos del problema)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# 2) COSTO ENTRE NODOS: distancia real (km) con la formula de Haversine
# ---------------------------------------------------------------------------
def distancia_haversine(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos puntos (lat, lon) sobre la superficie terrestre."""
    R = 6371.0  # radio de la Tierra en km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# 3) CONSTRUCCION DEL GRAFO (aristas ponderadas por distancia)
#    - K vecinos mas cercanos por nodo (grafo "realista": cada biblioteca solo
#      se conecta con las bibliotecas cercanas, no con todas).
#    - Arbol de Expansion Minima (Prim) agregado encima para GARANTIZAR que el
#      grafo sea conexo (todas las bibliotecas se pueden alcanzar entre si).
# ---------------------------------------------------------------------------
def _todas_las_distancias():
    ids = list(NODOS.keys())
    dist = {}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            d = distancia_haversine(NODOS[a]["lat"], NODOS[a]["lon"], NODOS[b]["lat"], NODOS[b]["lon"])
            dist[(a, b)] = d
            dist[(b, a)] = d
    return dist


def _mst_prim(dist, ids):
    """Arbol de expansion minima con el algoritmo de Prim. Devuelve set de aristas."""
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


def construir_grafo(k_vecinos=3):
    """
    Construye el grafo como diccionario de adyacencia:
        grafo["B01"] = [("B03", 4.82), ("B04", 6.10), ...]
    El costo de cada arista es la distancia real en km (redondeada a 2 decimales).
    """
    ids = list(NODOS.keys())
    dist = _todas_las_distancias()

    aristas = set(_mst_prim(dist, ids))  # garantiza conexidad

    # K vecinos mas cercanos por nodo (grafo mas realista, con varios caminos)
    for u in ids:
        vecinos = sorted((v for v in ids if v != u), key=lambda v: dist[(u, v)])
        for v in vecinos[:k_vecinos]:
            aristas.add(tuple(sorted((u, v))))

    grafo = defaultdict(list)
    for u, v in aristas:
        d = round(dist[(u, v)], 2)
        grafo[u].append((v, d))
        grafo[v].append((u, d))

    # ordenar vecinos por id para que la exploracion sea determinista
    for u in grafo:
        grafo[u].sort(key=lambda par: par[0])

    return dict(grafo)


def cargar_desde_excel(ruta="data_bibliotecas_bogota.xlsx"):
    """
    Opcional: si el usuario actualiza el Excel, esta funcion regenera la
    base de conocimiento (BIBLIOTECAS/NODOS) leyendo el archivo original.
    Requiere openpyxl.
    """
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
    print(f"Nodos (bibliotecas): {len(NODOS)}")
    print(f"Aristas (conexiones con distancia): {total_aristas}")
    for nodo, vecinos in g.items():
        print(nodo, "->", vecinos)
