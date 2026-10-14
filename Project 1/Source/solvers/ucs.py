"""
Uniform-Cost Search (UCS) Solver for Bloxorz.
Assigned to: Member 3 (Informed Search Algorithms)

Project Requirements (Section 3.4):
- Implement UCS using a priority queue.
- Clearly define and justify a non-uniform cost function in your report.
  (If every move costs 1, UCS reduces to BFS; design a meaningful cost model).
"""

from typing import Optional, Tuple, Callable
from .base import BaseSolver, SearchNode
from ..game.environment import BloxorzEnv
from ..game.state import GameState
from ..game.board import Board
from ..game.constants import Direction


def default_cost_function(
    state: GameState,
    action: Direction,
    next_state: GameState,
    board: Board,
) -> float:
    """
    Baseline uniform step cost: 1.0 per action.
    """
    return 1.0


def custom_cost_function(
    state: GameState,
    action: Direction,
    next_state: GameState,
    board: Board,
) -> float:
    """
    Non-uniform cost function (Section 3.4).
    
    Guidelines for Member 3:
    Design a meaningful cost function and justify it in your report!
    Examples of intuitions:
    - Base roll cost = 1.0
    - Fragile tile penalty: moving onto fragile (orange) tiles costs +2.0 (higher risk of falling).
    - Switch toggle bonus: triggering a switch costs 0.5 (incentivizes unlocking bridges).
    - Split cube coordination: moving unit cubes has a slight penalty (+0.2).
    """
    # TODO [Member 3]: Define your customized, well-justified cost function here.
    raise NotImplementedError("Member 3: Implement custom cost function here.")


class UCSSolver(BaseSolver):
    """
    Uniform-Cost Search solver.
    """

    def __init__(
        self,
        cost_fn: Optional[Callable[[GameState, Direction, GameState, Board], float]] = None,
        name: str = "UCS",
    ):
        super().__init__(name=name)
        self.cost_fn = cost_fn if cost_fn is not None else default_cost_function

    def _search(
        self,
        env: BloxorzEnv,
        timeout: float,
    ) -> Tuple[Optional[SearchNode], int, int]:
        """
        Executes Uniform-Cost Search.
        
        Guidelines for Member 3:
        1. Use a min-heap priority queue (`heapq` module) storing `SearchNode` instances.
        2. Priority is determined by path cost `g(n)` (lowest `g_cost` popped first).
        3. Maintain `best_g_costs: Dict[GameState, float]` tracking the cheapest path to each state.
        4. CRITICAL: For UCS, perform the GOAL TEST when popping the node from the priority queue
           (not when generating successors), which guarantees finding the optimal path!
        5. For each successor:
           - Calculate `new_g = current_node.g_cost + step_cost`.
           - If `new_g < best_g_costs.get(next_state, infinity)`:
             - Update `best_g_costs[next_state] = new_g`.
             - Push child node onto the priority queue.
        """
        # TODO [Member 3]: Implement UCS with heapq and priority queue.
        raise NotImplementedError("Member 3: Implement UCS search logic here.")
