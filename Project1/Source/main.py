"""
Main entry point for the Bloxorz Solver application.
Supports GUI interactive mode, CLI solver mode, batch benchmark experiments, and plot generation.
"""

import sys
import argparse
from pathlib import Path

# Ensure both Source directory and project root are on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
for p in (CURRENT_DIR, PARENT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from config import STAGES_DIR, OUTPUT_DIR
    from game.stage_loader import StageLoader
    from game.environment import BloxorzEnv
    from solvers.bfs import BFSSolver
    from solvers.dfs import DFSSolver, IDSSolver
    from solvers.ucs import UCSSolver, default_cost_function, custom_cost_function
    from solvers.astar import AStarSolver
    from solvers.heuristics import manhattan_heuristic, orientation_aware_heuristic
except ImportError:
    from Source.config import STAGES_DIR, OUTPUT_DIR
    from Source.game.stage_loader import StageLoader
    from Source.game.environment import BloxorzEnv
    from Source.solvers.bfs import BFSSolver
    from Source.solvers.dfs import DFSSolver, IDSSolver
    from Source.solvers.ucs import UCSSolver, default_cost_function
    from Source.solvers.astar import AStarSolver
    from Source.solvers.heuristics import manhattan_heuristic, orientation_aware_heuristic


def resolve_stage_path(stage_str: str) -> Path:
    """
    Robustly resolves stage file path from:
    1. Exact path
    2. Path relative to CURRENT_DIR
    3. Path relative to PARENT_DIR
    4. Bare filename inside STAGES_DIR
    """
    path = Path(stage_str)
    if path.exists():
        return path
    if (CURRENT_DIR / path).exists():
        return CURRENT_DIR / path
    if (PARENT_DIR / path).exists():
        return PARENT_DIR / path
    if (STAGES_DIR / path.name).exists():
        return STAGES_DIR / path.name
    return path


def run_cli_solver(
    stage_file: Path,
    solver_name: str,
    heuristic_name: str = "manhattan",
    cost_name: str = "default",
    timeout: float = 60.0,
):
    """Executes a solver on a stage from the command line and prints results."""
    resolved_file = resolve_stage_path(str(stage_file))
    if not resolved_file.exists():
        print(f"[!] Stage file not found: {stage_file}")
        print(f"    Looked in current dir and {STAGES_DIR}")
        sys.exit(1)

    board = StageLoader.load_from_file(resolved_file)
    env = BloxorzEnv(board)

    # Heuristic selection for A*
    heuristics = {
        "manhattan": manhattan_heuristic,
        "orientation": orientation_aware_heuristic,
    }
    heuristic_fn = heuristics.get(heuristic_name.lower(), manhattan_heuristic)
    cost_fn = custom_cost_function if cost_name.lower() == "custom" else default_cost_function
    # Solvers dictionary
    solvers = {
        "bfs": BFSSolver(),
        "dfs": DFSSolver(),
        "ids": IDSSolver(),
        "ucs": UCSSolver(cost_fn=cost_fn),
        "astar": AStarSolver(heuristic_fn=heuristic_fn),
    }

    solver = solvers.get(solver_name.lower())
    if not solver:
        print(f"[!] Unknown solver '{solver_name}'. Choose from: {', '.join(solvers.keys())}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"Solving {resolved_file.name} using {solver.name}")
    if solver_name.lower() == "astar":
        print(f"Heuristic: {heuristic_name}")
    print("=" * 60)

    result = solver.solve(env, timeout=timeout)
    print(result.summary())

    if result.success:
        print(f"\nSolution Path ({len(result.actions)} actions):")
        actions_str = " -> ".join([a.value for a in result.actions])
        print(actions_str)
        print(f"\nFinal State Goal Check: {result.states[-1].is_goal(board)}")
    else:
        print(f"\nSearch failed: {result.status_message}")


def run_gui():
    """Launches the Pygame Graphical Interface."""
    try:
        import pygame
        try:
            from gui.app import BloxorzApp
        except ImportError:
            from Source.gui.app import BloxorzApp

        app = BloxorzApp()
        app.run()
    except ImportError:
        print("\n[!] Pygame is not installed!")
        print("To run the GUI, please install pygame:")
        print("    pip install -r requirements.txt")
        print("\nAlternatively, you can run solvers in CLI mode:")
        print("    python main.py --cli --stage stage_01_core.json --solver astar")
        print("    python main.py --benchmark\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] GUI failed to start: {e}")
        print("A graphical display server may not be available (headless server).")
        print("Running in CLI demonstration mode instead...")
        default_stage = STAGES_DIR / "stage_01_core.json"
        run_cli_solver(default_stage, "astar")


def run_plot():
    """Generates comparison plots from benchmark output."""
    try:
        from experiments.plot_results import plot_benchmarks
    except ImportError:
        from Source.experiments.plot_results import plot_benchmarks
    plot_benchmarks()


def main():
    parser = argparse.ArgumentParser(
        description="Bloxorz AI Solver & Interactive Visualizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py                                          # Launch interactive GUI
  python main.py --cli --stage stage_01_core.json         # Run A* on Stage 1
  python main.py --cli --stage stage_03_bridge.json --solver bfs
  python main.py --cli --solver astar --heuristic orientation
  python main.py --benchmark                              # Run all stages & export CSV/JSON
  python main.py --plot                                   # Generate comparison bar charts
""",
    )
    parser.add_argument("--cli", action="store_true", help="Run in CLI headless mode")
    parser.add_argument(
        "--stage",
        type=str,
        default="stages/stage_01_core.json",
        help="Stage JSON file path or filename",
    )
    parser.add_argument(
        "--solver",
        type=str,
        default="astar",
        choices=["bfs", "dfs", "ids", "ucs", "astar"],
        help="Search algorithm to run (default: astar)",
    )
    parser.add_argument(
        "--heuristic",
        type=str,
        default="manhattan",
        choices=["manhattan", "orientation"],
        help="Heuristic function for A* (default: manhattan)",
    )
    parser.add_argument(
        "--cost",
        type=str,
        default="default",
        choices=["default", "custom"],
        help="Cost function for UCS (default: default)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Search timeout in seconds (default: 60.0)",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark suite across all stages and export CSV/JSON",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate comparison bar charts from benchmark_results.csv",
    )

    args = parser.parse_args()

    if args.benchmark:
        try:
            from experiments.benchmark import run_benchmarks
        except ImportError:
            from Source.experiments.benchmark import run_benchmarks
        run_benchmarks(timeout=args.timeout)
    elif args.plot:
        run_plot()
    elif args.cli:
        run_cli_solver(
            stage_file=Path(args.stage),
            solver_name=args.solver,
            heuristic_name=args.heuristic,
            cost_name=args.cost,
            timeout=args.timeout,
        )
    else:
        run_gui()


if __name__ == "__main__":
    main()