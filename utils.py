"""
utils.py — Funciones compartidas para el Proyecto 2: Coloración Óptima de Grafos
Análisis y Diseño de Algoritmos | UVG | Semestre 1, 2026
"""

import networkx as nx


# ---------------------------------------------------------------------------
# Generadores de grafos
# ---------------------------------------------------------------------------

def generate_random_graph(n: int, p: float = 0.5, seed: int = None) -> nx.Graph:
    """Grafo aleatorio Erdős–Rényi G(n, p)."""
    return nx.gnp_random_graph(n, p, seed=seed)


def generate_complete_graph(n: int) -> nx.Graph:
    """Grafo completo K_n  →  χ(K_n) = n."""
    return nx.complete_graph(n)


def generate_bipartite_graph(n: int) -> nx.Graph:
    """Grafo bipartito completo K_{n//2, n-n//2}  →  χ = 2 (si n ≥ 2)."""
    half = n // 2
    return nx.complete_bipartite_graph(half, n - half)


def generate_cycle_graph(n: int) -> nx.Graph:
    """Grafo ciclo C_n  →  χ = 2 si n par, χ = 3 si n impar."""
    return nx.cycle_graph(n)


# ---------------------------------------------------------------------------
# Conversión a bitmask (necesaria para el DP)
# ---------------------------------------------------------------------------

def graph_to_adjacency_bitmask(G: nx.Graph, n: int) -> list[int]:
    """
    Devuelve una lista `adj` de longitud n donde adj[v] es un entero cuyo
    bit i está activado si existe la arista (v, i).

    Requiere que los nodos de G sean enteros 0..n-1.
    """
    adj = [0] * n
    for u, v in G.edges():
        adj[u] |= (1 << v)
        adj[v] |= (1 << u)
    return adj


# ---------------------------------------------------------------------------
# Validación de coloración
# ---------------------------------------------------------------------------

def validate_coloring(G: nx.Graph, coloring: dict) -> bool:
    """
    Verifica que `coloring` (dict nodo→color) sea una coloración válida de G:
    ningún par de nodos adyacentes comparte el mismo color.

    Retorna True si es válida, False en caso contrario.
    """
    for u, v in G.edges():
        if coloring.get(u) == coloring.get(v):
            return False
    return True


def chromatic_number_from_coloring(coloring: dict) -> int:
    """Número de colores distintos usados en la coloración."""
    return len(set(coloring.values()))


# ---------------------------------------------------------------------------
# Utilidad: renombrar nodos a 0..n-1 (por si el grafo usa otros IDs)
# ---------------------------------------------------------------------------

def normalize_graph(G: nx.Graph) -> nx.Graph:
    """Devuelve un grafo isomorfo con nodos renombrados a 0, 1, ..., n-1."""
    mapping = {node: i for i, node in enumerate(G.nodes())}
    return nx.relabel_nodes(G, mapping)
