"""
Immutable, hashable GameState representation for Bloxorz.
Assigned to: Member 1 (Core Game Mechanics & State Modeling)

Essential for search algorithms (BFS, DFS, UCS, A*) to detect visited states.
"""

from typing import Tuple, Dict, Optional
from .constants import Orientation, TileType
from .block import Block
from .board import Board


class GameState:
    """
    Represents an exact snapshot of the game:
    - Block position & orientation (or split cube coordinates)
    - Open/closed status of all bridges (as an immutable tuple of (bridge_id, is_open))
    """

    def __init__(
        self,
        block: Block,
        bridge_states: Tuple[Tuple[str, bool], ...],
    ):
        self.block = block
        # Bridge states stored as canonical sorted tuple for consistent hashing
        self.bridge_states = tuple(sorted(bridge_states, key=lambda x: x[0]))
        self._cached_hash: Optional[int] = None
        self._cached_dict: Optional[Dict[str, bool]] = None

    @property
    def bridge_dict(self) -> Dict[str, bool]:
        """Returns bridge states as a dictionary for convenient lookup."""
        if self._cached_dict is None:
            self._cached_dict = dict(self.bridge_states)
        return self._cached_dict

    def is_goal(self, board: Board) -> bool:
        """
        Victory condition (Section 2.4):
        The block falls into the goal hole ONLY when standing upright on the goal cell.
        - A block that merely lies across the goal cell does NOT win.
        - A single split cube CANNOT complete the stage (Section 2.5).
        
        Guidelines for Member 1:
        1. If self.block.is_split is True -> return False.
        2. Check if self.block.orientation == Orientation.STANDING.
        3. Check if (self.block.r, self.block.c) == board.goal_pos.
        """
        # TODO [Member 1]: Implement victory goal check according to Section 2.4.
        raise NotImplementedError("Member 1: Implement is_goal check.")

    def is_valid(self, board: Board) -> bool:
        """
        Validates if the current state is physically supported and legal:
        1. All occupied cells must be inside bounds and passable (floor or open bridge).
        2. Fragile tiles rule (Section 2.5):
           A fragile tile breaks if the 1x1x2 block stands upright on it.
        
        Guidelines for Member 1:
        1. Get all occupied cells using self.block.occupied_cells().
        2. For every cell (r, c), verify board.is_passable(r, c, self.bridge_dict).
        3. If block is NOT split and is STANDING upright:
           Check if board.get_base_tile(r, c) == TileType.FRAGILE. If so, return False.
        4. Return True if all checks pass.
        """
        # TODO [Member 1]: Implement state legality validation (bounds, voids, fragile tiles).
        raise NotImplementedError("Member 1: Implement is_valid check.")

    def __hash__(self) -> int:
        """
        Computes state hash for set() and dict lookups.
        
        Guidelines for Member 1:
        Hash both the block state (via self.block.to_tuple()) AND the bridge states.
        Cache the hash value in self._cached_hash for high performance during search!
        """
        # TODO [Member 1]: Implement state hashing combining block and bridge states.
        raise NotImplementedError("Member 1: Implement __hash__.")

    def __eq__(self, other: object) -> bool:
        """
        Checks equality between two game states.
        
        Guidelines for Member 1:
        Two states are equal if and only if:
        1. Both are GameState instances.
        2. Both blocks have identical to_tuple() representations.
        3. Both bridge_states tuples are identical.
        """
        # TODO [Member 1]: Implement state equality check.
        raise NotImplementedError("Member 1: Implement __eq__.")

    def __repr__(self) -> str:
        return f"GameState(block={self.block}, bridges={dict(self.bridge_states)})"
