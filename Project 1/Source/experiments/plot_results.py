"""
Plotting script for Section 3.6 Experiments.
Reads benchmark_results.csv and produces comparative charts for the final report.
"""

import csv
from pathlib import Path
from typing import Dict, List
from ..config import OUTPUT_DIR


def plot_benchmarks(csv_file: Path = OUTPUT_DIR / "benchmark_results.csv"):
    """
    Generates comparison bar charts using matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[!] matplotlib is not installed. Run 'pip install matplotlib' to generate charts.")
        return

    if not csv_file.exists():
        print(f"[!] Benchmark results not found at {csv_file}. Run benchmark.py first.")
        return

    # Read CSV
    stages = []
    algorithms = []
    data_time: Dict[str, Dict[str, float]] = {}
    data_mem: Dict[str, Dict[str, float]] = {}
    data_expanded: Dict[str, Dict[str, int]] = {}
    data_moves: Dict[str, Dict[str, int]] = {}

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stage = row["stage"]
            algo = row["algorithm"]
            if stage not in stages:
                stages.append(stage)
            if algo not in algorithms:
                algorithms.append(algo)

            data_time.setdefault(stage, {})[algo] = float(row["time_ms"])
            data_mem.setdefault(stage, {})[algo] = float(row["peak_mem_kb"])
            data_expanded.setdefault(stage, {})[algo] = int(row["expanded_nodes"])
            data_moves.setdefault(stage, {})[algo] = (
                int(row["moves"]) if row["moves"] and row["moves"] != "None" else 0
            )

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Bloxorz Solver Algorithm Performance Comparison", fontsize=16, fontweight="bold")

    import numpy as np
    x = np.arange(len(stages))
    width = 0.8 / len(algorithms)

    # 1. Search Time
    ax1 = axes[0, 0]
    for i, algo in enumerate(algorithms):
        vals = [data_time[s].get(algo, 0) for s in stages]
        ax1.bar(x + i * width, vals, width, label=algo)
    ax1.set_title("Search Time (ms) - Lower is better")
    ax1.set_xticks(x + width * (len(algorithms) - 1) / 2)
    ax1.set_xticklabels(stages, rotation=20, ha="right")
    ax1.set_ylabel("Time (ms)")
    ax1.legend()
    ax1.grid(axis="y", linestyle="--", alpha=0.6)

    # 2. Peak Memory
    ax2 = axes[0, 1]
    for i, algo in enumerate(algorithms):
        vals = [data_mem[s].get(algo, 0) for s in stages]
        ax2.bar(x + i * width, vals, width, label=algo)
    ax2.set_title("Peak Memory (KB) - Lower is better")
    ax2.set_xticks(x + width * (len(algorithms) - 1) / 2)
    ax2.set_xticklabels(stages, rotation=20, ha="right")
    ax2.set_ylabel("Memory (KB)")
    ax2.legend()
    ax2.grid(axis="y", linestyle="--", alpha=0.6)

    # 3. Expanded Nodes
    ax3 = axes[1, 0]
    for i, algo in enumerate(algorithms):
        vals = [data_expanded[s].get(algo, 0) for s in stages]
        ax3.bar(x + i * width, vals, width, label=algo)
    ax3.set_title("Expanded Nodes - Lower is better")
    ax3.set_xticks(x + width * (len(algorithms) - 1) / 2)
    ax3.set_xticklabels(stages, rotation=20, ha="right")
    ax3.set_ylabel("Node Count")
    ax3.legend()
    ax3.grid(axis="y", linestyle="--", alpha=0.6)

    # 4. Solution Length (Moves)
    ax4 = axes[1, 1]
    for i, algo in enumerate(algorithms):
        vals = [data_moves[s].get(algo, 0) for s in stages]
        ax4.bar(x + i * width, vals, width, label=algo)
    ax4.set_title("Solution Length (Moves)")
    ax4.set_xticks(x + width * (len(algorithms) - 1) / 2)
    ax4.set_xticklabels(stages, rotation=20, ha="right")
    ax4.set_ylabel("Number of Moves")
    ax4.legend()
    ax4.grid(axis="y", linestyle="--", alpha=0.6)

    plt.tight_layout()
    chart_path = OUTPUT_DIR / "algorithm_comparison.png"
    plt.savefig(chart_path, dpi=300)
    print(f"[✓] Successfully generated comparison chart: {chart_path}")
    plt.close()


if __name__ == "__main__":
    plot_benchmarks()
