"""
Frontend interactivo para visualizar coloracion de grafos paso a paso.

Uso:
    c:/Users/danie/OneDrive/Desktop/CGP/.venv/Scripts/python.exe visualizer_app.py
Luego abrir:
    http://127.0.0.1:5000
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import networkx as nx
from flask import Flask, jsonify, render_template, request

from utils import (
    generate_bipartite_graph,
    generate_complete_graph,
    generate_cycle_graph,
    generate_random_graph,
    graph_to_adjacency_bitmask,
    normalize_graph,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "visualizer" / "templates"
STATIC_DIR = BASE_DIR / "visualizer" / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
)

MAX_DP_N = 18
MAX_GREEDY_VIS_N = 140


def _is_independent(subset: int, adj: list[int]) -> bool:
    temp = subset
    while temp:
        v = (temp & -temp).bit_length() - 1
        if adj[v] & subset:
            return False
        temp &= temp - 1
    return True


def _precompute_independent_flags(n: int, adj: list[int]) -> list[bool]:
    flags = [False] * (1 << n)
    flags[0] = True
    for subset in range(1, 1 << n):
        flags[subset] = _is_independent(subset, adj)
    return flags


def _build_crown_graph(pairs: int) -> tuple[nx.Graph, list[int], list[int]]:
    if pairs < 3:
        raise ValueError("El crown graph requiere al menos 3 pares de vertices.")

    left = list(range(pairs))
    right = list(range(pairs, 2 * pairs))

    graph = nx.Graph()
    graph.add_nodes_from(left)
    graph.add_nodes_from(right)

    for i, u in enumerate(left):
        for j, v in enumerate(right):
            if i != j:
                graph.add_edge(u, v)

    bad_order = []
    for i in range(pairs):
        bad_order.extend([left[i], right[i]])

    good_order = left + right
    return graph, bad_order, good_order


def _generate_graph(
    graph_type: str,
    n: int,
    p: float,
    seed: int,
) -> tuple[nx.Graph, dict]:
    graph_type = graph_type.lower().strip()

    if graph_type == "random":
        graph = generate_random_graph(n, p=p, seed=seed)
        meta = {"graph_label": f"Erdos-Renyi G({n}, {p:.2f})"}
    elif graph_type == "complete":
        graph = generate_complete_graph(n)
        meta = {"graph_label": f"Completo K{n}"}
    elif graph_type == "bipartite":
        graph = generate_bipartite_graph(n)
        meta = {"graph_label": f"Bipartito K_{{{n//2},{n - n//2}}}"}
    elif graph_type == "cycle":
        graph = generate_cycle_graph(n)
        meta = {"graph_label": f"Ciclo C{n}"}
    elif graph_type == "crown":
        graph, bad_order, good_order = _build_crown_graph(n)
        meta = {
            "graph_label": f"Counterexample Crown (pares={n}, vertices={2*n})",
            "bad_order": bad_order,
            "good_order": good_order,
        }
    else:
        raise ValueError(f"Tipo de grafo no soportado: {graph_type}")

    graph = normalize_graph(graph)
    return graph, meta


def _compute_layout(graph: nx.Graph) -> dict[str, dict[str, float]]:
    node_count = graph.number_of_nodes()

    if node_count == 0:
        return {}
    if node_count == 1:
        node = next(iter(graph.nodes()))
        return {str(node): {"x": 0.5, "y": 0.5}}

    if node_count <= 3:
        pos = nx.circular_layout(graph)
    else:
        pos = nx.spring_layout(graph, seed=42, k=1.2 / math.sqrt(node_count))

    xs = [float(pos[node][0]) for node in graph.nodes()]
    ys = [float(pos[node][1]) for node in graph.nodes()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    dx = max(max_x - min_x, 1e-9)
    dy = max(max_y - min_y, 1e-9)

    normalized = {}
    for node in graph.nodes():
        x = (float(pos[node][0]) - min_x) / dx
        y = (float(pos[node][1]) - min_y) / dy
        normalized[str(node)] = {"x": x, "y": y}

    return normalized


def _resolve_greedy_order(
    graph: nx.Graph,
    graph_type: str,
    graph_meta: dict,
    order_mode: str,
) -> list[int] | None:
    if graph_type != "crown":
        return None

    bad_order = graph_meta["bad_order"]
    good_order = graph_meta["good_order"]

    if order_mode == "bad":
        return bad_order
    if order_mode == "good":
        return good_order

    return sorted(graph.nodes(), key=lambda node: (-graph.degree(node), node))


def _serialize_graph(graph: nx.Graph) -> tuple[list[dict], list[dict]]:
    layout = _compute_layout(graph)

    nodes = [
        {
            "id": str(node),
            "label": str(node),
            "x": layout[str(node)]["x"],
            "y": layout[str(node)]["y"],
            "degree": int(graph.degree(node)),
        }
        for node in graph.nodes()
    ]

    edges = [{"source": str(u), "target": str(v)} for u, v in graph.edges()]
    return nodes, edges


def _greedy_steps(graph: nx.Graph, order: list[int] | None = None) -> tuple[int, dict[str, int], list[dict]]:
    if graph.number_of_nodes() == 0:
        return 0, {}, [{"kind": "progress", "progress": 1.0, "message": "Grafo vacio"}]

    if order is None:
        order = sorted(graph.nodes(), key=lambda node: (-graph.degree(node), node))

    if len(order) != graph.number_of_nodes() or set(order) != set(graph.nodes()):
        raise ValueError("El orden para greedy es invalido.")

    coloring: dict[str, int] = {}
    steps: list[dict] = [
        {
            "kind": "progress",
            "progress": 0.0,
            "message": "Inicio de greedy Largest-Degree-First",
        }
    ]

    total = len(order)
    for index, vertex in enumerate(order, start=1):
        neighbor_colors = {
            coloring[str(neighbor)]
            for neighbor in graph.neighbors(vertex)
            if str(neighbor) in coloring
        }

        color = 0
        while color in neighbor_colors:
            color += 1

        coloring[str(vertex)] = color

        steps.append(
            {
                "kind": "color",
                "vertex": str(vertex),
                "color": color,
                "coloring": dict(coloring),
                "progress": index / total,
                "message": (
                    f"Paso {index}/{total}: vertice {vertex} recibe color {color}."
                ),
            }
        )

    colors_used = max(coloring.values()) + 1
    return colors_used, coloring, steps


def _dp_steps(graph: nx.Graph) -> tuple[int, dict[str, int], list[dict]]:
    n = graph.number_of_nodes()

    if n == 0:
        return 0, {}, [{"kind": "progress", "progress": 1.0, "message": "Grafo vacio"}]

    if n > MAX_DP_N:
        raise ValueError(
            f"DP visual solo soporta n <= {MAX_DP_N}. Recibido: n={n}."
        )

    adj = graph_to_adjacency_bitmask(graph, n)
    independent = _precompute_independent_flags(n, adj)

    full_mask = (1 << n) - 1
    total_states = full_mask
    checkpoint = max(1, total_states // 70)

    inf = n + 1
    dp = [inf] * (1 << n)
    dp[0] = 0

    steps: list[dict] = [
        {
            "kind": "progress",
            "progress": 0.0,
            "message": "Inicio de DP bitmask: explorando subconjuntos.",
        }
    ]

    for subset in range(1, 1 << n):
        sub = subset
        best = inf
        while sub:
            if independent[sub]:
                candidate = dp[subset ^ sub] + 1
                if candidate < best:
                    best = candidate
            sub = (sub - 1) & subset
        dp[subset] = best

        if subset % checkpoint == 0 or subset == total_states:
            steps.append(
                {
                    "kind": "progress",
                    "progress": subset / total_states,
                    "message": (
                        f"DP: evaluado subset {subset}/{total_states}."
                    ),
                }
            )

    coloring: dict[str, int] = {}
    remaining = full_mask
    color_id = 0

    steps.append(
        {
            "kind": "progress",
            "progress": 1.0,
            "message": "Reconstruyendo coloracion optima desde la tabla DP.",
        }
    )

    while remaining:
        chosen = 0
        sub = remaining
        while sub:
            if independent[sub] and dp[remaining ^ sub] + 1 == dp[remaining]:
                chosen = sub
                break
            sub = (sub - 1) & remaining

        if chosen == 0:
            break

        members: list[str] = []
        temp = chosen
        while temp:
            vertex = (temp & -temp).bit_length() - 1
            node_id = str(vertex)
            coloring[node_id] = color_id
            members.append(node_id)
            temp &= temp - 1

        remaining ^= chosen
        assigned = len(coloring)

        steps.append(
            {
                "kind": "color_class",
                "color": color_id,
                "vertices": members,
                "coloring": dict(coloring),
                "progress": assigned / n,
                "message": (
                    f"Color {color_id} asignado a vertices {', '.join(members)}."
                ),
            }
        )
        color_id += 1

    return dp[full_mask], coloring, steps


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/health")
def health() -> tuple[dict, int]:
    return {"status": "ok"}, 200


@app.post("/api/run")
def run_visualization() -> tuple[dict, int]:
    payload = request.get_json(silent=True) or {}

    algorithm = str(payload.get("algorithm", "greedy")).lower().strip()
    graph_type = str(payload.get("graphType", "random")).lower().strip()
    n = int(payload.get("n", 12))
    p = float(payload.get("p", 0.5))
    seed = int(payload.get("seed", 42))
    order_mode = str(payload.get("orderMode", "ldf")).lower().strip()

    if n < 3:
        return {"error": "n debe ser >= 3 para visualizar."}, 400
    if not (0.0 <= p <= 1.0):
        return {"error": "p debe estar en el rango [0, 1]."}, 400

    graph, graph_meta = _generate_graph(graph_type=graph_type, n=n, p=p, seed=seed)

    if algorithm == "dp" and graph.number_of_nodes() > MAX_DP_N:
        return {
            "error": (
                f"DP visual soporta hasta n={MAX_DP_N}. "
                f"Este grafo tiene {graph.number_of_nodes()} vertices."
            )
        }, 400

    if algorithm == "greedy" and graph.number_of_nodes() > MAX_GREEDY_VIS_N:
        return {
            "error": (
                f"Greedy visual soporta hasta n={MAX_GREEDY_VIS_N} para animacion fluida. "
                f"Este grafo tiene {graph.number_of_nodes()} vertices."
            )
        }, 400

    started = time.perf_counter()

    if algorithm == "greedy":
        order = _resolve_greedy_order(graph, graph_type, graph_meta, order_mode)
        colors_used, final_coloring, steps = _greedy_steps(graph, order=order)
    elif algorithm == "dp":
        colors_used, final_coloring, steps = _dp_steps(graph)
    else:
        return {"error": f"Algoritmo no soportado: {algorithm}"}, 400

    compute_ms = (time.perf_counter() - started) * 1000.0

    nodes, edges = _serialize_graph(graph)

    response = {
        "nodes": nodes,
        "edges": edges,
        "steps": steps,
        "meta": {
            "algorithm": algorithm,
            "graphType": graph_type,
            "graphLabel": graph_meta.get("graph_label", graph_type),
            "n": graph.number_of_nodes(),
            "m": graph.number_of_edges(),
            "colorsUsed": int(colors_used),
            "computeMs": round(compute_ms, 3),
            "orderMode": order_mode,
            "finalColoring": final_coloring,
        },
    }

    return jsonify(response), 200


@app.post("/api/compare")
def compare_visualization() -> tuple[dict, int]:
    payload = request.get_json(silent=True) or {}

    graph_type = str(payload.get("graphType", "random")).lower().strip()
    n = int(payload.get("n", 12))
    p = float(payload.get("p", 0.5))
    seed = int(payload.get("seed", 42))
    order_mode = str(payload.get("orderMode", "ldf")).lower().strip()

    if n < 3:
        return {"error": "n debe ser >= 3 para visualizar."}, 400
    if not (0.0 <= p <= 1.0):
        return {"error": "p debe estar en el rango [0, 1]."}, 400

    graph, graph_meta = _generate_graph(graph_type=graph_type, n=n, p=p, seed=seed)

    if graph.number_of_nodes() > MAX_DP_N:
        return {
            "error": (
                f"Modo comparativo soporta hasta n={MAX_DP_N} vertices por el DP. "
                f"Este grafo tiene {graph.number_of_nodes()} vertices."
            )
        }, 400

    greedy_order = _resolve_greedy_order(graph, graph_type, graph_meta, order_mode)

    started_g = time.perf_counter()
    greedy_colors_used, greedy_coloring, greedy_steps = _greedy_steps(
        graph,
        order=greedy_order,
    )
    greedy_ms = (time.perf_counter() - started_g) * 1000.0

    started_dp = time.perf_counter()
    dp_colors_used, dp_coloring, dp_steps = _dp_steps(graph)
    dp_ms = (time.perf_counter() - started_dp) * 1000.0

    nodes, edges = _serialize_graph(graph)

    response = {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "graphType": graph_type,
            "graphLabel": graph_meta.get("graph_label", graph_type),
            "n": graph.number_of_nodes(),
            "m": graph.number_of_edges(),
            "orderMode": order_mode,
        },
        "greedy": {
            "steps": greedy_steps,
            "colorsUsed": int(greedy_colors_used),
            "computeMs": round(greedy_ms, 3),
            "finalColoring": greedy_coloring,
        },
        "dp": {
            "steps": dp_steps,
            "colorsUsed": int(dp_colors_used),
            "computeMs": round(dp_ms, 3),
            "finalColoring": dp_coloring,
        },
    }

    return jsonify(response), 200


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
