"""
greedy_coloring.py — Coloración aproximada de grafos mediante heurística Greedy
Análisis y Diseño de Algoritmos | UVG | Semestre 1, 2026

Estrategia: Largest-Degree-First (LDF)
  - Ordenar vértices por grado descendente
  - Asignar a cada vértice el menor color no usado por sus vecinos ya coloreados

Complejidad:
  - Tiempo:  O(n log n + m)   (ordenamiento + recorrido de adyacencias)
  - Espacio: O(n)
  - No garantiza optimalidad; puede usar hasta 2·χ(G) colores en el peor caso
"""

import networkx as nx
from utils import validate_coloring


def greedy_coloring_ordered(G: nx.Graph, order: list) -> tuple[int, dict]:
    """
    Coloración greedy de primer ajuste (first-fit) usando un orden explícito.

    Este helper permite demostrar que la calidad de greedy depende del orden
    de procesamiento de los vértices.
    """
    if G.number_of_nodes() == 0:
        return 0, {}

    if len(order) != G.number_of_nodes() or set(order) != set(G.nodes()):
        raise ValueError("El orden debe contener exactamente todos los nodos de G una vez.")

    coloring: dict = {}

    for v in order:
        used_colors = {coloring[u] for u in G.neighbors(v) if u in coloring}
        color = 0
        while color in used_colors:
            color += 1
        coloring[v] = color

    num_colors = max(coloring.values()) + 1
    return num_colors, coloring


def greedy_coloring(G: nx.Graph) -> tuple[int, dict]:
    """
    Coloración greedy Largest-Degree-First.

    Parámetros
    ----------
    G : nx.Graph
        Grafo no dirigido (nodos pueden ser cualquier hashable).

    Retorna
    -------
    num_colors : int
        Número de colores usados (aproximación de χ(G)).
    coloring : dict
        Diccionario {nodo: color (0-indexed)}.
    """
    # Ordenar vértices por grado descendente (tie-break por ID para determinismo)
    vertices = sorted(G.nodes(), key=lambda v: (-G.degree(v), v))
    return greedy_coloring_ordered(G, vertices)


def greedy_coloring_with_validation(G: nx.Graph) -> tuple[int, dict, bool]:
    """
    Ejecuta greedy_coloring y verifica la validez de la coloración resultante.

    Retorna
    -------
    num_colors : int
    coloring : dict
    is_valid : bool
        True si ningún par adyacente comparte color.
    """
    num_colors, coloring = greedy_coloring(G)
    is_valid = validate_coloring(G, coloring)
    return num_colors, coloring, is_valid


# ---------------------------------------------------------------------------
# Contraejemplo clásico: demostración de que greedy NO es óptimo
# ---------------------------------------------------------------------------

def build_bipartite_counterexample(n: int = 5) -> tuple[nx.Graph, int, list, int, list, int]:
    """
    Construye un contraejemplo bipartito de "crown graph" C_n.

    El grafo es bipartito y siempre cumple χ(G)=2, pero greedy first-fit puede
    usar n colores con un orden desfavorable (u1,v1,u2,v2,...).

    Parámetros
    ----------
    n : int
        Número de pares en la corona (total de vértices = 2n). Requiere n >= 3.

    Retorna
    -------
    G : nx.Graph
    chi_opt : int
    bad_order : list
    bad_colors : int
    good_order : list
    good_colors : int
    """
    if n < 3:
        raise ValueError("n debe ser >= 3 para usar este contraejemplo.")

    left = [f"u{i}" for i in range(n)]
    right = [f"v{i}" for i in range(n)]

    G = nx.Graph()
    G.add_nodes_from(left, bipartite=0)
    G.add_nodes_from(right, bipartite=1)

    # Crown graph: K_{n,n} sin matching perfecto (u_i, v_i)
    for i, u in enumerate(left):
        for j, v in enumerate(right):
            if i != j:
                G.add_edge(u, v)

    bad_order = []
    for i in range(n):
        bad_order.extend([left[i], right[i]])
    good_order = left + right

    chi_opt = 2
    bad_colors, _ = greedy_coloring_ordered(G, bad_order)
    good_colors, _ = greedy_coloring_ordered(G, good_order)

    return G, chi_opt, bad_order, bad_colors, good_order, good_colors


def build_greedy_counterexample() -> tuple[nx.Graph, int, int]:
    """Compatibilidad: retorna (G, χ_opt, colores_greedy_peor_orden)."""
    G, chi_opt, _, bad_colors, _, _ = build_bipartite_counterexample(n=5)
    return G, chi_opt, bad_colors


# ---------------------------------------------------------------------------
# Demo rápido
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        ("K4 (completo)",       nx.complete_graph(4),              4),
        ("C6 (ciclo par)",      nx.cycle_graph(6),                 2),
        ("C5 (ciclo impar)",    nx.cycle_graph(5),                 3),
        ("K_{3,3} (bipartito)", nx.complete_bipartite_graph(3, 3), 2),
        ("Petersen",            nx.petersen_graph(),               3),
    ]

    print("Greedy Largest-Degree-First\n")
    print(f"  {'Grafo':25s} {'χ óptimo':>10} {'Greedy':>8} {'Válido':>8}")
    print("  " + "-" * 55)

    for name, G, chi_opt in tests:
        num_colors, coloring, valid = greedy_coloring_with_validation(G)
        status = "SI" if valid else "NO"
        match = "=" if num_colors == chi_opt else f">{chi_opt}"
        print(f"  {name:25s} {chi_opt:>10} {num_colors:>8}  ({match})  válido={status}")

    print("\nContraejemplo bipartito (crown graph):")
    Gx, chi_x, _, bad_x, _, good_x = build_bipartite_counterexample(n=5)
    print(f"  Vértices={Gx.number_of_nodes()}, aristas={Gx.number_of_edges()}, χ óptimo={chi_x}")
    print(f"  Greedy con orden desfavorable usa {bad_x} colores")
    print(f"  Greedy con orden favorable usa {good_x} colores")
