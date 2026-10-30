# Team Workflow & Task Distribution Guide

**Project:** Bloxorz AI Solver  
**Team Size:** 4 Members  
**Duration:** ~3 Weeks  

---

## 1. Task Allocation for 4 Members

According to **Section 3.6 of the Project Specification**, the final report must document the explicit responsibilities of each team member and their individual completion percentages (which directly scale individual grades).

Here is the recommended task division:

| Member | Primary Role | Assigned Tasks & Components | Target Files |
| :--- | :--- | :--- | :--- |
| **Member 1** | **Core Game Mechanics & State Modeling** | • Board representation & JSON Stage Loader<br>• 1x1x2 block rolling physics (all 12 orientation transitions)<br>• Advanced tiles: Fragile tiles (orange), Bridges, Switches (soft, heavy, split)<br>• Block splitting & rejoining logic<br>• Immutable `GameState` hashing & equality (`__hash__`, `__eq__`)<br>• Stage design & validation test cases | `game/block.py`<br>`game/board.py`<br>`game/state.py`<br>`game/stage_loader.py`<br>`game/environment.py`<br>`stages/*.json`<br>`tests/test_transitions.py`<br>`tests/test_state.py` |
| **Member 2** | **Search Infrastructure & Uninformed Algorithms** | • Base search abstractions (`SearchNode`, `BaseSolver`, `SearchResult`)<br>• Execution metrics tracker (`tracemalloc` peak memory, `perf_counter` timing)<br>• Breadth-First Search (BFS) implementation<br>• Depth-First Search (DFS)<br>• Cycle avoidance & visited state hashing<br>• Solution path reconstruction | `solvers/base.py`<br>`solvers/bfs.py`<br>`solvers/dfs.py`<br>`tests/test_solvers.py` |
| **Member 3** | **Informed Search Algorithms & Heuristics** | • Priority queue management (min-heap with tie-breaking)<br>• Uniform-Cost Search (UCS) implementation<br>• Custom UCS cost function design & formal justification<br>• A* Search implementation<br>• Admissible & consistent heuristic functions (Manhattan / 2, Orientation-aware, Relaxed BFS)<br>• Mathematical admissibility proofs for the report | `solvers/ucs.py`<br>`solvers/astar.py`<br>`solvers/heuristics.py`<br>`tests/test_solvers.py` |
| **Member 4** | **GUI, Visualizer & Experimental Benchmarks** | • Pygame interactive user interface & renderer<br>• 3D shaded block rendering & tile visual design<br>• Manual keyboard play (arrows, spacebar for split cubes)<br>• Animated step-by-step solver replay controller<br>• Benchmark automated runner script (`experiments/benchmark.py`)<br>• Matplotlib chart generator (`experiments/plot_results.py`)<br>• Demo video recording & editing (Section 3.7) | `gui/renderer.py`<br>`gui/widgets.py`<br>`gui/app.py`<br>`main.py`<br>`experiments/benchmark.py`<br>`experiments/plot_results.py` |

---

## 2. Git Branching Strategy

To avoid merge conflicts, all 4 members should follow this workflow:

```
main (stable, working code only)
 │
 ├── feature/game-engine        (Member 1)
 ├── feature/uninformed-search  (Member 2)
 ├── feature/informed-search    (Member 3)
 └── feature/gui-experiments    (Member 4)
```

### Git Rules:
1. **Never commit directly to `main`**.
2. **Branch naming convention:** `feature/<role-or-feature-name>`, e.g.:
   - `git checkout -b feature/game-engine`
   - `git checkout -b feature/uninformed-search`
3. **Commit Messages:** Use clear imperative verbs:
   - `feat: implement block rolling orientation table`
   - `fix: correct fragile tile weight distribution check`
   - `test: add unit test for split cube rejoining`
4. **Pull Requests (PR):** Before merging into `main`, run the unit test suite:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py"
   ```
   Only merge when all tests pass!

---

## 3. 3-Week Project Roadmap

### **Week 1: Core Engine & Scaffolding**
- **Day 1-2:** Team kickoff. Review project specification, clone repository, inspect framework code.
- **Day 3-5:** 
  - Member 1 finalizes `block.py`, `state.py`, and JSON loader. Verifies orientation transitions.
  - Member 2 sets up `SearchNode` and verifies `tracemalloc` memory measurement.
  - Member 3 drafts heuristic formulas and cost function hypotheses.
  - Member 4 ensures Pygame runs and renders the board grid.
- **Day 6-7:** Merge Week 1 PRs. Run `test_transitions.py` and `test_state.py`.

### **Week 2: Algorithms Implementation & Integration**
- **Day 8-10:**
  - Member 2 implements and tunes BFS and DFS.
  - Member 3 implements UCS (with cost functions) and A* (with heuristics).
- **Day 11-12:**
  - Member 4 integrates solver calls into the GUI and tests animated replay.
  - Member 1 creates test stages (fragile tiles, bridges, switches, split switch).
- **Day 13-14:** Run full benchmark suite (`python3 main.py --benchmark`). Verify all 4 algorithms solve all test stages.

### **Week 3: Experiments, Report & Video**
- **Day 15-17:**
  - Member 4 generates comparison charts with `plot_results.py`.
  - Member 2 & 3 analyze time/memory/expanded nodes differences and write algorithm descriptions.
  - Member 1 writes state formalization and task distribution tables.
- **Day 18-19:** Record the YouTube demonstration video (GUI overview, manual gameplay, solver solving stages).
- **Day 20-21:** Assemble final `Report.pdf`, package `Source/`, verify submission structure, and submit.
