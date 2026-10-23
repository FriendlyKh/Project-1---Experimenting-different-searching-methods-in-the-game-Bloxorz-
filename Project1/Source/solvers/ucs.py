"""
Uniform-Cost Search (UCS) Solver for Bloxorz.
Assigned to: Member 3 (Informed Search Algorithms)

Project Requirements (Section 3.4):
- Implement UCS using a priority queue.
- Clearly define and justify a non-uniform cost function in your report.
  (If every move costs 1, UCS reduces to BFS; design a meaningful cost model).
"""

import time
import heapq
from typing import Optional, Tuple, Callable
from .base import BaseSolver, SearchNode
from ..game.environment import BloxorzEnv
from ..game.state import GameState
from ..game.board import Board
from ..game.constants import Direction, TileType
from ..game.block import Block


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
    # --- Cost model parameters (Section 3.4) ---
    BASE_MOVE_COST = 1.0        # một lần lăn / một bước của cube
    FRAGILE_PENALTY = 2.0       # có phần nào của block nằm trên ô cam (fragile)
    SWITCH_EVENT_COST = 0.5     # nước đi kích hoạt công tắc: thay cho base cost
    SPLIT_MOVE_PENALTY = 0.2    # di chuyển cube 1x1x1 khi đang tách đôi
    SWITCH_CUBE_COST = 0.3      # đổi quyền điều khiển sang cube còn lại
        # Đổi cube: không lăn, không chạm ô mới, không kích hoạt công tắc.

    if action == Direction.SWITCH_CUBE:
        return SWITCH_CUBE_COST

    cost = BASE_MOVE_COST

    # Sự kiện công tắc: bridge đổi trạng thái hoặc block vừa bị tách đôi.
    bridge_changed = state.bridge_states != next_state.bridge_states
    just_split = next_state.block.is_split and not state.block.is_split
    if bridge_changed or just_split:
        cost = SWITCH_EVENT_COST

    # Rủi ro địa hình: có phần nào của block trên ô fragile.
    if any(
        board.get_base_tile(r, c) == TileType.FRAGILE
        for r, c in next_state.block.occupied_cells()
    ):
        cost += FRAGILE_PENALTY

    # Chi phí phối hợp khi đang tách đôi.
    if state.block.is_split:
        cost += SPLIT_MOVE_PENALTY

    return cost


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
        self.cost_fn = cost_fn if cost_fn is not None else custom_cost_function

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
        start_time = time.perf_counter()

        initial_state = env.get_initial_state()
        start_node = SearchNode(initial_state)

        id_cnt = 0
        nodes_expanded = 0 # Number of Node pop from frontier and get_successor
        nodes_generated = 0 # Number of Node push into frontier
        
        frontier = [] # [GameState, cost]
        best_g_cost = {initial_state: 0} #Dict[GameState, float]
        heapq.heappush(frontier, start_node) #SearchNode has comparasion method

        while frontier and (time.perf_counter() - start_time) < timeout:
            cur_node = heapq.heappop(frontier)
            cur_state = cur_node.state

            # Lazy deletion
            if cur_node.g_cost > best_g_cost.get(cur_state, float("inf")):
                continue

            if cur_state.is_goal(env.board):
                return cur_node, nodes_expanded, nodes_generated
            
            nodes_expanded += 1
 
            for action, next_state, step_cost in env.get_successors(cur_state, self.cost_fn):
                new_g = cur_node.g_cost + step_cost

                if new_g < best_g_cost.get(next_state, float('inf')):
                    best_g_cost[next_state] = new_g
                    nodes_generated += 1

                    next_node = SearchNode(
                        state = next_state, 
                        parent = cur_node, 
                        action = action,
                        g_cost = new_g,
                        h_cost = 0,
                        depth = cur_node.depth + 1,
                        node_id = nodes_generated,
                        )
                    
                    heapq.heappush(frontier, next_node)


        return (None, nodes_expanded, nodes_generated) # Cant find goal or timeout
