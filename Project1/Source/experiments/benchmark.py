"""
Benchmark runner for Bloxorz Solvers (Section 3.6).
Runs BFS, DFS, UCS, and A* across all test stages and compiles results into CSV and tables.
"""

import csv
import json
import time
from pathlib import Path
from typing import List, Dict, Any

from ..config import STAGES_DIR, OUTPUT_DIR
from ..game.stage_loader import StageLoader
from ..game.environment import BloxorzEnv
from ..solvers.bfs import BFSSolver
from ..solvers.dfs import DFSSolver
from ..solvers.ucs import UCSSolver
from ..solvers.astar import AStarSolver


def _benchmark_stage_sort_key(path: Path):
    stem = path.stem.lower()
    prefix_order = {
        "stage_": 0,
        "pro_dfs_": 1,
        "pro_bfs_": 2,
        "pro_ucs_": 3,
        "pro_astar_": 4,
        "con_astar_": 5,
    }
    group = 6
    for prefix, rank in prefix_order.items():
        if stem.startswith(prefix):
            group = rank
            break
    return (group, path.name)


def run_benchmarks(
    stages_dir: Path = STAGES_DIR,
    output_dir: Path = OUTPUT_DIR,
    timeout: float = 30.0,
) -> List[Dict[str, Any]]:
    """
    Executes all search algorithms on each stage found in stages_dir.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_files = sorted(list(stages_dir.glob("*.json")), key=_benchmark_stage_sort_key)

    if not stage_files:
        print(f"[!] No stages found in {stages_dir}")
        return []

    solvers = [
        BFSSolver(),
        DFSSolver(max_depth=300),
        UCSSolver(),
        AStarSolver(),
    ]

    results: List[Dict[str, Any]] = []

    print("=" * 80)
    print("STARTING ALGORITHM BENCHMARK EXPERIMENTS")
    print(f"Stages: {len(stage_files)} | Solvers: {len(solvers)} | Timeout: {timeout}s")
    print("=" * 80)

    for stage_path in stage_files:
        stage_name = stage_path.stem
        print(f"\n[+] Testing Stage: {stage_name}")
        board = StageLoader.load_from_file(stage_path)
        env = BloxorzEnv(board)

        for solver in solvers:
            print(f"  -> Running {solver.name}...", end="", flush=True)
            res = solver.solve(env, timeout=timeout)
            print(f" {res.summary()}")

            row = {
                "stage": stage_name,
                "algorithm": solver.name,
                "success": res.success,
                "moves": res.solution_length if res.success else None,
                "cost": round(res.solution_cost, 2) if res.success else None,
                "time_ms": round(res.search_time * 1000, 2),
                "peak_mem_kb": round(res.peak_memory_kb, 2),
                "expanded_nodes": res.expanded_nodes,
                "generated_nodes": res.generated_nodes,
                "status": res.status_message,
            }
            results.append(row)

    # Export to CSV
    csv_path = output_dir / "benchmark_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "stage",
                "algorithm",
                "success",
                "moves",
                "cost",
                "time_ms",
                "peak_mem_kb",
                "expanded_nodes",
                "generated_nodes",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    # Export to JSON
    json_path = output_dir / "benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"[✓] Benchmark completed successfully!")
    print(f"[✓] Saved CSV: {csv_path}")
    print(f"[✓] Saved JSON: {json_path}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_benchmarks()
