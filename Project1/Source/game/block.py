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
            return [self.cube1, self.cube2]
        else:
            if self.orientation == Orientation.STANDING:
                return [(self.r, self.c)]
            if self.orientation == Orientation.LYING_H:
                return [(self.r, self.c), (self.r, self.c + 1)]
            elif self.orientation == Orientation.LYING_V:
                return [(self.r, self.c), (self.r + 1, self.c)]

    def roll(self, direction: Direction) -> "Block":
        """
        Returns a new Block representing the position and orientation after moving.
        """
        if self.is_split:
            return self._move_split(direction)
        else:
            return self._roll_standard(direction)

    def _roll_standard(self, direction: Direction) -> "Block":
            r, c = self.r, self.c
            match self.orientation:
                case Orientation.STANDING:
                    if direction == Direction.UP:
                        return Block(r - 2, c, Orientation.LYING_V)
                    elif direction == Direction.DOWN:
                        return Block(r + 1, c, Orientation.LYING_V)
                    elif direction == Direction.LEFT:
                        return Block(r, c - 2, Orientation.LYING_H)
                    elif direction == Direction.RIGHT:
                        return Block(r, c + 1, Orientation.LYING_H)
                case Orientation.LYING_H:
                    if direction == Direction.UP:
                        return Block(r - 1, c, Orientation.LYING_H)
                    elif direction == Direction.DOWN:
                        return Block(r + 1, c, Orientation.LYING_H)
                    elif direction == Direction.LEFT:
                        return Block(r, c - 1, Orientation.STANDING)
                    elif direction == Direction.RIGHT:
                        return Block(r, c + 2, Orientation.STANDING)
                case Orientation.LYING_V:
                    if direction == Direction.UP:
                        return Block(r - 1, c, Orientation.STANDING)
                    elif direction == Direction.DOWN:
                        return Block(r + 2, c, Orientation.STANDING)
                    elif direction == Direction.LEFT:
                        return Block(r, c - 1, Orientation.LYING_V)
                    elif direction == Direction.RIGHT:
                        return Block(r, c + 1, Orientation.LYING_V)
            return Block(r, c, self.orientation)

    def _move_split(self, direction: Direction) -> "Block":
        """
        Moves the currently active 1x1x1 cube or switches active cube.
        Checks for rejoining into a 1x1x2 block when cubes become adjacent.
        """
        # Tạo bản sao các thuộc tính để không làm hỏng state hiện tại khi chưa chắc chắn hợp lệ
        new_c1 = list(self.cube1)
        new_c2 = list(self.cube2)
        new_active = self.active_cube

        if direction == Direction.SWITCH_CUBE:
            return Block(
                r=self.r,
                c=self.c,
                orientation=self.orientation,
                is_split=True,
                cube1=self.cube1,
                cube2=self.cube2,
                active_cube=1 - self.active_cube,
            )
    def _move_split(self, direction: Direction) -> "Block":
        if direction == Direction.SWITCH_CUBE:
            return Block(
                r=self.r,
                c=self.c,
                orientation=self.orientation,
                is_split=True,
                cube1=self.cube1,
                cube2=self.cube2,
                active_cube=1 - self.active_cube,
            )

        dr, dc = 0, 0
        if direction == Direction.UP:
            dr = -1
        elif direction == Direction.DOWN:
            dr = 1
        elif direction == Direction.LEFT:
            dc = -1
        elif direction == Direction.RIGHT:
            dc = 1

        c1, c2 = self.cube1, self.cube2
        if self.active_cube == 0:
            c1 = (c1[0] + dr, c1[1] + dc)
        else:
            c2 = (c2[0] + dr, c2[1] + dc)

        merged = self._check_merge(c1, c2)
        if merged is not None:
            return merged

        return Block(
            r=c1[0],
            c=c1[1],
            orientation=Orientation.STANDING,
            is_split=True,
            cube1=c1,
            cube2=c2,
            active_cube=self.active_cube,
        )


    @staticmethod
    def _check_merge(cube1: Tuple[int, int], cube2: Tuple[int, int]) -> Optional["Block"]:
        if (cube1[0] == cube2[0]) and (abs(cube1[1] - cube2[1]) == 1):
            return Block(cube1[0], min(cube1[1], cube2[1]), Orientation.LYING_H, is_split=False)
        if (cube1[1] == cube2[1]) and (abs(cube1[0] - cube2[0]) == 1):
            return Block(min(cube1[0], cube2[0]), cube1[1], Orientation.LYING_V, is_split=False)
        return None

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
            active_pos = self.cube1 if self.active_cube == 0 else self.cube2
            return ("SPLIT", tuple(sorted([self.cube1, self.cube2])), active_pos)
        return ("STANDARD", self.r, self.c, self.orientation.value)


    def __eq__(self, other):
        return isinstance(other, Block) and self.to_tuple() == other.to_tuple()

    def __hash__(self):
        return hash(self.to_tuple())
    
    def __repr__(self) -> str:
        if self.is_split:
            return f"Block(SPLIT, c1={self.cube1}, c2={self.cube2}, active={self.active_cube})"
        return f"Block({self.orientation.value} at ({self.r}, {self.c}))"