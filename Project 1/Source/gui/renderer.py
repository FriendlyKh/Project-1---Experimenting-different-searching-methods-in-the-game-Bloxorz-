"""
Rendering engine for Bloxorz tiles, bridges, switches, and block orientations.
Assigned to: Member 4 (GUI & Visualization)

Project Requirements (Section 3.1 & 3.7):
- GUI displaying floor tiles, void, goal hole, fragile tiles, bridges, switches.
- Clearly show the block in its various orientations (Standing, Lying H, Lying V, Split).
"""

from typing import Tuple
import pygame
from ..game.constants import TileType, SwitchType, Orientation
from ..game.board import Board
from ..game.block import Block
from ..game.state import GameState
from ..config import (
    COLOR_BG,
    COLOR_FLOOR,
    COLOR_FLOOR_BORDER,
    COLOR_GOAL,
    COLOR_GOAL_BORDER,
    COLOR_FRAGILE,
    COLOR_FRAGILE_BORDER,
    COLOR_BRIDGE_OPEN,
    COLOR_BRIDGE_CLOSED,
    COLOR_SWITCH_SOFT,
    COLOR_SWITCH_HEAVY,
    COLOR_SWITCH_SPLIT,
    COLOR_BLOCK,
    COLOR_BLOCK_BORDER,
    COLOR_BLOCK_TOP,
    COLOR_SPLIT_CUBE_1,
    COLOR_SPLIT_CUBE_2,
    COLOR_ACTIVE_HIGHLIGHT,
)


class GameRenderer:
    """
    Renders the Bloxorz board, dynamic bridges, switches, and the block.
    """

    def __init__(self, surface: pygame.Surface, board_area: pygame.Rect):
        self.surface = surface
        self.board_area = board_area
        self.font_small = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 32, bold=True)

    def compute_offsets(self, board: Board) -> Tuple[int, int, int]:
        """
        Dynamically calculates tile size and centered offsets to fit the board area.
        """
        max_w = self.board_area.width - 40
        max_h = self.board_area.height - 40
        cell_size = min(max_w // max(1, board.cols), max_h // max(1, board.rows))
        cell_size = max(24, min(56, cell_size))
        total_w = board.cols * cell_size
        total_h = board.rows * cell_size
        offset_x = self.board_area.left + (self.board_area.width - total_w) // 2
        offset_y = self.board_area.top + (self.board_area.height - total_h) // 2
        return cell_size, offset_x, offset_y

    def draw(
        self,
        board: Board,
        state: GameState,
        is_won: bool = False,
        is_lost: bool = False,
    ):
        """
        Full frame render of the board, active bridges, switches, and the block.
        
        Guidelines for Member 4:
        1. Compute cell size and offsets using self.compute_offsets(board).
        2. Iterate over board.grid:
           - Draw FLOOR, GOAL, FRAGILE, and BRIDGE tiles with distinct colors.
        3. Draw switches (board.switches):
           - SOFT: circle
           - HEAVY: 'X'
           - SPLIT: '( )'
        4. Draw the block using self._draw_block(state.block, ...).
        5. Draw overlays if is_won or is_lost.
        """
        # TODO [Member 4]: Implement board and switch drawing loop.
        raise NotImplementedError("Member 4: Implement GameRenderer.draw.")

    def _draw_block(self, block: Block, cell_size: int, offset_x: int, offset_y: int):
        """
        Draws the 3D-shaded block or split cubes.
        
        Guidelines for Member 4:
        - If block.is_split: draw cube 1 and cube 2 with distinct colors and highlight active cube.
        - If standard: draw occupied cells with bevel/shading, highlighting the top face when standing.
        """
        # TODO [Member 4]: Implement block rendering across orientations and split mode.
        raise NotImplementedError("Member 4: Implement _draw_block.")

    def _draw_overlay(self, message: str, color: Tuple[int, int, int]):
        """Draws banner message across the board."""
        banner_rect = pygame.Rect(self.board_area.left, self.board_area.centery - 40, self.board_area.width, 80)
        overlay_surf = pygame.Surface((banner_rect.width, banner_rect.height), pygame.SRCALPHA)
        overlay_surf.fill((0, 0, 0, 200))
        self.surface.blit(overlay_surf, banner_rect.topleft)
        text = self.font_big.render(message, True, color)
        t_rect = text.get_rect(center=banner_rect.center)
        self.surface.blit(text, t_rect)
