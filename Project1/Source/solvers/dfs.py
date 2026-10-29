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

    def __init__(self, max_depth: int = 500):
        super().__init__(name="DFS")
        self.max_depth = max_depth

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
        """
        Executes Depth-First Search.

        Args:
            env: The Bloxorz environment.
            timeout: Maximum search duration in seconds.

        Returns:
            Tuple of (goal_node_or_None, expanded_count, generated_count).

        Guidelines for Member 2:
        1. Use an explicit LIFO stack (Python `list`: `append` and `pop`).
        2. Keep track of visited states. Because DFS can find a suboptimal path to a state,
           either store `{state: shallowest_depth}` or store the current path to prevent cycles.
        3. Respect `self.max_depth` to prevent deep recursions in infinite branches.
        4. When popping `current_node`, test `current_node.state.is_goal(env.board)`.
        5. Expand successors: add unvisited children to the stack.
        """
        # TODO [Member 2]: Implement DFS search loop with stack and cycle checking.
        start_time = time.perf_counter()

        initial_state = getattr(env, "initial_state", None)
        if initial_state is None and hasattr(env, "get_initial_state"):
            initial_state = env.get_initial_state()
        elif callable(initial_state):
            initial_state = initial_state()

        root = SearchNode(state=initial_state)
        stack: list[SearchNode] = [root]

        # Store {state: shallowest_depth} to prevent cycles while allowing shorter paths
        visited: dict = {initial_state: 0}

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

            # Reversed so the first legal action is popped first from the LIFO stack
            for child in reversed(children):
                if child.state not in visited:
                    visited[child.state] = child.depth
                    stack.append(child)
                    generated_count += 1

        return None, expanded_count, generated_count


class IDSSolver(BaseSolver):
    """
    Iterative Deepening Search (Optional alternative to DFS, Section 3.3).
    """

    def __init__(self, max_limit: int = 100):
        super().__init__(name="IDS")
        self.max_limit = max_limit

    def _get_successors(self, env: BloxorzEnv, node: SearchNode) -> list[SearchNode]:
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
        """
        Guidelines for Member 2:
        1. Loop `depth_limit` from 0 to `self.max_limit`.
        2. In each iteration, run Depth-Limited Search (DLS) up to `depth_limit`.
        3. If DLS finds the goal, return it immediately.
        4. Accumulate `expanded_count` and `generated_count` across depth limits.
        """
        # TODO [Member 2]: Implement Iterative Deepening loop.
        start_time = time.perf_counter()

        initial_state = getattr(env, "initial_state", None)
        if initial_state is None and hasattr(env, "get_initial_state"):
            initial_state = env.get_initial_state()
        elif callable(initial_state):
            initial_state = initial_state()

        total_expanded = 0
        total_generated = 0

        for depth_limit in range(self.max_limit + 1):
            if timeout and (time.perf_counter() - start_time) >= timeout:
                break

            root = SearchNode(state=initial_state)
            stack: list[SearchNode] = [root]
            visited_at_depth: dict = {initial_state: 0}
            total_generated += 1

            cutoff_occurred = False

            while stack:
                if timeout and (time.perf_counter() - start_time) >= timeout:
                    return None, total_expanded, total_generated

                current_node = stack.pop()

                if current_node.state.is_goal(env.board):
                    return current_node, total_expanded, total_generated

                if current_node.depth >= depth_limit:
                    cutoff_occurred = True
                    continue

                total_expanded += 1
                children = self._get_successors(env, current_node)

                for child in reversed(children):
                    if (
                            child.state not in visited_at_depth
                            or child.depth < visited_at_depth[child.state]
                    ):
                        visited_at_depth[child.state] = child.depth
                        stack.append(child)
                        total_generated += 1

            # If the entire tree was exhausted without hitting the depth limit, no solution exists
            if not cutoff_occurred:
                break

        return None, total_expanded, total_generated