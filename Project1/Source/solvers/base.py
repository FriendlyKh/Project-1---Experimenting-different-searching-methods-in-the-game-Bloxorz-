"""
Base search classes, search node representation, and benchmarking metrics.
Used across all algorithms: BFS, DFS/IDS, UCS, and A*.
"""

import time
import tracemalloc
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any
from ..game.state import GameState
from ..game.constants import Direction
from ..game.environment import BloxorzEnv


@dataclass
class SearchNode:
    """
    Search tree / graph node.
    """
    state: GameState
    parent: Optional["SearchNode"] = None
    action: Optional[Direction] = None
    g_cost: float = 0.0          # Path cost from root
    h_cost: float = 0.0          # Heuristic estimate to goal
    depth: int = 0
    node_id: int = 0             # Tie-breaker for PriorityQueue

    @property
    def f_cost(self) -> float:
        """Total evaluation function f(n) = g(n) + h(n)."""
        return self.g_cost + self.h_cost

    def __lt__(self, other: "SearchNode") -> bool:
        """Comparison for priority queue (min-heap)."""
        if self.f_cost != other.f_cost:
            return self.f_cost < other.f_cost
        # Secondary comparison on g_cost (prefer deeper/higher g to break ties towards goal)
        if self.g_cost != other.g_cost:
            return self.g_cost > other.g_cost
        # Tertiary tie-breaker by FIFO node_id
        return self.node_id < other.node_id

    def get_path_actions(self) -> List[Direction]:
        """Reconstructs sequence of actions from start state to this node."""
        actions = []
        curr = self
        while curr.parent is not None:
            if curr.action is not None:
                actions.append(curr.action)
            curr = curr.parent
        actions.reverse()
        return actions

    def get_path_states(self) -> List[GameState]:
        """Reconstructs sequence of states from start state to this node."""
        states = []
        curr = self
        while curr is not None:
            states.append(curr.state)
            curr = curr.parent
        states.reverse()
        return states


@dataclass
class SearchResult:
    """
    Standardized benchmark metrics required by Section 3.2-3.6.
    """
    algorithm: str
    success: bool
    actions: List[Direction] = field(default_factory=list)
    states: List[GameState] = field(default_factory=list)
    solution_length: int = 0        # Number of moves
    solution_cost: float = 0.0      # Total path cost
    search_time: float = 0.0        # Seconds
    peak_memory_kb: float = 0.0     # Peak memory in KB
    expanded_nodes: int = 0         # Expanded node count
    generated_nodes: int = 0        # Generated node count
    status_message: str = ""

    def summary(self) -> str:
        """Returns a formatted human-readable summary of the search run."""
        status = "SOLVED" if self.success else f"FAILED ({self.status_message})"
        return (
            f"[{self.algorithm}] {status} | "
            f"Moves: {self.solution_length} | "
            f"Cost: {self.solution_cost:.2f} | "
            f"Time: {self.search_time * 1000:.2f} ms | "
            f"Memory: {self.peak_memory_kb:.2f} KB | "
            f"Expanded: {self.expanded_nodes} | "
            f"Generated: {self.generated_nodes}"
        )


class BaseSolver(ABC):
    """
    Abstract Base Class for Bloxorz search solvers.
    Wraps execution with automatic memory profiling (tracemalloc) and wall-clock timing.
    """

    def __init__(self, name: str):
        self.name = name

    def solve(
        self,
        env: BloxorzEnv,
        timeout: float = 120.0,
    ) -> SearchResult:
        """
        Executes search on the given environment, measuring time and memory.
        """
        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()
        start_time = time.perf_counter()

        goal_node = None
        expanded = 0
        generated = 0
        status_msg = "Completed"

        try:
            goal_node, expanded, generated = self._search(env, timeout)
            if goal_node is None:
                status_msg = "No solution found or timed out"
        except Exception as e:
            status_msg = f"Error: {str(e)}"
        finally:
            elapsed = time.perf_counter() - start_time
            if tracemalloc.is_tracing():
                current_mem, peak_mem = tracemalloc.get_traced_memory()
                if not was_tracing:
                    tracemalloc.stop()
            else:
                peak_mem = 0

        peak_kb = peak_mem / 1024.0

        if goal_node is not None:
            actions = goal_node.get_path_actions()
            states = goal_node.get_path_states()
            return SearchResult(
                algorithm=self.name,
                success=True,
                actions=actions,
                states=states,
                solution_length=len(actions),
                solution_cost=goal_node.g_cost,
                search_time=elapsed,
                peak_memory_kb=peak_kb,
                expanded_nodes=expanded,
                generated_nodes=generated,
                status_message="Solution found",
            )
        else:
            return SearchResult(
                algorithm=self.name,
                success=False,
                search_time=elapsed,
                peak_memory_kb=peak_kb,
                expanded_nodes=expanded,
                generated_nodes=generated,
                status_message=status_msg,
            )

    @abstractmethod
    def _search(
        self,
        env: BloxorzEnv,
        timeout: float,
    ) -> Tuple[Optional[SearchNode], int, int]:
        """
        Algorithm-specific search logic to be implemented by team members.
        Returns: (goal_node_or_None, expanded_count, generated_count)
        """
        pass
