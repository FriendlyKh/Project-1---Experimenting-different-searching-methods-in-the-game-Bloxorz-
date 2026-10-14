"""
Main entry point for the Bloxorz Solver application.
Supports GUI interactive mode, CLI solver mode, and batch benchmark experiments.
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
    from config import STAGES_DIR
    from game.stage_loader import StageLoader
    from game.environment import BloxorzEnv
    from solvers.bfs import BFSSolver
    from solvers.dfs import DFSSolver
    from solvers.ucs import UCSSolver
    from solvers.astar import AStarSolver
except ImportError:
    from Source.config import STAGES_DIR
    from Source.game.stage_loader import StageLoader
    from Source.game.environment import BloxorzEnv
    from Source.solvers.bfs import BFSSolver
    from Source.solvers.dfs import DFSSolver
    from Source.solvers.ucs import UCSSolver
    from Source.solvers.astar import AStarSolver


def run_cli_solver(stage_file: Path, solver_name: str):
    """Executes a solver on a stage from the command line and prints results."""
    if not stage_file.exists():
        print(f"[!] Stage file not found: {stage_file}")
        sys.exit(1)

    board = StageLoader.load_from_file(stage_file)
    env = BloxorzEnv(board)

    solvers = {
        "bfs": BFSSolver(),
        "dfs": DFSSolver(),
        "ucs": UCSSolver(),
        "astar": AStarSolver(),
    }

    solver = solvers.get(solver_name.lower())
    if not solver:
        print(f"[!] Unknown solver '{solver_name}'. Choose from: bfs, dfs, ucs, astar")
        sys.exit(1)

    print(f"\n==========================================")
    print(f"Solving {stage_file.name} using {solver.name}")
    print(f"==========================================")
    result = solver.solve(env)
    print(result.summary())

    if result.success:
        print(f"\nSolution Path ({len(result.actions)} actions):")
        actions_str = " -> ".join([a.value for a in result.actions])
        print(actions_str)
        print(f"\nFinal State Goal Check: {result.states[-1].is_goal(board)}")


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
        print("    python3 main.py --cli --stage stages/stage_01_core.json --solver astar")
        print("    python3 main.py --benchmark\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] GUI failed to start: {e}")
        print("A graphical display server may not be available (headless server).")
        print("Running in CLI demonstration mode instead...")
        default_stage = STAGES_DIR / "stage_01_core.json"
        run_cli_solver(default_stage, "astar")


def main():
    parser = argparse.ArgumentParser(description="Bloxorz Solver & Interactive Game")
    parser.add_argument("--cli", action="store_true", help="Run in CLI headless mode")
    parser.add_argument("--stage", type=str, default="stages/stage_01_core.json", help="Stage JSON file path")
    parser.add_argument(
        "--solver",
        type=str,
        default="astar",
        choices=["bfs", "dfs", "ucs", "astar"],
        help="Algorithm to run in CLI mode",
    )
    parser.add_argument("--benchmark", action="store_true", help="Run all benchmarks and export CSV")

    args = parser.parse_args()

    if args.benchmark:
        try:
            from experiments.benchmark import run_benchmarks
        except ImportError:
            from Source.experiments.benchmark import run_benchmarks
        run_benchmarks()
    elif args.cli:
        stage_path = Path(args.stage)
        if not stage_path.is_absolute():
            # Check relative to cwd, then relative to CURRENT_DIR
            if not stage_path.exists() and (CURRENT_DIR / stage_path).exists():
                stage_path = CURRENT_DIR / stage_path
            elif not stage_path.exists() and (PARENT_DIR / stage_path).exists():
                stage_path = PARENT_DIR / stage_path
        run_cli_solver(stage_path, args.solver)
    else:
        run_gui()


if __name__ == "__main__":
    main()
