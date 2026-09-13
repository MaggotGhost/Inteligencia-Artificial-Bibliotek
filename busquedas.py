"""
busquedas.py
------------
Implementacion de los dos algoritmos de busqueda no informada pedidos:

  - Busqueda primero en anchura (BFS)
  - Busqueda de costo uniforme (UCS)

Ambas funciones devuelven un objeto ResultadoBusqueda con:
  camino            -> lista de IDs de biblioteca desde el origen hasta el destino
  costo_total       -> suma de las distancias (km) del camino encontrado
  nodos_expandidos  -> cuantos nodos se sacaron de la frontera y se expandieron
  nodos_generados   -> cuantos nodos se generaron y se metieron a la frontera
  orden_visita      -> orden en que se expandieron los nodos (para explicar el algoritmo)

Estas metricas son justamente las que se piden evaluar en las estrategias de
busqueda: completitud, complejidad temporal (nodos generados/expandidos),
complejidad espacial (maximo de nodos en memoria) y optimalidad.
"""

from collections import deque
import heapq
from dataclasses import dataclass, field


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
        ruta = " -> ".join(self.camino)
        return (
            f"[{self.algoritmo}] {self.origen} -> {self.destino}\n"
            f"  Camino: {ruta}\n"
            f"  Costo total (km): {self.costo_total:.2f}\n"
            f"  Nodos expandidos: {self.nodos_expandidos}\n"
            f"  Nodos generados: {self.nodos_generados}\n"
            f"  Maximo de nodos en memoria (complejidad espacial): {self.max_nodos_en_memoria}"
        )


def _reconstruir_camino(padres, destino):
    camino = [destino]
    while camino[-1] in padres:
        camino.append(padres[camino[-1]])
    camino.reverse()
    return camino


def busqueda_anchura(grafo, origen, destino):
    """
    BFS: explora nivel por nivel (por eso 'anchura'). Es completa y optima
    SOLO si todas las aristas tuvieran el mismo costo; aqui la usamos para
    encontrar el camino con MENOS BIBLIOTECAS INTERMEDIAS (menor numero de
    saltos), no necesariamente el de menor distancia.
    """
    if origen not in grafo or destino not in grafo:
        return ResultadoBusqueda("Busqueda en Anchura (BFS)", origen, destino, [], 0, 0, 0, 0, [], False)

    frontera = deque([origen])
    visitados = {origen}
    padres = {}
    orden_visita = []
    nodos_expandidos = 0
    nodos_generados = 1
    max_memoria = 1

    while frontera:
        max_memoria = max(max_memoria, len(frontera))
        actual = frontera.popleft()
        orden_visita.append(actual)
        nodos_expandidos += 1

        if actual == destino:
            camino = _reconstruir_camino(padres, destino)
            costo = _costo_de_camino(grafo, camino)
            return ResultadoBusqueda(
                "Busqueda en Anchura (BFS)", origen, destino, camino, costo,
                nodos_expandidos, nodos_generados, max_memoria, orden_visita, True
            )

        for vecino, _peso in grafo[actual]:
            if vecino not in visitados:
                visitados.add(vecino)
                padres[vecino] = actual
                frontera.append(vecino)
                nodos_generados += 1

    return ResultadoBusqueda("Busqueda en Anchura (BFS)", origen, destino, [], 0,
                              nodos_expandidos, nodos_generados, max_memoria, orden_visita, False)


def busqueda_costo_uniforme(grafo, origen, destino):
    """
    UCS: siempre expande el nodo de la frontera con MENOR costo acumulado
    (como Dijkstra). Es completa y optima: siempre encuentra el camino de
    menor distancia total, no el de menos saltos.
    """
    if origen not in grafo or destino not in grafo:
        return ResultadoBusqueda("Costo Uniforme (UCS)", origen, destino, [], 0, 0, 0, 0, [], False)

    contador = 0  # para desempatar en el heap de forma estable
    frontera = [(0, contador, origen)]
    costo_acumulado = {origen: 0}
    padres = {}
    visitados = set()
    orden_visita = []
    nodos_expandidos = 0
    nodos_generados = 1
    max_memoria = 1

    while frontera:
        max_memoria = max(max_memoria, len(frontera))
        costo, _, actual = heapq.heappop(frontera)

        if actual in visitados:
            continue
        visitados.add(actual)
        orden_visita.append(actual)
        nodos_expandidos += 1

        if actual == destino:
            camino = _reconstruir_camino(padres, destino)
            return ResultadoBusqueda(
                "Costo Uniforme (UCS)", origen, destino, camino, costo,
                nodos_expandidos, nodos_generados, max_memoria, orden_visita, True
            )

        for vecino, peso in grafo[actual]:
            nuevo_costo = costo + peso
            if vecino not in costo_acumulado or nuevo_costo < costo_acumulado[vecino]:
                costo_acumulado[vecino] = nuevo_costo
                padres[vecino] = actual
                contador += 1
                heapq.heappush(frontera, (nuevo_costo, contador, vecino))
                nodos_generados += 1

    return ResultadoBusqueda("Costo Uniforme (UCS)", origen, destino, [], 0,
                              nodos_expandidos, nodos_generados, max_memoria, orden_visita, False)


def _costo_de_camino(grafo, camino):
    total = 0.0
    for u, v in zip(camino, camino[1:]):
        for vecino, peso in grafo[u]:
            if vecino == v:
                total += peso
                break
    return total


if __name__ == "__main__":
    from grafo import construir_grafo
    g = construir_grafo()
    r1 = busqueda_anchura(g, "B01", "B16")
    r2 = busqueda_costo_uniforme(g, "B01", "B16")
    print(r1.resumen())
    print()
    print(r2.resumen())
