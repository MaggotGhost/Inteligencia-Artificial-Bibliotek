"""Aplicacion completa de rutas entre bibliotecas de Bogota.

Uso:
    python main.py                 # consola
    python main.py --gui            # interfaz Tkinter y Matplotlib
    python main.py --mapa           # genera mapas HTML BFS y UCS
    python main.py --validar        # ejecuta las comprobaciones
"""

import argparse
import heapq
import json
import math
import os
from collections import defaultdict, deque
from dataclasses import dataclass, field


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
NODOS = {biblioteca["id"]: biblioteca for biblioteca in BIBLIOTECAS}
CACHE_ARCHIVO = "cache_distancias_reales.json"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def distancia_haversine(lat1, lon1, lat2, lon2):
    radio_tierra = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radio_tierra * math.asin(math.sqrt(a))


def _estructura_del_grafo(k_vecinos=3):
    ids = list(NODOS)
    distancias = {}
    for indice, origen in enumerate(ids):
        for destino in ids[indice + 1:]:
            distancia = distancia_haversine(NODOS[origen]["lat"], NODOS[origen]["lon"], NODOS[destino]["lat"], NODOS[destino]["lon"])
            distancias[(origen, destino)] = distancia
            distancias[(destino, origen)] = distancia

    visitados = {ids[0]}
    restantes = set(ids[1:])
    aristas = set()
    while restantes:
        origen, destino, _ = min(
            (u, v, distancias[(u, v)])
            for u in visitados for v in restantes
        )
        aristas.add(tuple(sorted((origen, destino))))
        visitados.add(destino)
        restantes.remove(destino)

    for origen in ids:
        vecinos = sorted(
            (destino for destino in ids if destino != origen),
            key=lambda destino: distancias[(origen, destino)],
        )
        for destino in vecinos[:k_vecinos]:
            aristas.add(tuple(sorted((origen, destino))))
    return aristas


def _cargar_cache():
    if os.path.exists(CACHE_ARCHIVO):
        with open(CACHE_ARCHIVO, encoding="utf-8") as archivo:
            return json.load(archivo)
    return {}


def _guardar_cache(cache):
    with open(CACHE_ARCHIVO, "w", encoding="utf-8") as archivo:
        json.dump(cache, archivo, ensure_ascii=False, indent=2)


def _costo_real(origen, destino, cache):
    clave = f"{origen}-{destino}"
    inversa = f"{destino}-{origen}"
    if clave in cache:
        return cache[clave]
    if inversa in cache:
        return cache[inversa]

    try:
        import requests
        a, b = NODOS[origen], NODOS[destino]
        url = f"{OSRM_URL}/{a['lon']},{a['lat']};{b['lon']},{b['lat']}?overview=false"
        respuesta = requests.get(url, headers={"User-Agent": "proyecto-mapa-ia-bogota/1.0"}, timeout=30)
        respuesta.raise_for_status()
        distancia = round(respuesta.json()["routes"][0]["distance"] / 1000, 2)
    except Exception as error:
        distancia = round(distancia_haversine(NODOS[origen]["lat"], NODOS[origen]["lon"], NODOS[destino]["lat"], NODOS[destino]["lon"]), 2)
        print(f"  [!] OSRM fallo para {origen}-{destino} ({error}); uso linea recta: {distancia} km")
    cache[clave] = distancia
    return distancia


def construir_grafo(k_vecinos=3):
    cache = _cargar_cache()
    aristas = _estructura_del_grafo(k_vecinos)
    faltantes = [par for par in aristas if f"{par[0]}-{par[1]}" not in cache and f"{par[1]}-{par[0]}" not in cache]
    if faltantes:
        print(f"Consultando distancia real por calle para {len(faltantes)} conexiones nuevas...")

    grafo = defaultdict(list)
    for origen, destino in aristas:
        distancia = _costo_real(origen, destino, cache)
        grafo[origen].append((destino, distancia))
        grafo[destino].append((origen, distancia))
    if faltantes:
        _guardar_cache(cache)
    return {nodo: sorted(vecinos) for nodo, vecinos in grafo.items()}


@dataclass
class ResultadoBusqueda:
    algoritmo: str
    origen: str
    destino: str
    camino: list
    costo_total: float
    nodos_expandidos: int
    nodos_generados: int
    max_nodos_en_memoria: int
    orden_visita: list = field(default_factory=list)
    encontrado: bool = True

    def resumen(self):
        if not self.encontrado:
            return f"[{self.algoritmo}] No existe camino entre {self.origen} y {self.destino}."
        return (f"[{self.algoritmo}] {self.origen} -> {self.destino}\n"
                f"  Camino: {' -> '.join(self.camino)}\n"
                f"  Costo total (km): {self.costo_total:.2f}\n"
                f"  Nodos expandidos: {self.nodos_expandidos}\n"
                f"  Nodos generados: {self.nodos_generados}\n"
                f"  Maximo de nodos en memoria: {self.max_nodos_en_memoria}")


def _resultado_fallido(algoritmo, origen, destino):
    return ResultadoBusqueda(algoritmo, origen, destino, [], 0, 0, 0, 0, [], False)


def _reconstruir_camino(padres, destino):
    camino = [destino]
    while camino[-1] in padres:
        camino.append(padres[camino[-1]])
    return list(reversed(camino))


def _costo_de_camino(grafo, camino):
    return sum(next(peso for vecino, peso in grafo[origen] if vecino == destino)
               for origen, destino in zip(camino, camino[1:]))


def busqueda_anchura(grafo, origen, destino):
    nombre = "Busqueda en Anchura (BFS)"
    if origen not in grafo or destino not in grafo:
        return _resultado_fallido(nombre, origen, destino)
    frontera, visitados = deque([origen]), {origen}
    padres, orden_visita = {}, []
    generados, max_memoria = 1, 1
    while frontera:
        max_memoria = max(max_memoria, len(frontera))
        actual = frontera.popleft()
        orden_visita.append(actual)
        if actual == destino:
            camino = _reconstruir_camino(padres, destino)
            return ResultadoBusqueda(nombre, origen, destino, camino, _costo_de_camino(grafo, camino), len(orden_visita), generados, max_memoria, orden_visita)
        for vecino, _ in grafo[actual]:
            if vecino not in visitados:
                visitados.add(vecino)
                padres[vecino] = actual
                frontera.append(vecino)
                generados += 1
    return ResultadoBusqueda(nombre, origen, destino, [], 0, len(orden_visita), generados, max_memoria, orden_visita, False)


def busqueda_costo_uniforme(grafo, origen, destino):
    nombre = "Costo Uniforme (UCS)"
    if origen not in grafo or destino not in grafo:
        return _resultado_fallido(nombre, origen, destino)
    contador, frontera = 0, [(0, 0, origen)]
    costos, padres, visitados, orden_visita = {origen: 0}, {}, set(), []
    generados, max_memoria = 1, 1
    while frontera:
        max_memoria = max(max_memoria, len(frontera))
        costo, _, actual = heapq.heappop(frontera)
        if actual in visitados:
            continue
        visitados.add(actual)
        orden_visita.append(actual)
        if actual == destino:
            return ResultadoBusqueda(nombre, origen, destino, _reconstruir_camino(padres, destino), costo, len(orden_visita), generados, max_memoria, orden_visita)
        for vecino, peso in grafo[actual]:
            nuevo_costo = costo + peso
            if nuevo_costo < costos.get(vecino, float("inf")):
                costos[vecino], padres[vecino] = nuevo_costo, actual
                contador += 1
                heapq.heappush(frontera, (nuevo_costo, contador, vecino))
                generados += 1
    return ResultadoBusqueda(nombre, origen, destino, [], 0, len(orden_visita), generados, max_memoria, orden_visita, False)


def listar_bibliotecas():
    print("\nBibliotecas disponibles:")
    for b in NODOS.values():
        print(f"  {b['id']}  {b['nombre']:<45} ({b['localidad']})")


def pedir_id(mensaje):
    while True:
        valor = input(mensaje).strip().upper()
        if valor in NODOS:
            return valor
        print("  ID invalido. Debe ser como B01, B02, ... B28.")


def generar_mapa(origen="B01", destino="B16", algoritmo="ucs", archivo_salida="mapa_bibliotecas_bogota.html"):
    import folium

    grafo = construir_grafo()
    resultado = (busqueda_anchura(grafo, origen, destino)
                 if algoritmo == "bfs"
                 else busqueda_costo_uniforme(grafo, origen, destino))
    mapa = folium.Map(location=[4.65, -74.1], zoom_start=11, tiles="OpenStreetMap")
    dibujadas = set()
    for nodo, vecinos in grafo.items():
        for vecino, peso in vecinos:
            par = tuple(sorted((nodo, vecino)))
            if par in dibujadas:
                continue
            dibujadas.add(par)
            folium.PolyLine(
                [(NODOS[nodo]["lat"], NODOS[nodo]["lon"]), (NODOS[vecino]["lat"], NODOS[vecino]["lon"])],
                color="lightgray", weight=1.5, opacity=0.7,
                tooltip=f"{nodo} - {vecino}: {peso} km",
            ).add_to(mapa)
    for biblioteca in NODOS.values():
        folium.CircleMarker(
            (biblioteca["lat"], biblioteca["lon"]), radius=5, color="#4C72B0",
            fill=True, fill_opacity=0.9,
            popup=f"{biblioteca['id']} - {biblioteca['nombre']} ({biblioteca['localidad']})",
        ).add_to(mapa)
    if resultado.encontrado:
        puntos = [(NODOS[nodo]["lat"], NODOS[nodo]["lon"]) for nodo in resultado.camino]
        folium.PolyLine(puntos, color="crimson", weight=5, opacity=0.9).add_to(mapa)
        folium.Marker(puntos[0], popup=f"ORIGEN: {NODOS[origen]['nombre']}", icon=folium.Icon(color="green", icon="play")).add_to(mapa)
        folium.Marker(puntos[-1], popup=f"DESTINO: {NODOS[destino]['nombre']}", icon=folium.Icon(color="red", icon="flag")).add_to(mapa)
        titulo = f"<h4 style='margin:6px'>{resultado.algoritmo}: {origen} -> {destino} | Costo: {resultado.costo_total:.2f} km</h4>"
    else:
        titulo = f"<h4 style='margin:6px'>No se encontro camino entre {origen} y {destino}</h4>"
    mapa.get_root().html.add_child(folium.Element(titulo))
    mapa.save(archivo_salida)
    print(f"Mapa guardado en: {archivo_salida}")
    print(resultado.resumen())


def iniciar_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    class AppBibliotecas(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Rutas entre bibliotecas de Bogota - BFS vs Costo Uniforme")
            self.geometry("1100x700")
            self.grafo = construir_grafo()
            self.opciones = {f"{b['id']} - {b['nombre']} ({b['localidad']})": b["id"] for b in NODOS.values()}
            etiquetas = list(self.opciones)
            panel = ttk.Frame(self, padding=10)
            panel.pack(side="top", fill="x")
            ttk.Label(panel, text="Origen:").grid(row=0, column=0, sticky="w")
            self.combo_origen = ttk.Combobox(panel, values=etiquetas, width=45, state="readonly")
            self.combo_origen.grid(row=0, column=1, padx=5)
            self.combo_origen.current(0)
            ttk.Label(panel, text="Destino:").grid(row=0, column=2, sticky="w")
            self.combo_destino = ttk.Combobox(panel, values=etiquetas, width=45, state="readonly")
            self.combo_destino.grid(row=0, column=3, padx=5)
            self.combo_destino.current(15)
            ttk.Label(panel, text="Algoritmo:").grid(row=1, column=0, sticky="w", pady=8)
            self.algoritmo = tk.StringVar(value="ucs")
            ttk.Radiobutton(panel, text="Busqueda en Anchura (BFS)", variable=self.algoritmo, value="bfs").grid(row=1, column=1, sticky="w")
            ttk.Radiobutton(panel, text="Costo Uniforme (UCS)", variable=self.algoritmo, value="ucs").grid(row=1, column=2, sticky="w")
            ttk.Button(panel, text="Buscar ruta", command=self.buscar_ruta).grid(row=1, column=3, sticky="e")
            self.texto_resultado = tk.Text(self, height=8, wrap="word")
            self.texto_resultado.pack(side="top", fill="x", padx=10, pady=5)
            self.fig, self.ax = plt.subplots(figsize=(8, 6))
            self.canvas = FigureCanvasTkAgg(self.fig, master=self)
            self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True, padx=10, pady=5)
            self.dibujar_mapa()

        def dibujar_mapa(self, camino=None):
            self.ax.clear()
            self.ax.scatter([b["lon"] for b in NODOS.values()], [b["lat"] for b in NODOS.values()], c="#4C72B0", s=40, zorder=2)
            for biblioteca in NODOS.values():
                self.ax.annotate(biblioteca["id"], (biblioteca["lon"], biblioteca["lat"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
            dibujadas = set()
            for nodo, vecinos in self.grafo.items():
                for vecino, _ in vecinos:
                    par = tuple(sorted((nodo, vecino)))
                    if par in dibujadas:
                        continue
                    dibujadas.add(par)
                    self.ax.plot([NODOS[nodo]["lon"], NODOS[vecino]["lon"]], [NODOS[nodo]["lat"], NODOS[vecino]["lat"]], color="lightgray", linewidth=0.8, zorder=1)
            if camino:
                self.ax.plot([NODOS[n]["lon"] for n in camino], [NODOS[n]["lat"] for n in camino], color="crimson", linewidth=2.5, zorder=3)
            self.ax.set_title("Mapa de bibliotecas de Bogota")
            self.ax.set_xlabel("Longitud")
            self.ax.set_ylabel("Latitud")
            self.canvas.draw()

        def buscar_ruta(self):
            origen = self.opciones[self.combo_origen.get()]
            destino = self.opciones[self.combo_destino.get()]
            if origen == destino:
                messagebox.showwarning("Aviso", "Elige dos bibliotecas distintas.")
                return
            resultado = (busqueda_anchura(self.grafo, origen, destino)
                         if self.algoritmo.get() == "bfs"
                         else busqueda_costo_uniforme(self.grafo, origen, destino))
            self.texto_resultado.delete("1.0", tk.END)
            self.texto_resultado.insert(tk.END, resultado.resumen())
            self.dibujar_mapa(resultado.camino if resultado.encontrado else None)

    AppBibliotecas().mainloop()


def validar():
    import openpyxl
    grafo = construir_grafo()
    assert len(NODOS) == 28
    assert len(grafo) == len(NODOS)
    visitados, frontera = {next(iter(grafo))}, deque([next(iter(grafo))])
    while frontera:
        actual = frontera.popleft()
        for vecino, _ in grafo[actual]:
            if vecino not in visitados:
                visitados.add(vecino)
                frontera.append(vecino)
    assert len(visitados) == len(grafo), "El grafo no es conexo"
    assert all(peso > 0 for vecinos in grafo.values() for _, peso in vecinos)
    bfs = busqueda_anchura(grafo, "B13", "B26")
    ucs = busqueda_costo_uniforme(grafo, "B13", "B26")
    assert bfs.encontrado and ucs.encontrado
    assert ucs.costo_total <= bfs.costo_total
    excel = "bibliotecas_bogota_final.xlsx"
    assert os.path.exists(excel), "No se encontro el Excel de la base de datos"
    wb = openpyxl.load_workbook(excel, read_only=True, data_only=True)
    assert wb["Bibliotecas Bogota"].max_row - 1 == len(NODOS)
    print("OK: grafo, BFS, UCS, distancias y Excel verificados.")


def main():
    parser = argparse.ArgumentParser(description="Rutas entre bibliotecas de Bogota")
    parser.add_argument("--gui", action="store_true", help="abrir interfaz grafica")
    parser.add_argument("--mapa", action="store_true", help="generar mapas HTML BFS y UCS")
    parser.add_argument("--validar", action="store_true", help="ejecutar validaciones")
    argumentos = parser.parse_args()
    if argumentos.gui:
        iniciar_gui()
        return
    if argumentos.mapa:
        generar_mapa("B06", "B08", "bfs", "mapa_bfs_B06_B08.html")
        generar_mapa("B06", "B08", "ucs", "mapa_ucs_B06_B08.html")
        return
    if argumentos.validar:
        validar()
        return
    grafo = construir_grafo()
    print("=== Rutas entre bibliotecas de Bogota (BFS vs Costo Uniforme) ===")
    listar_bibliotecas()

    origen = pedir_id("\nID de biblioteca de ORIGEN: ")
    destino = pedir_id("ID de biblioteca de DESTINO: ")

    print("\nAlgoritmo:")
    print("  1) Busqueda en Anchura (BFS)")
    print("  2) Costo Uniforme (UCS)")
    print("  3) Los dos (comparar)")
    opcion = input("Elige 1, 2 o 3: ").strip()

    if opcion in ("1", "3"):
        r = busqueda_anchura(grafo, origen, destino)
        print("\n" + r.resumen())
    if opcion in ("2", "3"):
        r = busqueda_costo_uniforme(grafo, origen, destino)
        print("\n" + r.resumen())


if __name__ == "__main__":
    main()
