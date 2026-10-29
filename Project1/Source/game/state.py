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

    __slots__ = ("block", "bridge_states", "_cached_hash", "_cached_dict")

    def __init__(
        self,
        block: Block,
        bridge_states: Tuple[Tuple[str, bool], ...], #((id, is_open))
        *,
        _canonical: bool = False,
    ):
        self.block = block
        # Bridge states stored as canonical sorted tuple for consistent hashing
        if _canonical or len(bridge_states) <= 1:
            self.bridge_states = bridge_states
        else:
            self.bridge_states = tuple(sorted(bridge_states, key=lambda x: x[0])) #Sorted with id
        self._cached_hash: int = hash((block._key, self.bridge_states))
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
        """
        # Khối đang tách (split) thì không thể thắng
        if self.block.is_split:
            return False
        return (
            self.block.orientation == Orientation.STANDING
            and (self.block.r, self.block.c) == board.goal_pos
        )

    def is_valid(self, board: Board) -> bool:
        """
        Validates if the current state is physically supported and legal:
        1. All occupied cells must be inside bounds and passable (floor or open bridge).
        2. Fragile tiles rule (Section 2.5):
           A fragile tile breaks if the 1x1x2 block stands upright on it.

        """
        rows = board.rows
        cols = board.cols
        grid = board.grid
        for r, c in self.block._cells:
            if not (0 <= r < rows and 0 <= c < cols):
                return False
            tile = grid[r][c]
            if tile == TileType.VOID:
                return False
            if tile == TileType.BRIDGE:
                bridge_id = board.cell_to_bridge.get((r, c))
                if bridge_id is None or not self.bridge_dict.get(bridge_id, False):
                    return False
        if (not self.block.is_split) and (self.block.orientation == Orientation.STANDING):
            if grid[self.block.r][self.block.c] == TileType.FRAGILE:
                return False
        return True

    def __hash__(self) -> int:
        """
        Computes state hash for set() and dict lookups.
        """
        return self._cached_hash

    def __eq__(self, other: object) -> bool:
        """
        Checks equality between two game states.
        """
        if self is other:
            return True
        return (
            type(other) is GameState
            and self._cached_hash == other._cached_hash
            and self.block._key == other.block._key
            and self.bridge_states == other.bridge_states
        )

    def __repr__(self) -> str:
        return f"GameState(block={self.block}, bridges={dict(self.bridge_states)})"
