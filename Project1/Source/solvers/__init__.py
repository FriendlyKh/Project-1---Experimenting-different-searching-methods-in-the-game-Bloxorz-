"""
Solvers package exposing base classes and search algorithms.
"""

from .base import BaseSolver, SearchNode, SearchResult
from .bfs import BFSSolver
from .dfs import DFSSolver, IDSSolver
from .ucs import UCSSolver, default_cost_function, custom_cost_function
from .astar import AStarSolver
from .heuristics import (
    manhattan_heuristic,
    orientation_aware_heuristic,
    RelaxedBFSHeuristic,
)

__all__ = [
    "BaseSolver",
    "SearchNode",
    "SearchResult",
    "BFSSolver",
    "DFSSolver",
    "IDSSolver",
    "UCSSolver",
    "default_cost_function",
    "custom_cost_function",
    "AStarSolver",
    "manhattan_heuristic",
    "orientation_aware_heuristic",
    "RelaxedBFSHeuristic",
]
