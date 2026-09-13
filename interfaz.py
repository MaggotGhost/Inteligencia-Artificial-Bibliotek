"""
interfaz.py
-----------
Interfaz grafica (Tkinter) para el proyecto de busqueda en el mapa de
bibliotecas de Bogota.

El usuario elige:
  - Biblioteca de origen
  - Biblioteca de destino
  - Algoritmo: Busqueda en Anchura (BFS) o Costo Uniforme (UCS)

Y obtiene:
  - El camino encontrado (lista de bibliotecas)
  - El costo total en km
  - Estadisticas del algoritmo (nodos expandidos/generados, memoria maxima)
  - Un mapa (matplotlib) con todas las bibliotecas y la ruta resaltada

Ejecutar con:  python3 interfaz.py
"""

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from grafo import construir_grafo, NODOS
from busquedas import busqueda_anchura, busqueda_costo_uniforme


class AppBibliotecas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rutas entre bibliotecas de Bogota - BFS vs Costo Uniforme")
        self.geometry("1100x700")

        self.grafo = construir_grafo()
        self.opciones = {f"{b['id']} - {b['nombre']} ({b['localidad']})": b["id"] for b in NODOS.values()}
        etiquetas = list(self.opciones.keys())

        # -------- Panel de controles --------
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

        # -------- Panel de resultados --------
        self.texto_resultado = tk.Text(self, height=8, wrap="word")
        self.texto_resultado.pack(side="top", fill="x", padx=10, pady=5)

        # -------- Mapa --------
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True, padx=10, pady=5)

        self.dibujar_mapa_base()

    def dibujar_mapa_base(self, camino=None):
        self.ax.clear()
        lons = [b["lon"] for b in NODOS.values()]
        lats = [b["lat"] for b in NODOS.values()]
        self.ax.scatter(lons, lats, c="#4C72B0", s=40, zorder=2)

        for b in NODOS.values():
            self.ax.annotate(b["id"], (b["lon"], b["lat"]), fontsize=7,
                              xytext=(3, 3), textcoords="offset points")

        # todas las conexiones del grafo, en gris claro
        dibujadas = set()
        for u, vecinos in self.grafo.items():
            for v, _peso in vecinos:
                par = tuple(sorted((u, v)))
                if par in dibujadas:
                    continue
                dibujadas.add(par)
                self.ax.plot(
                    [NODOS[u]["lon"], NODOS[v]["lon"]],
                    [NODOS[u]["lat"], NODOS[v]["lat"]],
                    color="lightgray", linewidth=0.8, zorder=1,
                )

        if camino:
            xs = [NODOS[n]["lon"] for n in camino]
            ys = [NODOS[n]["lat"] for n in camino]
            self.ax.plot(xs, ys, color="crimson", linewidth=2.5, zorder=3)
            self.ax.scatter(xs, ys, color="crimson", s=60, zorder=4)

        self.ax.set_title("Mapa de bibliotecas de Bogota")
        self.ax.set_xlabel("Longitud")
        self.ax.set_ylabel("Latitud")
        self.canvas.draw()

    def buscar_ruta(self):
        origen_id = self.opciones[self.combo_origen.get()]
        destino_id = self.opciones[self.combo_destino.get()]

        if origen_id == destino_id:
            messagebox.showwarning("Aviso", "Elige dos bibliotecas distintas.")
            return

        if self.algoritmo.get() == "bfs":
            resultado = busqueda_anchura(self.grafo, origen_id, destino_id)
        else:
            resultado = busqueda_costo_uniforme(self.grafo, origen_id, destino_id)

        self.texto_resultado.delete("1.0", tk.END)
        if not resultado.encontrado:
            self.texto_resultado.insert(tk.END, "No se encontro un camino entre esas bibliotecas.")
            self.dibujar_mapa_base()
            return

        nombres_camino = " -> ".join(f"{NODOS[n]['id']} ({NODOS[n]['nombre']})" for n in resultado.camino)
        self.texto_resultado.insert(tk.END, resultado.resumen() + "\n\n")
        self.texto_resultado.insert(tk.END, f"Ruta detallada:\n{nombres_camino}")

        self.dibujar_mapa_base(camino=resultado.camino)


if __name__ == "__main__":
    app = AppBibliotecas()
    app.mainloop()
