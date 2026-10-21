"""
Breadth-First Search (BFS) Solver for Bloxorz.
Assigned to: Member 2 (Uninformed Search Algorithms)

Project Requirements (Section 3.2):
- Implement BFS to find the shortest path in terms of number of moves.
- Track Search Time, Peak Memory, Expanded Nodes, and Solution Length.
"""

from collections import deque
import time
from typing import Optional, Tuple
from .base import BaseSolver, SearchNode
from ..game.environment import BloxorzEnv


class BFSSolver(BaseSolver):
    """
    Solves Bloxorz using Breadth-First Search (FIFO queue).
    """

    def __init__(self):
        super().__init__(name="BFS")

    def _search(
        self,
        env: BloxorzEnv,
        timeout: float,
    ) -> Tuple[Optional[SearchNode], int, int]:
        """
        Executes Breadth-First Search.
        
        Args:
            env: The Bloxorz environment providing initial state and successors.
            timeout: Maximum search duration in seconds.
            
        Returns:
            Tuple of:
            - goal_node: SearchNode representing the goal state (or None if no path/timeout).
            - expanded_nodes_count: Total nodes popped and expanded.
            - generated_nodes_count: Total child nodes created.
            
        Guidelines for Member 2:
        1. Initialize `frontier` as a FIFO queue (use `collections.deque([root_node])`).
        2. Maintain a `visited` set to avoid revisiting states (cycle detection).
        3. Check if initial state is already the goal (`state.is_goal(env.board)`).
        4. While frontier is not empty and time hasn't exceeded `timeout`:
           a. Pop `current_node = frontier.popleft()`.
           b. Increment `expanded_nodes_count`.
           c. For each `(action, next_state, cost)` in `env.get_successors(current_node.state)`:
              - If `next_state` has not been visited:
                - Create child `SearchNode`.
                - Check for goal: if `next_state.is_goal(env.board)`, return `(child_node, expanded, generated)`.
                - Add `next_state` to `visited`.
                - Append `child_node` to `frontier`.
        5. Return `(None, expanded, generated)` if queue becomes empty without reaching goal.
        """
        # TODO [Member 2]: Implement BFS using collections.deque and visited set.
        start_time = time.perf_counter()

        initial_state = env.get_initial_state()
        root_node = SearchNode(state=initial_state)

        expanded_nodes_count = 0
        generated_nodes_count = 0

        if initial_state.is_goal(env.board):
            return (root_node, expanded_nodes_count, generated_nodes_count)

        frontier = deque([root_node])
        visited = set([root_node])

        while frontier and (time.perf_counter() - start_time) < timeout:
            current_node = frontier.popleft()
            expanded_nodes_count += 1

            for action, next_state, cost in env.get_successors(current_node.state):
                if next_state is not None and next_state not in visited:
                    generated_nodes_count += 1

                    child_node = SearchNode(
                        state=next_state, 
                        parent=current_node,
                        action=action,
                        g_cost=current_node.g_cost + cost,
                        depth=current_node.depth + 1,
                        node_id=generated_nodes_count
                    )

                    if next_state.is_goal(env.board):
                        return (child_node, expanded_nodes_count, generated_nodes_count)

                    frontier.append(child_node)
                    visited.add(child_node)

        return (None, expanded_nodes_count, generated_nodes_count)