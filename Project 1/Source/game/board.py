"""
Board representation, switches, and bridge mechanics.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Set
from .constants import TileType, SwitchType, SwitchOperation


@dataclass
class Bridge:
    """
    A bridge consisting of one or more tiles on the board.
    When open: acts as normal FLOOR tiles.
    When closed: acts as VOID tiles.
    """
    id: str
    cells: List[Tuple[int, int]]
    initially_open: bool = False


@dataclass
class Switch:
    """
    A switch on the board.
    - type: SOFT (any part touches), HEAVY (standing only), SPLIT (standing only, teleports & splits)
    - operation: TOGGLE (flips bridge state) or PERMANENT (forces bridge open)
    - linked_bridges: IDs of bridges affected by this switch
    - split_targets: [(r1, c1), (r2, c2)] target coordinates if type == SPLIT
    """
    pos: Tuple[int, int]
    type: SwitchType
    operation: SwitchOperation = SwitchOperation.TOGGLE
    linked_bridges: List[str] = field(default_factory=list)
    split_targets: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None


class Board:
    """
    The game board grid and static elements.
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        grid: List[List[TileType]],
        goal_pos: Tuple[int, int],
        start_pos: Tuple[int, int],
        bridges: Optional[Dict[str, Bridge]] = None,
        switches: Optional[Dict[Tuple[int, int], Switch]] = None,
    ):
        self.rows = rows
        self.cols = cols
        self.grid = grid
        self.goal_pos = goal_pos
        self.start_pos = start_pos
        self.bridges = bridges or {}
        self.switches = switches or {}

        # Precompute mapping from cell coordinate to bridge_id for quick lookups
        self.cell_to_bridge: Dict[Tuple[int, int], str] = {}
        for b_id, bridge in self.bridges.items():
            for cell in bridge.cells:
                self.cell_to_bridge[cell] = b_id

    def in_bounds(self, r: int, c: int) -> bool:
        """Returns True if (r, c) is within the grid boundary."""
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_base_tile(self, r: int, c: int) -> TileType:
        """Returns the static tile type at (r, c)."""
        if not self.in_bounds(r, c):
            return TileType.VOID
        return self.grid[r][c]

    def is_passable(self, r: int, c: int, bridge_states: Dict[str, bool]) -> bool:
        """
        Determines if a cell is solid floor given dynamic bridge open/closed statuses.
        """
        if not self.in_bounds(r, c):
            return False

        tile = self.grid[r][c]
        if tile == TileType.VOID:
            return False

        if tile == TileType.BRIDGE:
            bridge_id = self.cell_to_bridge.get((r, c))
            if bridge_id is None:
                return False
            # Passable only if this bridge is currently open
            return bridge_states.get(bridge_id, False)

        return True  # FLOOR, GOAL, FRAGILE are physically present
