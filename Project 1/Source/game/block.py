"""
Block representation and orientation physics for Bloxorz.
Assigned to: Member 1 (Core Game Mechanics & State Modeling)

Handles both standard 1x1x2 block and split 1x1x1 unit cubes.
"""

from typing import Tuple, List, Optional
from .constants import Orientation, Direction


class Block:
    """
    Represents the block in Bloxorz.
    
    Can be in two modes:
    1. Standard 1x1x2 block:
       - Defined by top-left anchor (r, c) and orientation (STANDING, LYING_H, LYING_V).
    2. Split mode (2 unit cubes 1x1x1):
       - Defined by cube1 (r1, c1), cube2 (r2, c2), and active_cube index (0 or 1).
    """

    def __init__(
        self,
        r: int,
        c: int,
        orientation: Orientation = Orientation.STANDING,
        is_split: bool = False,
        cube1: Optional[Tuple[int, int]] = None,
        cube2: Optional[Tuple[int, int]] = None,
        active_cube: int = 0,
    ):
        self.r = r
        self.c = c
        self.orientation = orientation
        self.is_split = is_split
        self.cube1 = cube1 if cube1 is not None else (r, c)
        self.cube2 = cube2 if cube2 is not None else (r, c)
        self.active_cube = active_cube

    def occupied_cells(self) -> List[Tuple[int, int]]:
        """
        Returns list of (row, col) coordinates currently occupied by the block.
        
        Guidelines for Member 1:
        - If is_split: returns [self.cube1, self.cube2]
        - If STANDING: returns [(self.r, self.c)]
        - If LYING_H: returns [(self.r, self.c), (self.r, self.c + 1)]
        - If LYING_V: returns [(self.r, self.c), (self.r + 1, self.c)]
        """
        # TODO [Member 1]: Return list of (row, col) coordinates occupied by the block.
        raise NotImplementedError("Member 1: Implement occupied_cells.")

    def roll(self, direction: Direction) -> "Block":
        """
        Returns a new Block representing the position and orientation after moving.
        Pure function: does NOT mutate self.
        """
        if self.is_split:
            return self._move_split(direction)
        else:
            return self._roll_standard(direction)

    def _roll_standard(self, direction: Direction) -> "Block":
        """
        Standard 1x1x2 block rolling physics.
        
        Orientation transition table to implement:
        -------------------------------------------------------------
        Current Orient | Direction | New Orient | New Anchor (r', c')
        -------------------------------------------------------------
        STANDING       | UP        | LYING_V    | (r - 2, c)
        STANDING       | DOWN      | LYING_V    | (r + 1, c)
        STANDING       | LEFT      | LYING_H    | (r, c - 2)
        STANDING       | RIGHT     | LYING_H    | (r, c + 1)
        -------------------------------------------------------------
        LYING_H        | UP        | LYING_H    | (r - 1, c)
        LYING_H        | DOWN      | LYING_H    | (r + 1, c)
        LYING_H        | LEFT      | STANDING   | (r, c - 1)
        LYING_H        | RIGHT     | STANDING   | (r, c + 2)
        -------------------------------------------------------------
        LYING_V        | UP        | STANDING   | (r - 1, c)
        LYING_V        | DOWN      | STANDING   | (r + 2, c)
        LYING_V        | LEFT      | LYING_V    | (r, c - 1)
        LYING_V        | RIGHT     | LYING_V    | (r, c + 1)
        -------------------------------------------------------------
        """
        # TODO [Member 1]: Implement the 12 orientation roll transitions using the table above.
        raise NotImplementedError("Member 1: Implement _roll_standard transitions.")

    def _move_split(self, direction: Direction) -> "Block":
        """
        Moves the currently active 1x1x1 cube or switches active cube.
        Checks for rejoining into a 1x1x2 block when cubes become adjacent.
        
        Guidelines for Member 1:
        1. If direction == Direction.SWITCH_CUBE:
           Toggle active cube index (0 -> 1 or 1 -> 0).
        2. Otherwise, move the active cube 1 unit in the specified direction.
        3. Check if cubes can merge using self._check_merge(cube1, cube2).
        """
        # TODO [Member 1]: Implement split cube movement and spacebar switching.
        raise NotImplementedError("Member 1: Implement _move_split.")

    @staticmethod
    def _check_merge(cube1: Tuple[int, int], cube2: Tuple[int, int]) -> Optional["Block"]:
        """
        If two 1x1x1 cubes are horizontally or vertically adjacent,
        merges them back into a single standard 1x1x2 block.
        
        Guidelines for Member 1:
        - Horizontally adjacent (r1 == r2 and |c1 - c2| == 1):
          returns Block(r1, min(c1, c2), Orientation.LYING_H, is_split=False)
        - Vertically adjacent (c1 == c2 and |r1 - r2| == 1):
          returns Block(min(r1, r2), c1, Orientation.LYING_V, is_split=False)
        - Otherwise returns None.
        """
        # TODO [Member 1]: Implement merge detection for adjacent cubes.
        raise NotImplementedError("Member 1: Implement _check_merge.")

    def split_into(self, target1: Tuple[int, int], target2: Tuple[int, int]) -> "Block":
        """Teleports and splits the block into two 1x1x1 unit cubes."""
        return Block(
            r=target1[0],
            c=target1[1],
            orientation=Orientation.STANDING,
            is_split=True,
            cube1=target1,
            cube2=target2,
            active_cube=0,
        )

    def to_tuple(self) -> tuple:
        """Returns canonical tuple for hashing in GameState."""
        if self.is_split:
            sorted_cubes = tuple(sorted([self.cube1, self.cube2]))
            return ("SPLIT", sorted_cubes, self.active_cube)
        return ("STANDARD", self.r, self.c, self.orientation.value)

    def __repr__(self) -> str:
        if self.is_split:
            return f"Block(SPLIT, c1={self.cube1}, c2={self.cube2}, active={self.active_cube})"
        return f"Block({self.orientation.value} at ({self.r}, {self.c}))"
