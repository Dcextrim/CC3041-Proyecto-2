"""
benchmark.py — Análisis empírico de DP bitmask vs Greedy LDF
Análisis y Diseño de Algoritmos | UVG | Semestre 1, 2026

Ejecutar:
    python benchmark.py

Genera:
    - Tabla de resultados en consola
    - benchmark_results.csv
    - scatter_regression.png
"""

import time
import csv
import math
import argparse
import warnings
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

try:
    # NumPy 2.x expone RankWarning en numpy.exceptions
    from numpy.exceptions import RankWarning
except ImportError:  # compatibilidad con versiones anteriores
    RankWarning = RuntimeWarning

from utils import (
    generate_random_graph,
    generate_complete_graph,
    generate_bipartite_graph,
    generate_cycle_graph,
    normalize_graph,
)
from dp_coloring import dp_coloring
from greedy_coloring import greedy_coloring

# ---------------------------------------------------------------------------
# Configuración de entradas de prueba (según enunciado)
# ---------------------------------------------------------------------------

GRAPH_CONFIGS = [
    # (tipo_label, función_generadora, lista_de_n, kwargs_extra)
    ("random",    generate_random_graph,    [5, 8, 10, 12, 14, 16], {"p": 0.5, "seed": 42}),
    ("complete",  generate_complete_graph,  [5, 6, 7, 8, 9, 10],   {}),
    ("bipartite", generate_bipartite_graph, [6, 8, 10, 12, 14, 16], {}),
    ("cycle",     generate_cycle_graph,     [6, 8, 10, 12, 15, 18], {}),
]

REPEATS = 3          # número de repeticiones para promediar tiempos
DP_MAX_N = 18        # máximo n para el que corremos DP (n=18 → 2^18 ≈ 262 K entradas)
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_CSV = BASE_DIR / "benchmark_results.csv"
OUTPUT_PNG = BASE_DIR / "scatter_regression.png"

GREEDY_LARGE_CONFIGS = [
    ("random", generate_random_graph, [50, 100, 200, 500], {"p": 0.1, "seed": 123}),
    ("bipartite", generate_bipartite_graph, [50, 100, 200, 500], {}),
    ("cycle", generate_cycle_graph, [50, 100, 200, 500], {}),
]


# ---------------------------------------------------------------------------
# Función de medición
# ---------------------------------------------------------------------------

def measure(func, *args, repeats: int = REPEATS) -> float:
    """Tiempo promedio de ejecución de func(*args) en segundos."""
    total = 0.0
    for _ in range(repeats):
        t0 = time.perf_counter()
        func(*args)
        total += time.perf_counter() - t0
    return total / repeats


# ---------------------------------------------------------------------------
# Bucle principal de benchmark
# ---------------------------------------------------------------------------

def run_benchmark(
    repeats: int = REPEATS,
    dp_max_n: int = DP_MAX_N,
    include_greedy_large: bool = False,
) -> list[dict]:
    results = []

    configs = list(GRAPH_CONFIGS)
    if include_greedy_large:
        configs.extend(GREEDY_LARGE_CONFIGS)

    print(f"\n{'Tipo':>10} {'n':>4} {'Aristas':>8} {'chi(DP)':>7} "
          f"{'Greedy':>7} {'t_DP(s)':>12} {'t_Greedy(s)':>13}")
    print("-" * 70)

    for graph_type, gen_fn, ns, kwargs in configs:
        for n in ns:
            G = normalize_graph(gen_fn(n, **kwargs))
            m = G.number_of_edges()

            # --- Greedy (siempre) ---
            t_greedy = measure(greedy_coloring, G, repeats=repeats)
            chi_greedy, _ = greedy_coloring(G)

            # --- DP (solo si n ≤ DP_MAX_N) ---
            if n <= dp_max_n:
                t_dp = measure(dp_coloring, G, repeats=repeats)
                chi_dp, _ = dp_coloring(G)
            else:
                t_dp = float("nan")
                chi_dp = None

            row = {
                "type":      graph_type,
                "n":         n,
                "edges":     m,
                "chi_dp":    chi_dp,
                "chi_greedy": chi_greedy,
                "t_dp":      t_dp,
                "t_greedy":  t_greedy,
            }
            results.append(row)

            chi_dp_str = str(chi_dp) if chi_dp is not None else "—"
            t_dp_str   = f"{t_dp:.6f}" if not math.isnan(t_dp) else "—"
            print(f"{graph_type:>10} {n:>4} {m:>8} {chi_dp_str:>6} "
                  f"{chi_greedy:>7} {t_dp_str:>12} {t_greedy:>13.6f}")

    return results


# ---------------------------------------------------------------------------
# Exportar CSV
# ---------------------------------------------------------------------------

def save_csv(results: list[dict], path: Path = OUTPUT_CSV) -> None:
    fields = ["type", "n", "edges", "chi_dp", "chi_greedy", "t_dp", "t_greedy"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResultados guardados en '{path.name}'")


# ---------------------------------------------------------------------------
# Gráfica de dispersión + regresión
# ---------------------------------------------------------------------------

def r_squared(y_actual: np.ndarray, y_predicted: np.ndarray) -> float:
    """Coeficiente de determinación R²."""
    ss_res = np.sum((y_actual - y_predicted) ** 2)
    ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else 1.0


def plot_results(results: list[dict], path: Path = OUTPUT_PNG, show_plot: bool = True) -> None:
    # Separar puntos DP y Greedy con tiempos válidos
    dp_rows     = [r for r in results if not math.isnan(r["t_dp"]) and r["t_dp"] > 0]
    greedy_rows = [r for r in results if r["t_greedy"] > 0]

    ns_dp     = np.array([r["n"] for r in dp_rows], dtype=float)
    ts_dp     = np.array([r["t_dp"] for r in dp_rows])
    ns_greedy = np.array([r["n"] for r in greedy_rows], dtype=float)
    ts_greedy = np.array([r["t_greedy"] for r in greedy_rows])

    fig, ax = plt.subplots(figsize=(10, 6))

    # --- Scatter ---
    ax.scatter(ns_dp, ts_dp, color="royalblue", zorder=5,
               label="DP bitmask (medido)", s=60)
    ax.scatter(ns_greedy, ts_greedy, color="tomato", zorder=5,
               label="Greedy LDF (medido)", marker="s", s=60)

    # --- Regresión DP: ajuste exponencial (lineal en escala log) ---
    if len(ns_dp) >= 2:
        log_ts_dp = np.log(ts_dp)
        coefs_dp  = np.polyfit(ns_dp, log_ts_dp, 1)
        n_fit_dp  = np.linspace(ns_dp.min(), ns_dp.max(), 200)
        t_fit_dp  = np.exp(np.polyval(coefs_dp, n_fit_dp))
        r2_dp     = r_squared(log_ts_dp, np.polyval(coefs_dp, ns_dp))
        ax.plot(n_fit_dp, t_fit_dp, "--", color="royalblue", linewidth=1.8,
                label=f"Regresión DP: exp({coefs_dp[0]:.3f}·n)  R²={r2_dp:.3f}")
        print(f"R² ajuste DP (escala log): {r2_dp:.4f}")

    # --- Regresión Greedy: polinomio grado 2 ---
    if len(ns_greedy) >= 3:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RankWarning)
            coefs_g = np.polyfit(ns_greedy, ts_greedy, 2)
        n_fit_g  = np.linspace(ns_greedy.min(), ns_greedy.max(), 200)
        t_fit_g  = np.polyval(coefs_g, n_fit_g)
        r2_g     = r_squared(ts_greedy, np.polyval(coefs_g, ns_greedy))
        ax.plot(n_fit_g, t_fit_g, "--", color="tomato", linewidth=1.8,
                label=f"Regresión Greedy: grado 2  R²={r2_g:.3f}")
        print(f"R² ajuste Greedy (grado 2): {r2_g:.4f}")

    ax.set_yscale("log")
    ax.set_xlabel("Número de vértices n", fontsize=13)
    ax.set_ylabel("Tiempo de ejecución (s) — escala logarítmica", fontsize=13)
    ax.set_title("DP bitmask vs Greedy LDF — Tiempos de ejecución", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, which="both", linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    print(f"Gráfica guardada en '{path.name}'")
    if show_plot:
        plt.show()
    else:
        plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark de coloración de grafos: DP bitmask vs Greedy LDF"
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=REPEATS,
        help="Repeticiones por medición para promediar tiempo (default: 3)",
    )
    parser.add_argument(
        "--dp-max-n",
        type=int,
        default=DP_MAX_N,
        help="Tamaño máximo n para ejecutar DP exacto (default: 18)",
    )
    parser.add_argument(
        "--include-greedy-large",
        action="store_true",
        help="Incluye tamaños grandes (hasta n=500) para greedy; DP se omite allí.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="No abre ventana de matplotlib (útil en ejecución no interactiva).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()

    if args.repeats < 1:
        raise ValueError("--repeats debe ser >= 1")
    if args.dp_max_n < 0:
        raise ValueError("--dp-max-n debe ser >= 0")

    print("=" * 70)
    print("  Benchmark: Coloración Óptima de Grafos")
    print("  DP bitmask (exacto) vs Greedy LDF (aproximado)")
    print("=" * 70)

    results = run_benchmark(
        repeats=args.repeats,
        dp_max_n=args.dp_max_n,
        include_greedy_large=args.include_greedy_large,
    )
    save_csv(results)
    plot_results(results, show_plot=not args.no_show)
