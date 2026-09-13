"""
mapa_interactivo.py
--------------------
Genera un mapa HTML interactivo (con folium) sobre el mapa REAL de Bogota,
mostrando todas las bibliotecas, todas las conexiones del grafo y resaltando
la ruta encontrada por el algoritmo elegido entre un origen y un destino.

No requiere Tkinter: el resultado es un archivo .html que se abre en
cualquier navegador. Sirve como complemento visual de interfaz.py / main.py.

Ejecutar con:  python3 mapa_interactivo.py
"""

import folium

from grafo import construir_grafo, NODOS
from busquedas import busqueda_anchura, busqueda_costo_uniforme


def generar_mapa(origen="B01", destino="B16", algoritmo="ucs", archivo_salida="mapa_bibliotecas_bogota.html"):
    grafo = construir_grafo()

    if algoritmo == "bfs":
        resultado = busqueda_anchura(grafo, origen, destino)
    else:
        resultado = busqueda_costo_uniforme(grafo, origen, destino)

    centro = [4.65, -74.1]
    mapa = folium.Map(location=centro, zoom_start=11, tiles="OpenStreetMap")

    # todas las conexiones del grafo (gris, delgadas)
    dibujadas = set()
    for u, vecinos in grafo.items():
        for v, peso in vecinos:
            par = tuple(sorted((u, v)))
            if par in dibujadas:
                continue
            dibujadas.add(par)
            folium.PolyLine(
                locations=[(NODOS[u]["lat"], NODOS[u]["lon"]), (NODOS[v]["lat"], NODOS[v]["lon"])],
                color="lightgray", weight=1.5, opacity=0.7,
                tooltip=f"{u} - {v}: {peso} km",
            ).add_to(mapa)

    # todas las bibliotecas (marcadores azules)
    for b in NODOS.values():
        folium.CircleMarker(
            location=(b["lat"], b["lon"]),
            radius=5,
            color="#4C72B0",
            fill=True,
            fill_opacity=0.9,
            popup=f"{b['id']} - {b['nombre']} ({b['localidad']})",
        ).add_to(mapa)

    # ruta encontrada (roja, resaltada) y marcadores de inicio/fin
    if resultado.encontrado:
        puntos = [(NODOS[n]["lat"], NODOS[n]["lon"]) for n in resultado.camino]
        folium.PolyLine(locations=puntos, color="crimson", weight=5, opacity=0.9).add_to(mapa)

        folium.Marker(
            location=puntos[0], popup=f"ORIGEN: {NODOS[origen]['nombre']}",
            icon=folium.Icon(color="green", icon="play"),
        ).add_to(mapa)
        folium.Marker(
            location=puntos[-1], popup=f"DESTINO: {NODOS[destino]['nombre']}",
            icon=folium.Icon(color="red", icon="flag"),
        ).add_to(mapa)

        titulo = (
            f"<h4 style='margin:6px'>{resultado.algoritmo}: {origen} → {destino} "
            f"| Costo: {resultado.costo_total:.2f} km | "
            f"Nodos expandidos: {resultado.nodos_expandidos}</h4>"
        )
    else:
        titulo = f"<h4 style='margin:6px'>No se encontro camino entre {origen} y {destino}</h4>"

    mapa.get_root().html.add_child(folium.Element(titulo))
    mapa.save(archivo_salida)
    print(f"Mapa guardado en: {archivo_salida}")
    print(resultado.resumen())
    return archivo_salida


if __name__ == "__main__":
    generar_mapa(origen="B06", destino="B08", algoritmo="bfs",
                 archivo_salida="mapa_bfs_B06_B08.html")
    generar_mapa(origen="B06", destino="B08", algoritmo="ucs",
                 archivo_salida="mapa_ucs_B06_B08.html")