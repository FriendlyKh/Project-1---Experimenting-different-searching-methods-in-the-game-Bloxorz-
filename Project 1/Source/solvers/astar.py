"""
A* Search Solver for Bloxorz.
Assigned to: Member 3 (Informed Search Algorithms)

Project Requirements (Section 3.5):
- Implement A* search using f(n) = g(n) + h(n).
- Must record Search Time, Memory Usage, Expanded Nodes, and Solution Length.
"""

from typing import Optional, Tuple, Callable
from .base import BaseSolver, SearchNode
from .heuristics import manhattan_heuristic
from ..game.environment import BloxorzEnv
from ..game.state import GameState
from ..game.board import Board


class AStarSolver(BaseSolver):
    """
    A* Search implementation.
    """

    def __init__(
        self,
        heuristic_fn: Optional[Callable[[GameState, Board], float]] = None,
        name: str = "A*",
    ):
        super().__init__(name=name)
        self.heuristic_fn = (
            heuristic_fn if heuristic_fn is not None else manhattan_heuristic
        )

    def _search(
        self,
        env: BloxorzEnv,
        timeout: float,
    ) -> Tuple[Optional[SearchNode], int, int]:
        """
        Executes A* Search.
        
        Guidelines for Member 3:
        1. Maintain a min-heap priority queue ordered by total evaluation cost `f(n) = g(n) + h(n)`.
        2. Root node has `g = 0.0` and `h = self.heuristic_fn(root.state, env.board)`.
        3. Maintain `best_g_costs: Dict[GameState, float]` to avoid reopening worse paths.
        4. In the main loop:
           - Pop `current_node = heapq.heappop(heap)`.
           - Skip if `current_node.g_cost > best_g_costs.get(current_node.state)`.
           - Increment `expanded_nodes_count`.
           - Goal check: if `current_node.state.is_goal(env.board)`, return `current_node`.
           - For each successor `(action, next_state, step_cost)`:
             - Compute `new_g = current_node.g_cost + step_cost`.
             - If `new_g < best_g_costs.get(next_state, infinity)`:
               - Update `best_g_costs[next_state] = new_g`.
               - Compute `h_val = self.heuristic_fn(next_state, env.board)`.
               - Create child `SearchNode(g_cost=new_g, h_cost=h_val, ...)` and push to heap.
        """
        # TODO [Member 3]: Implement A* search loop with priority queue f(n) = g(n) + h(n).
        raise NotImplementedError("Member 3: Implement A* search logic here.")
