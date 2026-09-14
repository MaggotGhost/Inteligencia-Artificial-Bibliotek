# Rutas entre bibliotecas de Bogotá — BFS vs Costo Uniforme

Proyecto en Python que modela las 28 bibliotecas públicas de Bogotá (datos del
Excel `bibliotecas_bogota_final.xlsx`) como un **grafo con costos reales** (distancia
en km, fórmula de Haversine) y resuelve el problema de encontrar rutas entre
dos bibliotecas usando dos algoritmos de **búsqueda no informada**:

- **Búsqueda en anchura (BFS)**
- **Búsqueda de costo uniforme (UCS)**

## Archivos

| Archivo | Contenido |
|---|---|
| `main.py` | Aplicación completa: datos, grafo, BFS, UCS, consola, interfaz gráfica, mapas HTML y validación |
| `bibliotecas_bogota_final.xlsx` | Excel original con los datos |
| `validar.py` | Comprobaciones automaticas del grafo, BFS, UCS, distancias y Excel |

## Cómo se construyó el grafo (la "base de conocimiento")

Los **nodos** son las bibliotecas (id, nombre, localidad, latitud, longitud).
El **costo de cada arista** es la distancia real en kilómetros entre dos
bibliotecas (fórmula de Haversine, sobre la esfera terrestre).

No conectamos cada biblioteca con TODAS las demás (no tendría sentido para un
problema de búsqueda), sino que:

1. Se calcula un **Árbol de Expansión Mínima** (algoritmo de Prim) para
   garantizar que el grafo sea **conexo** (siempre existe un camino entre dos
   bibliotecas cualesquiera).
2. Se agregan las conexiones a los **3 vecinos más cercanos** de cada
   biblioteca, para que existan varias rutas posibles entre dos puntos (si no,
   BFS y UCS siempre darían el mismo único camino).

Resultado: 28 nodos, 54 aristas ponderadas.

## Cómo ejecutar

```bash
pip install requests matplotlib folium openpyxl

# Verificar que el proyecto quedo bien
python validar.py

# Opción 1: consola (siempre funciona)
python main.py

# Opción 2: interfaz gráfica
python main.py --gui

# Opción 3: mapa interactivo HTML
python main.py --mapa

# Validar el proyecto
python main.py --validar
```

> Nota: `interfaz.py` usa Tkinter, que viene con Python pero en Linux a veces
> hay que instalarlo aparte: `sudo apt install python3-tk`.

La validacion debe terminar con:

```text
OK: grafo, BFS, UCS, distancias y Excel verificados.
```

La prueba usa `B13` como origen y `B26` como destino. BFS debe encontrar una
ruta de 100.90 km y UCS una de 95.83 km. La diferencia es esperada: BFS
minimiza la cantidad de saltos, mientras UCS minimiza la distancia acumulada.
Ademas, `validar.py` compara UCS con una implementacion independiente de
Dijkstra para todos los pares de bibliotecas.

## Relación con la teoría (diapositivas del curso)

- **Completitud**: BFS y UCS son ambas completas en este grafo (finito y con
  costos positivos): siempre encuentran una solución si existe.
- **Optimalidad**: BFS solo es óptima si todas las aristas tuvieran el mismo
  costo (no es el caso aquí: son distancias reales distintas). Por eso BFS
  encuentra el camino con **menos bibliotecas intermedias** (menos saltos),
  mientras que **UCS siempre encuentra el camino de menor distancia total**
  (analiza el costo acumulado, no la cantidad de pasos). Puedes comprobarlo
  ejecutando ambos algoritmos entre `B13` y `B26`: BFS da 100.90 km y UCS da
  95.83 km para el mismo origen/destino.
- **Complejidad temporal**: se mide con nodos generados/expandidos (ambos
  algoritmos lo reportan en su resumen).
- **Complejidad espacial**: se mide con el máximo de nodos que estuvieron a la
  vez en la frontera (también reportado).
- **b, d, m**: en este grafo, `b` (factor de ramificación) es en promedio ~4
  (cada biblioteca tiene pocos vecinos cercanos), `d` es la profundidad de la
  solución encontrada (número de saltos del camino) y `m` es 27 (la
  profundidad máxima posible, con 28 nodos).
