"""Comprobaciones automaticas del proyecto de rutas entre bibliotecas."""

from collections import deque
import heapq
from pathlib import Path

from busquedas import busqueda_anchura, busqueda_costo_uniforme
from grafo import NODOS, cargar_desde_excel, construir_grafo


def costo_minimo_referencia(grafo, origen, destino):
    """Calcula el costo minimo de forma independiente a la implementacion UCS."""
    frontera = [(0.0, origen)]
    mejores = {origen: 0.0}

    while frontera:
        costo, actual = heapq.heappop(frontera)
        if costo != mejores[actual]:
            continue
        if actual == destino:
            return costo

        for vecino, peso in grafo[actual]:
            nuevo_costo = costo + peso
            if nuevo_costo < mejores.get(vecino, float("inf")):
                mejores[vecino] = nuevo_costo
                heapq.heappush(frontera, (nuevo_costo, vecino))

    return None


def validar_conectividad(grafo):
    visitados = {next(iter(grafo))}
    frontera = deque(visitados)
    while frontera:
        actual = frontera.popleft()
        for vecino, _peso in grafo[actual]:
            if vecino not in visitados:
                visitados.add(vecino)
                frontera.append(vecino)
    return len(visitados) == len(grafo)


def main():
    grafo = construir_grafo()
    assert len(NODOS) == 28, "La base de conocimiento debe tener 28 bibliotecas"
    assert len(grafo) == len(NODOS), "Hay bibliotecas sin conexiones"
    assert validar_conectividad(grafo), "El grafo no es conexo"
    assert all(peso > 0 for vecinos in grafo.values() for _vecino, peso in vecinos)

    bfs = busqueda_anchura(grafo, "B13", "B26")
    ucs = busqueda_costo_uniforme(grafo, "B13", "B26")
    assert bfs.encontrado and ucs.encontrado, "No se encontro la ruta de prueba"
    assert round(bfs.costo_total, 2) == 100.90
    assert round(ucs.costo_total, 2) == 95.83
    assert ucs.costo_total <= bfs.costo_total

    for origen in NODOS:
        for destino in NODOS:
            resultado = busqueda_costo_uniforme(grafo, origen, destino)
            esperado = costo_minimo_referencia(grafo, origen, destino)
            assert resultado.encontrado
            assert abs(resultado.costo_total - esperado) < 1e-9

    excel = Path("bibliotecas_bogota_final.xlsx")
    assert excel.exists(), "No se encontro el Excel de la base de datos"
    assert len(cargar_desde_excel(excel)) == len(NODOS)
    print("OK: grafo, BFS, UCS, distancias y Excel verificados.")


if __name__ == "__main__":
    main()