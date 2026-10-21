"""
Depth-First Search (DFS) & Iterative Deepening Search (IDS) Solvers.
Assigned to: Member 2 (Uninformed Search Algorithms)

Project Requirements (Section 3.3):
- Implement DFS or IDS to solve Bloxorz.
- Handle repeated states to avoid getting stuck in infinite loops / cycles.
"""

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
        raise NotImplementedError("Member 2: Implement DFS search logic here.")


class IDSSolver(BaseSolver):
    """
    Iterative Deepening Search (Optional alternative to DFS, Section 3.3).
    """

    def __init__(self, max_limit: int = 100):
        super().__init__(name="IDS")
        self.max_limit = max_limit

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
        raise NotImplementedError("Member 2: Implement IDS search logic here.")
