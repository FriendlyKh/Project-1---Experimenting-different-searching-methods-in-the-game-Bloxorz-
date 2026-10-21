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
from ..game.board import Board, Switch
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
        # # TODO [Member 4]: Implement board and switch drawing loop.
        # raise NotImplementedError("Member 4: Implement GameRenderer.draw.")
        cell_size, offset_x, offset_y = self.compute_offsets(board)
        bridge_dict = state.bridge_dict
        # 1. Draw Board Grid & Tiles
        for r in range(board.rows):
            for c in range(board.cols):
                tile = board.get_base_tile(r, c)
                if tile == TileType.VOID:
                    continue
                x = offset_x + c * cell_size
                y = offset_y + r * cell_size
                cell_rect = pygame.Rect(x, y, cell_size, cell_size)
                self._draw_tile(cell_rect, tile, (r, c), board, bridge_dict)
        # 2. Draw Switches on top of tiles
        for pos, switch in board.switches.items():
            r, c = pos
            sx = offset_x + c * cell_size
            sy = offset_y + r * cell_size
            cell_rect = pygame.Rect(sx, sy, cell_size, cell_size)
            self._draw_switch(cell_rect, switch)
        # 3. Draw Block (if not lost / fallen off)
        if state is not None and not is_lost:
            self._draw_block(state.block, cell_size, offset_x, offset_y)
        # 4. Victory / Defeat Overlays
        if is_won:
            self._draw_overlay("STAGE CLEARED! VICTORY!", (80, 220, 120))
        elif is_lost:
            self._draw_overlay("FELL OFF! PRESS 'R' TO RETRY", (235, 75, 75))

    def _draw_tile(
        self,
        rect: pygame.Rect,
        tile: TileType,
        pos: Tuple[int, int],
        board: Board,
        bridge_dict: dict,
    ):
        """Draws individual tile based on its type and current state."""
        inset = 1
        inner_rect = rect.inflate(-2 * inset, -2 * inset)
        if tile == TileType.FLOOR:
            pygame.draw.rect(self.surface, COLOR_FLOOR, inner_rect, border_radius=3)
            pygame.draw.rect(self.surface, COLOR_FLOOR_BORDER, inner_rect, width=1, border_radius=3)
        elif tile == TileType.GOAL:
            pygame.draw.rect(self.surface, COLOR_GOAL, inner_rect, border_radius=4)
            pygame.draw.rect(self.surface, COLOR_GOAL_BORDER, inner_rect, width=3, border_radius=4)
        elif tile == TileType.FRAGILE:
            pygame.draw.rect(self.surface, COLOR_FRAGILE, inner_rect, border_radius=3)
            pygame.draw.rect(self.surface, COLOR_FRAGILE_BORDER, inner_rect, width=2, border_radius=3)
            # Hatch pattern line to visually emphasize fragility
            pygame.draw.line(self.surface, COLOR_FRAGILE_BORDER, inner_rect.topleft, inner_rect.bottomright, 1)
        elif tile == TileType.BRIDGE:
            b_id = board.cell_to_bridge.get(pos)
            is_open = bridge_dict.get(b_id, False) if b_id else False
            if is_open:
                pygame.draw.rect(self.surface, COLOR_BRIDGE_OPEN, inner_rect, border_radius=3)
                pygame.draw.rect(self.surface, (160, 220, 255), inner_rect, width=1, border_radius=3)
            else:
                # Closed bridge drawn with faint outline
                pygame.draw.rect(self.surface, COLOR_BRIDGE_CLOSED, inner_rect, border_radius=3)
                pygame.draw.rect(self.surface, (65, 70, 90), inner_rect, width=1, border_radius=3)

    def _draw_switch(self, rect: pygame.Rect, switch: Switch):
        """Draws switch icon based on its type: SOFT (circle), HEAVY ('X'), SPLIT ('( )')."""
        cx, cy = rect.center
        size = rect.width
        if switch.type == SwitchType.SOFT:
            radius = max(4, size // 4)
            pygame.draw.circle(self.surface, COLOR_SWITCH_SOFT, (cx, cy), radius)
            pygame.draw.circle(self.surface, (180, 150, 20), (cx, cy), radius, width=2)
        elif switch.type == SwitchType.HEAVY:
            arm = max(4, size // 4)
            width = max(2, size // 10)
            pygame.draw.line(self.surface, COLOR_SWITCH_HEAVY, (cx - arm, cy - arm), (cx + arm, cy + arm), width)
            pygame.draw.line(self.surface, COLOR_SWITCH_HEAVY, (cx - arm, cy + arm), (cx + arm, cy - arm), width)
        elif switch.type == SwitchType.SPLIT:
            arm = max(4, size // 4)
            width = max(2, size // 12)
            # Draw split brackets "( )"
            bracket_h = arm + 2
            # Left bracket '('
            pygame.draw.line(self.surface, COLOR_SWITCH_SPLIT, (cx - arm, cy - bracket_h), (cx - arm - 2, cy), width)
            pygame.draw.line(self.surface, COLOR_SWITCH_SPLIT, (cx - arm - 2, cy), (cx - arm, cy + bracket_h), width)
            # Right bracket ')'
            pygame.draw.line(self.surface, COLOR_SWITCH_SPLIT, (cx + arm, cy - bracket_h), (cx + arm + 2, cy), width)
            pygame.draw.line(self.surface, COLOR_SWITCH_SPLIT, (cx + arm + 2, cy), (cx + arm, cy + bracket_h), width)

    def _draw_block(self, block: Block, cell_size: int, offset_x: int, offset_y: int):
        """
        Draws the 3D-shaded block or split cubes.
        
        Guidelines for Member 4:
        - If block.is_split: draw cube 1 and cube 2 with distinct colors and highlight active cube.
        - If standard: draw occupied cells with bevel/shading, highlighting the top face when standing.
        """
        # # TODO [Member 4]: Implement block rendering across orientations and split mode.
        # raise NotImplementedError("Member 4: Implement _draw_block.")
        if block.is_split:
            # Render split cubes independently
            cubes = [(block.cube1, COLOR_SPLIT_CUBE_1, 0), (block.cube2, COLOR_SPLIT_CUBE_2, 1)]
            for (cr, cc), color, c_idx in cubes:
                x = offset_x + cc * cell_size
                y = offset_y + cr * cell_size
                is_active = (block.active_cube == c_idx)
                self._draw_3d_cube(x, y, cell_size, cell_size, color, is_active=is_active)
        else:
            # Standard 1x1x2 block
            x = offset_x + block.c * cell_size
            y = offset_y + block.r * cell_size
            if block.orientation == Orientation.STANDING:
                # 2 units tall upright
                h_elev = int(cell_size * 0.55)
                self._draw_3d_box(x, y, cell_size, cell_size, h_elev, is_standing=True)
            elif block.orientation == Orientation.LYING_H:
                # 2 units wide horizontally, 1 unit tall
                h_elev = int(cell_size * 0.3)
                self._draw_3d_box(x, y, 2 * cell_size, cell_size, h_elev, is_standing=False)
            elif block.orientation == Orientation.LYING_V:
                # 2 units long vertically, 1 unit tall
                h_elev = int(cell_size * 0.3)
                self._draw_3d_box(x, y, cell_size, 2 * cell_size, h_elev, is_standing=False)

    def _draw_3d_box(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        elevation: int,
        is_standing: bool,
    ):
        """Draws a 3D-shaded rectangular block with top and side faces."""
        pad = 2
        top_rect = pygame.Rect(x + pad, y - elevation + pad, width - 2 * pad, height - 2 * pad)
        front_rect = pygame.Rect(x + pad, y + height - elevation - pad, width - 2 * pad, elevation)
        # Front / side face shading
        pygame.draw.rect(self.surface, COLOR_BLOCK, front_rect, border_bottom_left_radius=4, border_bottom_right_radius=4)
        pygame.draw.rect(self.surface, COLOR_BLOCK_BORDER, front_rect, width=2, border_bottom_left_radius=4, border_bottom_right_radius=4)
        # Top face with highlight
        top_color = COLOR_BLOCK_TOP if is_standing else (200, 115, 60)
        pygame.draw.rect(self.surface, top_color, top_rect, border_radius=4)
        pygame.draw.rect(self.surface, COLOR_BLOCK_BORDER, top_rect, width=2, border_radius=4)
        
    def _draw_3d_cube(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: Tuple[int, int, int],
        is_active: bool,
    ):
        """Draws an individual 1x1x1 split cube with active selection halo."""
        pad = 2
        elevation = int(h * 0.35)
        top_rect = pygame.Rect(x + pad, y - elevation + pad, w - 2 * pad, h - 2 * pad)
        front_rect = pygame.Rect(x + pad, y + h - elevation - pad, w - 2 * pad, elevation)
        # Front side
        side_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.rect(self.surface, side_color, front_rect, border_bottom_left_radius=3, border_bottom_right_radius=3)
        pygame.draw.rect(self.surface, COLOR_BLOCK_BORDER, front_rect, width=1, border_bottom_left_radius=3, border_bottom_right_radius=3)
        # Top side
        pygame.draw.rect(self.surface, color, top_rect, border_radius=3)
        if is_active:
            # Active cube highlight outline
            pygame.draw.rect(self.surface, COLOR_ACTIVE_HIGHLIGHT, top_rect, width=3, border_radius=3)
        else:
            pygame.draw.rect(self.surface, COLOR_BLOCK_BORDER, top_rect, width=1, border_radius=3)
    def _draw_overlay(self, message: str, color: Tuple[int, int, int]):
        """Draws banner message across the board."""
        banner_rect = pygame.Rect(self.board_area.left, self.board_area.centery - 40, self.board_area.width, 80)
        overlay_surf = pygame.Surface((banner_rect.width, banner_rect.height), pygame.SRCALPHA)
        overlay_surf.fill((0, 0, 0, 200))
        self.surface.blit(overlay_surf, banner_rect.topleft)
        text = self.font_big.render(message, True, color)
        t_rect = text.get_rect(center=banner_rect.center)
        self.surface.blit(text, t_rect)