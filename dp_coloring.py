"""
dp_coloring.py — Coloración exacta de grafos mediante DP sobre subconjuntos (bitmask)
Análisis y Diseño de Algoritmos | UVG | Semestre 1, 2026

Complejidad:
  - Tiempo:  O(3^n)  — precomputar conjuntos independientes + DP principal
  - Espacio: O(2^n)  — tabla dp
  - Límite práctico: n ≤ 20
"""

import networkx as nx
from utils import graph_to_adjacency_bitmask, normalize_graph

_MAX_N = 20  # límite práctico por memoria/tiempo


def _is_independent(S: int, adj: list[int]) -> bool:
    """
    Verifica en O(n) si el subconjunto S (representado como bitmask) es
    un conjunto independiente: ningún par de vértices en S comparte arista.

    Equivalente eficiente: para cada vértice v en S, ningún vecino de v
    debe estar también en S  →  adj[v] & S == 0.
    """
    temp = S
    while temp:
        v = (temp & -temp).bit_length() - 1  # índice del bit más bajo
        if adj[v] & S:
            return False
        temp &= temp - 1  # quitar bit más bajo
    return True


def _precompute_independent_flags(n: int, adj: list[int]) -> list[bool]:
    """
    Retorna un arreglo booleano indep donde indep[S] indica si S es
    un conjunto independiente.
    """
    indep = [False] * (1 << n)
    indep[0] = True
    for S in range(1, 1 << n):
        indep[S] = _is_independent(S, adj)
    return indep


def dp_coloring(G: nx.Graph) -> tuple[int, list[int]]:
    """
    Calcula el número cromático exacto χ(G) usando DP sobre subconjuntos.

    Parámetros
    ----------
    G : nx.Graph
        Grafo no dirigido con nodos renombrables a 0..n-1.

    Retorna
    -------
    chi : int
        Número cromático χ(G).
    dp : list[int]
        Tabla DP completa (dp[S] = mínimo de colores para colorear S).

    Lanza
    -----
    ValueError
        Si n > _MAX_N (demasiado grande para el DP bitmask).
    """
    G = normalize_graph(G)
    n = G.number_of_nodes()

    if n == 0:
        return 0, [0]
    if n > _MAX_N:
        raise ValueError(
            f"n={n} excede el límite práctico del DP bitmask (n ≤ {_MAX_N})."
        )

    adj = graph_to_adjacency_bitmask(G, n)
    full = (1 << n) - 1  # máscara con todos los vértices

    # Precomputar independencia de todos los subconjuntos
    indep = _precompute_independent_flags(n, adj)

    # DP: dp[S] = mínimo número de colores (clases de color) para colorear S
    INF = n + 1
    dp = [INF] * (1 << n)
    dp[0] = 0

    for S in range(1, 1 << n):
        # Iterar solo sobre subconjuntos independientes que están dentro de S
        # Trick: enumerar subconjuntos de S eficientemente
        sub = S
        while sub:
            if indep[sub]:
                candidate = dp[S ^ sub] + 1
                if candidate < dp[S]:
                    dp[S] = candidate
            sub = (sub - 1) & S  # siguiente subconjunto propio de S

    return dp[full], dp


def dp_coloring_with_assignment(G: nx.Graph) -> tuple[int, dict]:
    """
    Calcula χ(G) y reconstruye una asignación de colores válida.

    Retorna
    -------
    chi : int
        Número cromático.
    coloring : dict
        Diccionario {nodo: color (0-indexed)}.
    """
    original_nodes = list(G.nodes())
    G = normalize_graph(G)
    n = G.number_of_nodes()

    if n == 0:
        return 0, {}

    chi, dp = dp_coloring(G)
    adj = graph_to_adjacency_bitmask(G, n)
    indep = _precompute_independent_flags(n, adj)

    # Reconstruir la asignación rastreando los conjuntos independientes usados
    coloring = {}
    remaining = (1 << n) - 1
    color_id = 0

    while remaining:
        # Encontrar el conjunto independiente I ⊆ remaining tal que
        # dp[remaining ^ I] + 1 == dp[remaining]
        sub = remaining
        while sub:
            if indep[sub] and dp[remaining ^ sub] + 1 == dp[remaining]:
                # Asignar color_id a todos los vértices en sub
                temp = sub
                while temp:
                    v = (temp & -temp).bit_length() - 1
                    coloring[v] = color_id
                    temp &= temp - 1
                remaining ^= sub
                color_id += 1
                break
            sub = (sub - 1) & remaining

    # Restaurar IDs originales para que la salida respete los nodos de entrada.
    coloring_with_original_ids = {
        original_nodes[v]: color
        for v, color in coloring.items()
    }

    return chi, coloring_with_original_ids


# ---------------------------------------------------------------------------
# Demo rápido
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import networkx as nx

    tests = [
        ("K4 (completo)",          nx.complete_graph(4),   4),
        ("C6 (ciclo par)",         nx.cycle_graph(6),      2),
        ("C5 (ciclo impar)",       nx.cycle_graph(5),      3),
        ("K_{3,3} (bipartito)",    nx.complete_bipartite_graph(3, 3), 2),
        ("Petersen",               nx.petersen_graph(),    3),
    ]

    for name, G, expected in tests:
        chi, _ = dp_coloring(G)
        status = "OK" if chi == expected else f"FALLO (esperado {expected})"
        print(f"  {name:25s} χ = {chi}  [{status}]")
