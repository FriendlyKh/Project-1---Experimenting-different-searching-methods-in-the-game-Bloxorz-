"""
Block representation and orientation physics for Bloxorz.
Assigned to: Member 1 (Core Game Mechanics & State Modeling)

Handles both standard 1x1x2 block and split 1x1x1 unit cubes.
"""

from typing import Tuple, List, Optional
from .constants import Orientation, Direction


class Block:
    """
    A block in Bloxorz.
    Two modes:
    1. Standard 1x1x2 block:
       - Positioned at top anchor (r, c) and have 3 orientation (STANDING, LYING_H, LYING_V).
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
        """
        if self.is_split:
            return [self.cube1,self.cube2]
        else:
            if self.orientation == Orientation.STANDING:
                return [(self.r, self.c)]
            if self.orientation ==  Orientation.LYING_H:
                return [(self.r, self.c),(self.r,self.c+1)]
            elif self.orientation ==  Orientation.LYING_V:
                return [(self.r, self.c),(self.r+1,self.c)]

    def roll(self, direction: Direction) -> "Block":
        """
        Returns a new Block representing the position and orientation after moving.
        """
        if self.is_split:
            return self._move_split(direction)
        else:
            return self._roll_standard(direction)

    def _roll_standard(self, direction: Direction) -> "Block":
        """
        Standard 1x1x2 block rolling physics.
        Table of directions:
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
        match self.orientation:
            case Orientation.STANDING:
                if direction == "UP":
                    self.orientation = Orientation.LYING_V
                    self.r -= 2
                elif direction == "DOWN":
                    self.orientation = Orientation.LYING_V
                    self.r += 1
                elif direction == "LEFT":
                    self.orientation = Orientation.LYING_H
                    self.c -= 1
                elif direction == "RIGHT":
                    self.orientation = Orientation.LYING_H
                    self.c += 2
            case Orientation.LYING_H:
                if direction == Direction.UP:
                    self.r -= 1
                elif direction == "DOWN":
                    self.r += 1
                elif direction == "LEFT":
                    self.orientation = Orientation.STANDING
                    self.c -= 1
                elif direction == "RIGHT":
                    self.orientation = Orientation.STANDING
                    self.c += 2
            case Orientation.LYING_V:
                if direction == "UP":
                    self.orientation = Orientation.STANDING
                    self.r -= 1
                elif direction == "DOWN":
                    self.orientation = Orientation.STANDING
                    self.r += 2
                elif direction == "LEFT":
                    self.c -= 1
                elif direction == "RIGHT":
                    self.c += 1
        raise NotImplementedError()

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
        if direction == Direction.SWITCH_CUBE:
            self.active_cube = not self.active_cube
        else:
            if self.active_cube == 0:
                match direction:
                    case Direction.UP:
                        self.cube1[0] -= 1
                    case Direction.DOWN:
                        self.cube1[0] += 1
                    case Direction.LEFT:
                        self.cube1[1] -= 1
                    case Direction.RIGHT:
                        self.cube1[1] += 1
            else:
                match direction:
                    case Direction.UP:
                        self.cube2[0] -= 1
                    case Direction.DOWN:
                        self.cube2[0] += 1
                    case Direction.LEFT:
                        self.cube2[1] -= 1
                    case Direction.RIGHT:
                        self.cube2[1] += 1


        raise NotImplementedError("Member 1: Implement _move_split.")

    @staticmethod
    def _check_merge(cube1: Tuple[int, int], cube2: Tuple[int, int]) -> Optional["Block"]:
        """
        If two 1x1x1 cubes are horizontally or vertically adjacent,
        merges them back into a single standard 1x1x2 block.

        """
        if (cube1[0] == cube2[0]) and (abs(cube1[1] - cube2[1]) == 1):
            return Block(cube1[0], min(cube1[1], cube2[1]), Orientation.LYING_H, is_split=False)
        if (cube1[1] == cube2[1]) and (abs(cube1[0] - cube2[0]) == 1):
            return Block(min(cube1[0], cube2[0]), cube1[0], Orientation.LYING_V, is_split=False)
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
