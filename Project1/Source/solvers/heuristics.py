"""
Heuristic functions for A* Search in Bloxorz.
Assigned to: Member 3 (Informed Search Algorithms)

Project Requirements (Section 3.5):
- Design appropriate heuristics that estimate how close a state is to the goal.
- Prove in the report whether your heuristics are admissible (never overestimate true cost)
  and/or consistent.
"""

from collections import deque
from typing import Tuple, Dict
from ..game.state import GameState
from ..game.board import Board
from ..game.constants import Orientation, TileType

def manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    """Calculates Manhattan distance |r1 - r2| + |c1 - c2|."""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def manhattan_heuristic(state: GameState, board: Board) -> float:
    """
    Heuristic 1: Manhattan Distance divided by 2.
    
    Admissibility:
    A single roll of a 1x1x2 block shifts its coordinate by at most 2 cells.
    Therefore, the true remaining move cost is at least ceil(distance / 2) >= distance / 2.
    For split blocks, each action moves one cube by 1 unit; both cubes must reach
    the goal, so (dist1 + dist2) / 2 is an admissible lower bound.
    """
    goal = board.goal_pos
    if state.block.is_split:        # if block is in split 
        d1 = manhattan_distance(state.block.cube1, goal)
        d2 = manhattan_distance(state.block.cube2, goal)
        return (d1 + d2) / 2.0
    else:       # min of each cell distance to goal
        min_dist = min(manhattan_distance(c, goal) for c in state.block.occupied_cells())
        return min_dist / 2.0


def orientation_aware_heuristic(state: GameState, board: Board) -> float:
    """
    Heuristic 2: Orientation-Aware Heuristic.
    
    Admissibility:
    The goal can ONLY be reached when the block is STANDING upright on board.goal_pos.
    If the block is LYING_H or LYING_V, it requires at least one extra roll (+0.5 penalty)
    to stand up, even if it already overlaps the goal cell.
    If the block is SPLIT, it requires at least one extra roll (+1.0 penalty) to merge.
    """
    base_h = manhattan_heuristic(state, board)

    if state.block.is_split:
        return base_h + 1.0

    if state.block.orientation != Orientation.STANDING:
        return base_h + 0.5

    return base_h


class RelaxedBFSHeuristic:
    """
    Heuristic 3: Relaxed Grid BFS Shortest Path (Optional Advanced Heuristic).
    
    Precomputes true shortest path distances on the static board floor grid
    from the goal cell to all reachable tiles via backward BFS.
    Accounts for holes and voids while remaining admissible.
    """

    def __init__(self, board: Board):
        self.board = board
        self.distances: Dict[Tuple[int, int], int] = {}
        self._precompute()

    def _precompute(self):
        goal = self.board.goal_pos
        queue = deque([(goal, 0)])
        self.distances[goal] = 0

        while queue:
            (r,c), dist = queue.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc 
                if self.board.in_bounds(nr, nc):
                    tile = self.board.get_base_tile(nr, nc)
                    # consider any non-void tile traversable
                    if tile != TileType.VOID and (nr, nc) not in self.distances:
                        self.distances[(nr, nc)] = dist + 1
                        queue.append(((nr, nc), dist + 1))

    def __call__(self, state: GameState, board: Board) -> float:
        if state.block.is_split:
            d1 = self.distances.get(state.block.cube1, 100)
            d2 = self.distances.get(state.block.cube2, 100)
            return (d1 + d2) / 2.0
        else:
            min_dist = min(
                self.distances.get(cell, 100) for cell in state.block.occupied_cells()
            )
            h = min_dist / 2.0
            if state.block.orientation != Orientation.STANDING:
                h += 0.5
                
            return h
