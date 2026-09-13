"""
main.py
-------
Interfaz por consola (no requiere Tkinter, funciona en cualquier maquina).
Util como alternativa a interfaz.py o para probar el proyecto rapido.

Ejecutar con:  python3 main.py
"""

from grafo import construir_grafo, NODOS
from busquedas import busqueda_anchura, busqueda_costo_uniforme


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


def main():
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
