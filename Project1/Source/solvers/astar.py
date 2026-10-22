"""
A* Search Solver for Bloxorz.
Assigned to: Member 3 (Informed Search Algorithms)

Project Requirements (Section 3.5):
- Implement A* search using f(n) = g(n) + h(n).
- Must record Search Time, Memory Usage, Expanded Nodes, and Solution Length.
"""

import time
import heapq
from typing import Optional, Tuple, Callable, Dict, List
from .base import BaseSolver, SearchNode
from .heuristics import manhattan_heuristic
from ..game.environment import BloxorzEnv
from ..game.state import GameState
from ..game.board import Board

class AStarSolver(BaseSolver):
    """
    A* Search implementation using a priority queue ordered by f(n) = g(n) + h(n)
    """

    def __init__(
        self, 
        heuristic_fn: Optional[Callable[[GameState, Board], float]] = None,
        name: str = "A*"
    ):
        super().__init__(name = name)
        self.heuristic_fn = (heuristic_fn if heuristic_fn is not None else manhattan_heuristic)

    def _search(
            self, 
            env: BloxorzEnv,
            timeout: float,
    ) -> Tuple[Optional[SearchNode], int, int]:
        """ Run A* search

        Returns:
            Tuple of:
            - goal_node: SearchNode reaching the goal state, or None.
            - expanded_nodes_count: Number of popped and expanded states.
            - generated_nodes_count: Total child nodes pushed to frontier.
        """
        start_time = time.perf_counter()

        initial_state = env.get_initial_state()
        initial_h = self.heuristic_fn(initial_state, env.board)

        root_node = SearchNode(
            state = initial_state,
            parent = None,
            action = None,
            g_cost = 0.0,
            h_cost = initial_h,
            depth = 0,
            node_id = 0,
        )

        expanded_nodes_count = 0
        generated_nodes_count = 1

        # Min-heap priority queue ordered by SearchNode.__lt__ (f_cost, g_cost, node_id)
        frontier: List[SearchNode] = [root_node]

        # Tracks lowest path cost g(s) found so far to each visited GameState
        best_g_costs: Dict[GameState, float] = {initial_state: 0.0}

        while frontier and (time.perf_counter() - start_time) < timeout:
            current_node = heapq.heappop(frontier)

            # Lazy pruning: skip node if a strictly cheaper path to this state was already expanded
            if current_node.g_cost > best_g_costs.get(current_node.state, float("inf")):
                continue

            # Goal test performed upon node expansion guarantees optimality with admissible heuristics
            if current_node.state.is_goal(env.board):
                return (current_node, expanded_nodes_count, generated_nodes_count)

            expanded_nodes_count += 1

            for action, next_state, step_cost in env.get_successors(current_node.state):
                new_g = current_node.g_cost + step_cost

                # Only explore this child if it yields a strictly better path cost 
                if new_g < best_g_costs.get(next_state, float("inf")):
                    best_g_costs[next_state] = new_g
                    generated_nodes_count += 1

                    h_val = self.heuristic_fn(next_state, env.board) # heuristic cost of next state
                    child_node = SearchNode(
                        state = next_state,
                        parent = current_node,
                        action=action,
                        g_cost = new_g,
                        h_cost = h_val,
                        depth = current_node.depth + 1,
                        node_id = generated_nodes_count,
                    )
                    heapq.heappush(frontier, child_node)

        return (None, expanded_nodes_count, generated_nodes_count)





