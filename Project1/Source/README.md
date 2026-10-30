# Bloxorz Solver - Source Code & User Guide

**Course:** CSC14003 - Introduction to Artificial Intelligence  
**Project 1:** Bloxorz Solver  
**Faculty of Information Technology, University of Science, VNU-HCM**

---

## 1. Quickstart & Installation

### Requirements
- **Python:** 3.9 or higher
- **Dependencies:** Listed in `requirements.txt`

### Install Dependencies
Run from inside the `Source/` folder:
```bash
pip install -r requirements.txt
```

---

## 2. How to Run

### A. Launch Interactive Graphical Interface (GUI)
```bash
python3 main.py
```
*Note: Requires a graphical desktop environment and Pygame.*

#### GUI Features & Controls:
- **Arrow Keys (Up, Down, Left, Right):** Roll the block manually across the board.
- **Spacebar:** Switch active unit cube when split into two cubes.
- **`R` Key or "Restart Stage":** Reset current stage to the beginning.
- **`N` / `P` Keys or "Next" / "Prev":** Navigate between different puzzle stages.
- **Solver Buttons (`Solve BFS`, `Solve DFS`, `Solve UCS`, `Solve A*`):**
  - Triggers the selected AI search algorithm in real time.
  - Automatically loads the solved path into the visualizer.
  - Displays runtime metrics: solution length, search time, memory, expanded nodes.
- **Replay Controller:**
  - **Play / Pause:** Start or stop animated auto-playback of the solver's route.
  - **Step >:** Step forward one move at a time.
  - **Reset:** Return to the first step of the replay sequence.

---

### B. Command-Line Interface (CLI / Headless Mode)
Ideal for testing on servers without a display or quick algorithmic verification:
```bash
# Run A* on Stage 1
python3 main.py --cli --stage stages/stage_01_core.json --solver astar

# Run BFS on Classic Stage 1
python3 main.py --cli --stage stages/stage_classic_01.json --solver bfs

# Run UCS on Stage 3 with bridges
python3 main.py --cli --stage stages/stage_03_bridge.json --solver ucs

# Run DFS on Stage 2 with fragile tiles
python3 main.py --cli --stage stages/stage_02_fragile.json --solver dfs
```

---

### C. Run Automated Benchmark Suite (Section 3.6 Experiments)
Executes all 4 search algorithms across all 5 test stages, measuring **Search Time**, **Peak Memory**, **Expanded Nodes**, and **Solution Length**:
```bash
python3 main.py --benchmark
```
- Results are saved to:
  - `experiments/output/benchmark_results.csv`
  - `experiments/output/benchmark_results.json`

To generate comparison bar charts for your report:
```bash
python3 -m experiments.plot_results
```
- Output plot saved to: `experiments/output/algorithm_comparison.png`

---

### D. Run Unit Test Suite
Verify orientation transition physics, state immutability, hashing, and algorithms:
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## 3. Directory Structure

```
Source/
├── main.py                     # Primary entry point (GUI, CLI, benchmark runner)
├── requirements.txt            # Python dependencies (pygame, matplotlib)
├── README.md                   # Setup and execution instructions
├── config.py                   # Game configurations, colors, and constants
│
├── game/                       # Core game mechanics and state representation
│   ├── constants.py            # Enums: Orientation, Direction, TileType, SwitchType
│   ├── block.py                # 1x1x2 block, roll transitions, split & merge logic
│   ├── board.py                # Grid cells, dynamic bridges, and switch mappings
│   ├── state.py                # Immutable and hashable GameState for graph search
│   ├── stage_loader.py         # JSON stage parser
│   └── environment.py          # BloxorzEnv transition model & successor generation
│
├── solvers/                    # Search algorithms
│   ├── base.py                 # BaseSolver, SearchNode, SearchResult (metrics profiler)
│   ├── bfs.py                  # Breadth-First Search (Member 2)
│   ├── dfs.py                  # Depth-First Search (Member 2)
│   ├── ucs.py                  # Uniform-Cost Search with cost functions (Member 3)
│   ├── astar.py                # A* Search algorithm (Member 3)
│   └── heuristics.py           # Manhattan, Orientation-aware, Relaxed BFS (Member 3)
│
├── gui/                        # Pygame interface & visualization (Member 4)
│   ├── app.py                  # Application event loop, solvers bridge, replay timer
│   ├── renderer.py             # Board grid, 3D block shading, and status banners
│   └── widgets.py              # Clickable buttons, hover states, UI elements
│
├── stages/                     # JSON puzzle definitions
│   ├── stage_01_core.json      # Basic rolling and goal mechanics
│   ├── stage_02_fragile.json   # Fragile (orange) tiles
│   ├── stage_03_bridge.json    # Soft & heavy switches with toggle bridges
│   ├── stage_04_split.json     # Split switch "( )", dual cubes, and rejoining
│   └── stage_classic_01.json   # Authentic Bloxorz Stage 1
│
├── experiments/                # Benchmarking and reporting tools
│   ├── benchmark.py            # Automated runner across stages and solvers
│   └── plot_results.py         # Matplotlib chart generator (PNG outputs)
│
└── tests/                      # Unit test suite
    ├── test_transitions.py     # Verifies all 12 orientation roll transitions
    ├── test_state.py           # State hashing, fragile rules, and victory conditions
    ├── test_stage_loader.py    # JSON stage loading tests
    └── test_solvers.py         # End-to-end algorithmic correctness tests
```
