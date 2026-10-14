# Bloxorz Solver - Architectural Blueprint

This document explains the internal design, coordinate system, state representations, physics transitions, and algorithm interfaces of the framework.

---

## 1. System Architecture Overview

```
                                +-------------------+
                                |    JSON Stage     |
                                |    Definitions    |
                                +---------+---------+
                                          |
                                          v
                                +-------------------+
                                |    StageLoader    |
                                +---------+---------+
                                          |
                                          v
+------------------+            +-------------------+
|     Block        | ---------> |      Board        |
|  (Orientation &  |            |  (Grid, Bridges,  |
|   Coordinates)   |            |     Switches)     |
+--------+---------+            +---------+---------+
         |                                |
         +----------------+---------------+
                          |
                          v
                +-------------------+
                |     GameState     | <--- Immutable & Hashable!
                | (Block + Bridges) |
                +---------+---------+
                          |
                          v
                +-------------------+
                |    BloxorzEnv     |
                | (Transition Model |
                |   & Successors)   |
                +---------+---------+
                          |
         +----------------+----------------+
         |                                 |
         v                                 v
+-------------------+             +-------------------+
|     Solvers       |             |   GUI Visualizer  |
| (BFS/DFS/UCS/A*)  |             |     (Pygame)      |
+---------+---------+             +-------------------+
         |
         v
+-------------------+
|  Benchmark Engine |
| & Matplotlib Plot |
+-------------------+
```

---

## 2. Coordinate System & Block Orientations

The board is a 2D matrix where `(r, c)` denotes `(row, column)`:
- `row` increases downwards.
- `col` increases rightwards.

The standard 1x1x2 block exists in exactly one of three orientations:

1. **`Orientation.STANDING`**:
   - Occupies a single cell: `(r, c)`.
   - Height is 2 units, base is 1x1.

2. **`Orientation.LYING_H` (Horizontal)**:
   - Occupies two horizontally adjacent cells: `(r, c)` and `(r, c + 1)`.
   - Length along columns.

3. **`Orientation.LYING_V` (Vertical)**:
   - Occupies two vertically adjacent cells: `(r, c)` and `(r + 1, c)`.
   - Length along rows.

---

## 3. The 12 Deterministic Orientation Roll Transitions

When the block rolls in direction $d \in \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}\}$, its new anchor coordinate and orientation change deterministically:

| Current Orientation | Direction | Next Orientation | Next Anchor $(r', c')$ | Occupied Cells |
| :--- | :--- | :--- | :--- | :--- |
| **STANDING** $(r, c)$ | `UP` | `LYING_V` | $(r - 2, c)$ | $(r - 2, c), (r - 1, c)$ |
| **STANDING** $(r, c)$ | `DOWN` | `LYING_V` | $(r + 1, c)$ | $(r + 1, c), (r + 2, c)$ |
| **STANDING** $(r, c)$ | `LEFT` | `LYING_H` | $(r, c - 2)$ | $(r, c - 2), (r, c - 1)$ |
| **STANDING** $(r, c)$ | `RIGHT` | `LYING_H` | $(r, c + 1)$ | $(r, c + 1), (r, c + 2)$ |
| **LYING_H** $(r, c), (r, c+1)$ | `UP` | `LYING_H` | $(r - 1, c)$ | $(r - 1, c), (r - 1, c + 1)$ |
| **LYING_H** $(r, c), (r, c+1)$ | `DOWN` | `LYING_H` | $(r + 1, c)$ | $(r + 1, c), (r + 1, c + 1)$ |
| **LYING_H** $(r, c), (r, c+1)$ | `LEFT` | `STANDING` | $(r, c - 1)$ | $(r, c - 1)$ |
| **LYING_H** $(r, c), (r, c+1)$ | `RIGHT` | `STANDING` | $(r, c + 2)$ | $(r, c + 2)$ |
| **LYING_V** $(r, c), (r+1, c)$ | `UP` | `STANDING` | $(r - 1, c)$ | $(r - 1, c)$ |
| **LYING_V** $(r, c), (r+1, c)$ | `DOWN` | `STANDING` | $(r + 2, c)$ | $(r + 2, c)$ |
| **LYING_V** $(r, c), (r+1, c)$ | `LEFT` | `LYING_V` | $(r, c - 1)$ | $(r, c - 1), (r + 1, c - 1)$ |
| **LYING_V** $(r, c), (r+1, c)$ | `RIGHT` | `LYING_V` | $(r, c + 1)$ | $(r, c + 1), (r + 1, c + 1)$ |

---

## 4. Hashable State Representation

A key requirement in Section 3.1 & Page 4 is:
> *"With switches and bridges, the state must include the open/closed status of every bridge, not just the block's position and orientation: states with the same block placement but different bridge configurations are different states."*

In Python, `GameState` implements:
```python
class GameState:
    def __init__(self, block: Block, bridge_states: Tuple[Tuple[str, bool], ...]):
        self.block = block
        self.bridge_states = tuple(sorted(bridge_states, key=lambda x: x[0]))

    def __hash__(self):
        return hash((self.block.to_tuple(), self.bridge_states))

    def __eq__(self, other):
        return (
            isinstance(other, GameState)
            and self.block.to_tuple() == other.block.to_tuple()
            and self.bridge_states == other.bridge_states
        )
```

Why this is critical:
- `set()` (closed list in BFS/DFS) and `dict` (`best_g` in UCS/A*) rely on `__hash__` and `__eq__`.
- Using immutable tuples prevents accidental mutation bugs during tree exploration.

---

## 5. Advanced Mechanics: Switches, Bridges & Split Cubes

### A. Switches & Bridges
1. **Soft Switch:** Activated when ANY cell of the block (or either split cube) lands on it.
2. **Heavy Switch:** Activated ONLY when a standard 1x1x2 block is **STANDING** on it.
3. **Split Switch:** Activated ONLY when standing on it. Immediately teleports the block to two designated coordinates and splits it into two 1x1x1 cubes.
4. **Operations:**
   - `TOGGLE`: Inverts bridge state (`open <-> closed`).
   - `PERMANENT`: Permanently opens bridge.

### B. Split Cubes & Rejoining
- When split, the cubes move independently 1 step at a time (`UP`, `DOWN`, `LEFT`, `RIGHT`).
- The player / solver can switch control between cubes (`SWITCH_CUBE`).
- **Rejoining Rule:** Whenever the two cubes occupy adjacent cells:
  - Horizontally adjacent (`r1 == r2` and `|c1 - c2| == 1`): Merges into `Orientation.LYING_H`.
  - Vertically adjacent (`c1 == c2` and `|r1 - r2| == 1`): Merges into `Orientation.LYING_V`.

---

## 6. Profiling & Metrics Collection (`solvers/base.py`)

To satisfy Section 3.2-3.6 requirements:
- **Search Time:** Measured via high-resolution wall-clock timer `time.perf_counter()`.
- **Peak Memory:** Measured via Python's built-in `tracemalloc` module:
  ```python
  tracemalloc.start()
  # ... execute search algorithm ...
  current_mem, peak_mem = tracemalloc.get_traced_memory()
  tracemalloc.stop()
  peak_kb = peak_mem / 1024.0
  ```
- **Expanded Nodes:** Incremented whenever a node is popped from the frontier and its successors generated.
- **Generated Nodes:** Incremented whenever a child state is created.
- **Solution Length:** Number of actions in the path from initial state to goal.
