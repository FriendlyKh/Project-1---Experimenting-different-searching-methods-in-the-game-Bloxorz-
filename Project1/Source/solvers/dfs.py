"""
Depth-First Search (DFS) & Iterative Deepening Search (IDS) Solvers.
Assigned to: Member 2 (Uninformed Search Algorithms)

Project Requirements (Section 3.3):
- Implement DFS or IDS to solve Bloxorz.
- Handle repeated states to avoid getting stuck in infinite loops / cycles.
"""

import time
from typing import Optional, Tuple
from .base import BaseSolver, SearchNode
from ..game.environment import BloxorzEnv



class DFSSolver(BaseSolver):
    """
    Depth-First Search with explicit stack and cycle detection.
    """

    def __init__(self, max_depth: int = 100000):
        super().__init__(name="DFS")
        self.max_depth = max(max_depth,100000)

    def _get_successors(self, env: BloxorzEnv, node: SearchNode) -> list[SearchNode]:
        """Helper to generate child SearchNodes compatibly across common base setups."""
        return [
            SearchNode(state=ns, parent=node, action=a,
                    g_cost=node.g_cost + c, depth=node.depth + 1)
            for a, ns, c in env.get_successors(node.state)
        ]

    def _search(
            self,
            env: BloxorzEnv,
            timeout: float,
    ) -> Tuple[Optional[SearchNode], int, int]:
        start_time = time.perf_counter()

        initial_state = getattr(env, "initial_state", None)
        if initial_state is None and hasattr(env, "get_initial_state"):
            initial_state = env.get_initial_state()
        elif callable(initial_state):
            initial_state = initial_state()

        root = SearchNode(state=initial_state)
        stack: list[SearchNode] = [root]
        visited: set = {initial_state}

        expanded_count = 0
        generated_count = 1

        while stack:
            if timeout and (time.perf_counter() - start_time) >= timeout:
                break

            current_node = stack.pop()

            if current_node.state.is_goal(env.board):
                return current_node, expanded_count, generated_count

            if current_node.depth >= self.max_depth:
                continue

            expanded_count += 1
            children = self._get_successors(env, current_node)

            for child in reversed(children):
                if child.state not in visited:
                    visited.add(child.state)
                    stack.append(child)
                    generated_count += 1

        return None, expanded_count, generated_count



class IDSSolver(BaseSolver):
    """
    Iterative Deepening Search (Optional alternative to DFS, Section 3.3).
    """
    pass