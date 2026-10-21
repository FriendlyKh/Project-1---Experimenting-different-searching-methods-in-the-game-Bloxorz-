"""
Heuristic functions for A* Search in Bloxorz.
Assigned to: Member 3 (Informed Search Algorithms)

Project Requirements (Section 3.5):
- Design appropriate heuristics that estimate how close a state is to the goal.
- Prove in the report whether your heuristics are admissible (never overestimate true cost)
  and/or consistent.
"""

from typing import Tuple
from ..game.state import GameState
from ..game.board import Board


def manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    """Calculates Manhattan distance |r1 - r2| + |c1 - c2|."""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def manhattan_heuristic(state: GameState, board: Board) -> float:
    """
    Heuristic 1: Manhattan Distance divided by 2.
    
    Guidelines for Member 3:
    - Why divide by 2? A single roll of the 1x1x2 block changes coordinate by at most 2.
    - Calculate distance from block position to `board.goal_pos`.
    - Handle standard block vs split cubes.
    - Return `distance / 2.0`.
    """
    # TODO [Member 3]: Implement Manhattan distance / 2 heuristic.
    raise NotImplementedError("Member 3: Implement manhattan_heuristic.")


def orientation_aware_heuristic(state: GameState, board: Board) -> float:
    """
    Heuristic 2: Orientation-Aware Heuristic.
    
    Guidelines for Member 3:
    - The stage is won ONLY when the block is STANDING upright on the goal.
    - If the block is LYING horizontally or vertically, it requires at least one extra
      roll to stand up.
    - Add an appropriate penalty (e.g. +0.5 or +1.0) if `orientation != STANDING`.
    - Ensure your penalty maintains admissibility (never overestimates remaining cost).
    """
    # TODO [Member 3]: Implement orientation-aware heuristic.
    raise NotImplementedError("Member 3: Implement orientation_aware_heuristic.")


class RelaxedBFSHeuristic:
    """
    Heuristic 3: Relaxed Grid BFS Shortest Path (Optional Advanced Heuristic).
    
    Guidelines for Member 3:
    - Precomputes shortest path distance on the 2D floor grid from the goal cell to all tiles
      (ignoring orientation and fragile rules).
    - True lower bound considering walls and voids!
    """

    def __init__(self, board: Board):
        self.board = board
        # TODO [Member 3]: Precompute BFS distance dictionary from goal_pos to all floor tiles.

    def __call__(self, state: GameState, board: Board) -> float:
        # TODO [Member 3]: Lookup precomputed distance and divide by 2.0.
        raise NotImplementedError("Member 3: Implement RelaxedBFSHeuristic call.")
