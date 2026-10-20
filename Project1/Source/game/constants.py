"""
Game constants, enumerations, and type definitions for Bloxorz.
"""

from enum import Enum, IntEnum


class Orientation(str, Enum):
    """
    Orientation of the 1x1x2 rectangular block.
    - STANDING: occupies 1 cell (r, c)
    - LYING_H: occupies 2 horizontal cells (r, c) and (r, c + 1)
    - LYING_V: occupies 2 vertical cells (r, c) and (r + 1, c)
    """
    STANDING = "standing"
    LYING_H = "horizontal"
    LYING_V = "vertical"


class Direction(str, Enum):
    """
    Directions the block or split cubes can move.
    """
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    # Special action when block is split into 2 cubes: switch active control
    SWITCH_CUBE = "SWITCH_CUBE"


class TileType(IntEnum):
    """
    Board cell types.
    """
    VOID = 0       # Empty space / off-board: block falls
    FLOOR = 1      # Normal solid tile
    GOAL = 2       # Target hole: solved only if block is STANDING upright
    FRAGILE = 3    # Orange tile: safe for LYING block, breaks if STANDING
    BRIDGE = 4     # Passable when open, acts as VOID when closed


class SwitchType(str, Enum):
    """
    Three switch mechanisms as specified in Section 2.5:
    - SOFT: Circle/octagon. Activated by ANY part of block (standing or lying, or 1x1x1 cube)
    - HEAVY: X-shaped. Activated ONLY when 1x1x2 block is STANDING on it
    - SPLIT: Bracket "( )". Activated ONLY when 1x1x2 block is STANDING on it
    """
    SOFT = "soft"
    HEAVY = "heavy"
    SPLIT = "split"


class SwitchOperation(str, Enum):
    """
    How a switch affects its linked bridges:
    - TOGGLE: Inverts the bridge state (open -> closed, closed -> open)
    - PERMANENT: Permanently sets the bridge state to open
    """
    TOGGLE = "toggle"
    PERMANENT = "permanent"
