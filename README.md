# Proyecto 2 — Coloración Óptima de Grafos

Análisis y Diseño de Algoritmos · UVG · Semestre 1, 2026

---

## Descripción

Implementación y análisis empírico comparativo de dos algoritmos para el problema
de coloración óptima de grafos: dado G = (V, E), hallar χ(G), el mínimo número de
colores tal que ningún par de vértices adyacentes comparta color.

| Algoritmo | Estrategia | Complejidad | Optimalidad |
| :--- | :--- | :---: | :---: |
| DP bitmask | Programación dinámica sobre subconjuntos | O(3ⁿ) | Exacto |
| Greedy LDF | Largest-Degree-First | O(n log n + m) | Aproximado |

---

## Estructura del proyecto

```text
proyecto2/
├── dp_coloring.py          # DP bitmask exacto (n ≤ 20)
├── greedy_coloring.py      # Greedy Largest-Degree-First + contraejemplo crown
├── benchmark.py            # Análisis empírico — genera CSV y PNG
├── utils.py                # Generadores de grafos y validación
├── visualizer_app.py       # Servidor Flask para el visualizador web
├── visualizer/
│   ├── templates/
│   │   └── index.html      # Interfaz de usuario
│   └── static/
│       ├── app.js          # Lógica de animación (Canvas API)
│       └── styles.css      # Estilos responsive
└── informe/
    ├── generar_informe_pdf.py  # Genera informe.pdf con ReportLab
    ├── informe.pdf             # Informe académico final
    └── guion_video.txt         # Guión del video explicativo (5 min)
```

---

## Instalación

```bash
pip install networkx matplotlib numpy flask reportlab
```

---

## Ejecución

### Visualizador interactivo (recomendado)

```bash
python visualizer_app.py
```

Abre **[http://127.0.0.1:5000](http://127.0.0.1:5000)** en el navegador.

### Benchmark empírico

```bash
# Análisis base — genera benchmark_results.csv y scatter_regression.png
python benchmark.py --no-show

# Con escalabilidad de Greedy hasta n = 500
python benchmark.py --include-greedy-large --no-show
```

### Verificación de correctitud

```bash
python dp_coloring.py
python greedy_coloring.py
```

### Regenerar el informe PDF

```bash
python informe/generar_informe_pdf.py
```

---

## Visualizador web

El frontend permite explorar ambos algoritmos de forma animada:

- **Modo individual** — elige Greedy o DP, tipo de grafo, n, semilla y velocidad.
  La animación colorea los vértices paso a paso en el canvas.
- **Modo comparativo** — muestra Greedy y DP en paralelo sobre el mismo grafo,
  con progreso y leyenda de colores independientes para cada panel.
- **Contraejemplo crown** — selecciona tipo *Crown* con orden *Desfavorable* para
  ver cómo Greedy usa más colores que el óptimo, evidenciando la ausencia de
  Greedy Choice Property.

---

## Salidas generadas

| Archivo | Descripción |
| :--- | :--- |
| `benchmark_results.csv` | χ(DP), χ(Greedy) y tiempos por tipo y tamaño de grafo |
| `scatter_regression.png` | Dispersión con curvas de regresión y valores R² |
| `informe/informe.pdf` | Informe académico completo con análisis y pseudocódigos |

---

## Tipos de grafos analizados

| Tipo | Tamaños de n | χ conocido |
| :--- | :---: | :---: |
| Erdős–Rényi G(n, 0.5) | 5, 8, 10, 12, 14, 16 | Variable |
| Completo Kₙ | 5 – 10 | n |
| Bipartito K⌊n/2⌋,⌈n/2⌉ | 6, 8, 10, 12, 14, 16 | 2 |
| Ciclo Cₙ | 6, 8, 10, 12, 15, 18 | 2 (par) / 3 (impar) |
