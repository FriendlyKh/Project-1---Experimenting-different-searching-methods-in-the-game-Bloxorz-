"""
Cute & Bright Dual-Mode Rendering Engine for Bloxorz Solver with:
- Interactive 3D Viewpoint Camera (Orbit Yaw/Pitch, Mouse Drag Pan, Scroll Wheel Zoom)
- Smooth Block Roll / Parabolic Hop / Split-Arc / Squash-and-Stretch Animations
- Continuous Ambient Animations (Rotating Starlight Goal, Blinking Kawaii Block, Flowing Path Pulses)
- Mode 1 ('2.5D'): Rotatable 3D / 2.5D Voxel Diorama with depth-sorted 3D tiles, dynamic face lighting,
  procedural textures (ceramic, honeycomb wafer, wooden planks, sunken portal), and cast shadows.
- Mode 2 ('2D'): Zoomable & Pannable Top-Down Algorithm Visualization view with explored-cell heatmap,
  heuristic h(n) values, switch-to-bridge causal links, animated path pulses, and step badges.

Assigned to: Member 4 (GUI & Visualization)
"""

import math
from typing import Tuple, List, Dict, Optional
import pygame

from ..game.constants import TileType, SwitchType, Orientation
from ..game.board import Board, Switch
from ..game.block import Block
from ..game.state import GameState
from ..config import (
    VIEW_MODE_25D,
    VIEW_MODE_2D,
    DEFAULT_CAM_YAW,
    DEFAULT_CAM_PITCH,
    DEFAULT_CAM_ZOOM,
    MIN_CAM_ZOOM,
    MAX_CAM_ZOOM,
    MIN_CAM_PITCH,
    MAX_CAM_PITCH,
    COLOR_BG,
    COLOR_BG_ACCENT,
    COLOR_BOARD_MAT,
    COLOR_BOARD_MAT_BORDER,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_FLOOR,
    COLOR_FLOOR_SHADE,
    COLOR_FLOOR_BORDER,
    COLOR_FLOOR_SIDE,
    COLOR_FLOOR_SIDE_DARK,
    COLOR_GOAL,
    COLOR_GOAL_INNER,
    COLOR_GOAL_GLOW,
    COLOR_GOAL_BORDER,
    COLOR_FRAGILE,
    COLOR_FRAGILE_STRIPE,
    COLOR_FRAGILE_BORDER,
    COLOR_FRAGILE_SIDE,
    COLOR_BRIDGE_OPEN,
    COLOR_BRIDGE_OPEN_PLANK,
    COLOR_BRIDGE_OPEN_BORDER,
    COLOR_BRIDGE_OPEN_SIDE,
    COLOR_BRIDGE_CLOSED,
    COLOR_BRIDGE_CLOSED_BORDER,
    COLOR_SWITCH_SOFT,
    COLOR_SWITCH_SOFT_RIM,
    COLOR_SWITCH_HEAVY,
    COLOR_SWITCH_HEAVY_RIM,
    COLOR_SWITCH_SPLIT,
    COLOR_SWITCH_SPLIT_RIM,
    COLOR_BLOCK,
    COLOR_BLOCK_TOP,
    COLOR_BLOCK_SIDE,
    COLOR_BLOCK_BORDER,
    COLOR_BLOCK_SHINE,
    COLOR_SPLIT_CUBE_1,
    COLOR_SPLIT_CUBE_1_SIDE,
    COLOR_SPLIT_CUBE_2,
    COLOR_SPLIT_CUBE_2_SIDE,
    COLOR_ACTIVE_HIGHLIGHT,
    COLOR_VIS_EXPLORED,
    COLOR_VIS_EXPLORED_BORDER,
    COLOR_VIS_PATH,
    COLOR_VIS_PATH_NODE,
    COLOR_VIS_START,
    COLOR_VIS_LINK,
)
from .widgets import draw_soft_shadow, draw_pastel_card


def _clamp_color(rgb: Tuple[int, int, int], delta: int) -> Tuple[int, int, int]:
    return (
        max(0, min(255, int(rgb[0] + delta))),
        max(0, min(255, int(rgb[1] + delta))),
        max(0, min(255, int(rgb[2] + delta))),
    )


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease_out_Back(t: float) -> float:
    """Smooth cubic ease-out with subtle toy overshoot."""
    t = max(0.0, min(1.0, t))
    c1 = 1.15
    c3 = c1 + 1.0
    return 1.0 + c3 * pow(t - 1.0, 3) + c1 * pow(t - 1.0, 2)


class GameRenderer:
    """
    Renders the Bloxorz board, dynamic bridges, switches, algorithm overlays, and the animated block
    with an interactive 3D / 2.5D Orbit Camera and a Pan/Zoom 2D Algorithm Visualization Camera.
    """

    def __init__(self, surface: pygame.Surface, board_area: pygame.Rect):
        self.surface = surface
        self.board_area = board_area
        self.view_mode: str = VIEW_MODE_25D

        # Interactive Camera State (Pan, Zoom, 3D Orbit Yaw & Pitch)
        self.cam_pan_x: float = 0.0
        self.cam_pan_y: float = 0.0
        self.cam_zoom: float = DEFAULT_CAM_ZOOM
        self.cam_yaw: float = DEFAULT_CAM_YAW        # degrees (0..360)
        self.cam_pitch: float = DEFAULT_CAM_PITCH    # degrees (24..84)

        self.font_tiny = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 11, bold=True)
        self.font_small = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 13, bold=True)
        self.font_badge = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 14, bold=True)
        self.font_big = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 26, bold=True)
        self.font_sub = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 15, bold=False)

    # ========================================================================
    # CAMERA CONTROLS (PAN, ZOOM, ORBIT 3D VIEWPOINT)
    # ========================================================================

    def reset_camera(self):
        """Resets camera pan, zoom, and 3D viewpoint angles to default."""
        self.cam_pan_x = 0.0
        self.cam_pan_y = 0.0
        self.cam_zoom = DEFAULT_CAM_ZOOM
        self.cam_yaw = DEFAULT_CAM_YAW
        self.cam_pitch = DEFAULT_CAM_PITCH

    def pan_camera(self, dx: float, dy: float):
        """Translates the camera viewport by (dx, dy) pixels."""
        self.cam_pan_x += dx
        self.cam_pan_y += dy

    def orbit_camera(self, d_yaw: float, d_pitch: float):
        """Rotates the 3D viewpoint yaw and pitch angles in degrees."""
        self.cam_yaw = (self.cam_yaw + d_yaw) % 360.0
        self.cam_pitch = max(MIN_CAM_PITCH, min(MAX_CAM_PITCH, self.cam_pitch + d_pitch))

    def zoom_camera(self, factor: float, pivot: Optional[Tuple[int, int]] = None):
        """Zooms the camera smoothly around the given screen pivot (or playmat center)."""
        old_zoom = self.cam_zoom
        new_zoom = max(MIN_CAM_ZOOM, min(MAX_CAM_ZOOM, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 1e-4:
            return
        if pivot is not None:
            cx = self.board_area.centerx + self.cam_pan_x
            cy = self.board_area.centery + 8 + self.cam_pan_y
            px, py = pivot
            scale_ratio = new_zoom / old_zoom
            self.cam_pan_x += (px - cx) * (1.0 - scale_ratio)
            self.cam_pan_y += (py - cy) * (1.0 - scale_ratio)
        self.cam_zoom = new_zoom

    def set_view_mode(self, mode: str):
        """Sets the active rendering mode ('2.5D' or '2D')."""
        if mode in (VIEW_MODE_25D, VIEW_MODE_2D):
            self.view_mode = mode

    def toggle_view_mode(self) -> str:
        """Toggles between 2.5D and 2D modes and returns the new mode."""
        self.view_mode = VIEW_MODE_2D if self.view_mode == VIEW_MODE_25D else VIEW_MODE_25D
        return self.view_mode

    def compute_offsets(self, board: Board) -> Tuple[int, int, int]:
        """
        Calculates scaled cell size and panned offsets for 2D mode (and base scale for 3D mode).
        """
        pad_x = 96
        pad_top = 100
        pad_bottom = 96
        avail_w = max(120, self.board_area.width - pad_x)
        avail_h = max(120, self.board_area.height - pad_top - pad_bottom)

        base_cell = min(avail_w / max(1, board.cols), avail_h / max(1, board.rows))
        base_cell = max(22.0, min(58.0, base_cell))
        cell_size = max(12, int(round(base_cell * self.cam_zoom)))

        total_w = board.cols * cell_size
        total_h = board.rows * cell_size

        offset_x = int(self.board_area.left + (self.board_area.width - total_w) / 2.0 + self.cam_pan_x)
        offset_y = int(
            self.board_area.top
            + pad_top
            + (avail_h - total_h) / 2.0
            + self.cam_pan_y
        )
        return cell_size, offset_x, offset_y

    # ========================================================================
    # 3D PROJECTION MATH
    # ========================================================================

    def _get_3d_params(self, board: Board) -> Tuple[float, float, float, float, float, float, float]:
        """Returns (scale, center_sx, center_sy, cx_grid, cy_grid, yaw_rad, pitch_rad)."""
        pad_x = 120
        pad_y = 140
        avail_w = max(120, self.board_area.width - pad_x)
        avail_h = max(120, self.board_area.height - pad_y)
        diag = math.hypot(board.cols, board.rows)
        base_scale = min(avail_w / max(1.0, diag * 0.92), avail_h / max(1.0, diag * 0.72))
        base_scale = max(20.0, min(54.0, base_scale))
        scale = base_scale * self.cam_zoom

        center_sx = self.board_area.centerx + self.cam_pan_x
        center_sy = self.board_area.centery + 14 + self.cam_pan_y
        cx_grid = board.cols / 2.0
        cy_grid = board.rows / 2.0
        yaw_rad = math.radians(self.cam_yaw)
        pitch_rad = math.radians(self.cam_pitch)
        return scale, center_sx, center_sy, cx_grid, cy_grid, yaw_rad, pitch_rad

    @staticmethod
    def _project_pt(
        gx: float,
        gy: float,
        gz: float,
        scale: float,
        center_sx: float,
        center_sy: float,
        cx_grid: float,
        cy_grid: float,
        yaw_rad: float,
        pitch_rad: float,
    ) -> Tuple[int, int]:
        """Projects a 3D grid coordinate (gx=col, gy=row, gz=height) onto 2D screen pixels."""
        dx = gx - cx_grid
        dy = gy - cy_grid
        rx = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
        ry = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)
        sx = center_sx + rx * scale
        sy = center_sy + (ry * math.sin(pitch_rad) - gz * math.cos(pitch_rad)) * scale
        return (int(round(sx)), int(round(sy)))

    @staticmethod
    def _depth_of(gx: float, gy: float, gz: float, cx_grid: float, cy_grid: float, yaw_rad: float, pitch_rad: float) -> float:
        """Computes camera-space depth for Painter's algorithm back-to-front sorting."""
        dx = gx - cx_grid
        dy = gy - cy_grid
        ry = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)
        return ry * math.cos(pitch_rad) + gz * 0.25

    # ========================================================================
    # MAIN DRAW ENTRYPOINT
    # ========================================================================

    def draw(
        self,
        board: Board,
        state: GameState,
        is_won: bool = False,
        is_lost: bool = False,
        view_mode: Optional[str] = None,
        explored_cells: Optional[Dict[Tuple[int, int], int]] = None,
        replay_states: Optional[List[GameState]] = None,
        replay_idx: int = 0,
        show_algo_overlay: bool = True,
        prev_state: Optional[GameState] = None,
        anim_progress: float = 1.0,
        anim_time: float = 0.0,
        death_anim_t: float = -1.0,
        level_transition_t: float = -1.0,
        level_transition_dir: int = 1,
    ):
        """
        Full frame render of the canvas, playmat, 3D/2D board, animated block,
        and interactive camera HUD.
        """
        mode = view_mode if view_mode is not None else self.view_mode
        bridge_dict = state.bridge_dict if state is not None else {}

        # Cache normalised death phase for use deep inside _draw_animated_block_3d
        from ..config import DEATH_ANIM_DURATION as _DAD
        self._death_anim_t_cache = (
            max(0.0, min(1.0, death_anim_t / max(0.001, _DAD)))
            if death_anim_t >= 0 else 0.0
        )

        # ── Real screen-shake: nudge cam_pan while the board renders ──────────
        # Restoring it afterwards keeps state clean for the next frame.
        shake_x = shake_y = 0.0
        if is_lost and 0.0 <= death_anim_t < 0.60:
            phase_sh = max(0.0, 1.0 - death_anim_t / 0.60)
            amp = (phase_sh ** 1.4) * 11.0
            shake_x = amp * math.sin(death_anim_t * 76.0)
            shake_y = amp * math.cos(death_anim_t * 61.0) * 0.50
            self.cam_pan_x += shake_x
            self.cam_pan_y += shake_y

        # ── Compute actual block screen-center (used by death particles) ──────
        block_screen_pos: Tuple[int, int] = (self.board_area.centerx, self.board_area.centery)
        if state is not None:
            try:
                if mode == VIEW_MODE_2D:
                    cs, ox, oy = self.compute_offsets(board)
                    block_screen_pos = self._state_center_px(state.block, cs, ox, oy)
                else:
                    sc, csx, csy, cxg, cyg, yr, pr = self._get_3d_params(board)
                    cells = state.block.occupied_cells()
                    avg_r = sum(c[0] for c in cells) / len(cells)
                    avg_c = sum(c[1] for c in cells) / len(cells)
                    bx, by = self._project_pt(
                        avg_c + 0.5, avg_r + 0.5, 0.5,
                        sc, csx, csy, cxg, cyg, yr, pr,
                    )
                    block_screen_pos = (bx, by)
            except Exception:
                pass

        # 1. Draw Cute Bright Polka-Dot / Pastel Cloud Canvas & Playmat Frame
        self._draw_canvas_background(board, mode, explored_cells, replay_states, replay_idx)

        # Clip board rendering strictly to the inner playmat viewport so zoomed/panned tiles never spill out
        viewport_clip = pygame.Rect(
            self.board_area.left + 26,
            self.board_area.top + 64,
            self.board_area.width - 52,
            self.board_area.height - 130,
        )
        prev_clip = self.surface.get_clip() if hasattr(self.surface, "get_clip") else None
        if hasattr(self.surface, "set_clip"):
            self.surface.set_clip(viewport_clip)

        # 2. Render Board & Animated Block according to mode
        if mode == VIEW_MODE_2D:
            cell_size, offset_x, offset_y = self.compute_offsets(board)
            self._draw_board_2d(
                board=board,
                state=state,
                prev_state=prev_state,
                anim_progress=anim_progress,
                anim_time=anim_time,
                bridge_dict=bridge_dict,
                cell_size=cell_size,
                offset_x=offset_x,
                offset_y=offset_y,
                is_lost=is_lost,
                explored_cells=explored_cells if show_algo_overlay else None,
                replay_states=replay_states if show_algo_overlay else None,
                replay_idx=replay_idx,
            )
        else:
            self._draw_board_3d_viewpoint(
                board=board,
                state=state,
                prev_state=prev_state,
                anim_progress=anim_progress,
                anim_time=anim_time,
                bridge_dict=bridge_dict,
                is_lost=is_lost,
                is_won=is_won,
                explored_cells=explored_cells if show_algo_overlay else None,
                replay_states=replay_states if show_algo_overlay else None,
                replay_idx=replay_idx,
            )

        if hasattr(self.surface, "set_clip"):
            self.surface.set_clip(prev_clip)

        # Restore screen-shake offset so cam state stays clean
        if shake_x or shake_y:
            self.cam_pan_x -= shake_x
            self.cam_pan_y -= shake_y

        # 3. Draw Floating Camera Status & Controls Hint Pill + Bottom Legend Strip
        self._draw_camera_hud_strip(mode)
        self._draw_legend_bar(mode)

        # 4. Death animation effects (particles burst from actual block position)
        if death_anim_t >= 0:
            self._draw_death_effects(death_anim_t, anim_time, block_screen_pos)

        # 5. Victory Confetti & Cute Banner Overlays
        if is_won:
            self._draw_victory_confetti(anim_time)
            self._draw_overlay(
                "STAGE CLEARED! WONDERFUL JOB!",
                "Press 'N' for Next Stage or 'R' to Replay",
                bg_color=(236, 253, 245),
                border_color=(82, 204, 146),
                title_color=(36, 138, 92),
            )
        elif is_lost and death_anim_t >= 0.80:
            # Show the death banner only after the fall animation has played
            self._draw_overlay(
                "OOPS! BLOCK FELL OFF THE BOARD!",
                "Press 'R' or Click Reset to Try Again",
                bg_color=(255, 240, 244),
                border_color=(242, 106, 132),
                title_color=(198, 52, 82),
            )

        # 6. Level-swipe transition overlay (drawn last so it covers everything)
        if level_transition_t >= 0:
            self._draw_level_transition(level_transition_t, level_transition_dir)



    # ========================================================================
    # CANVAS, HEADER & CAMERA HUD
    # ========================================================================

    def _draw_canvas_background(
        self,
        board: Board,
        mode: str,
        explored_cells: Optional[Dict[Tuple[int, int], int]],
        replay_states: Optional[List[GameState]],
        replay_idx: int,
    ):
        """Draws the pastel sky-cream background, polka dots, playmat card, and top header bar."""
        pygame.draw.rect(self.surface, COLOR_BG, self.board_area)

        dot_spacing = 36
        for y in range(self.board_area.top + 18, self.board_area.bottom, dot_spacing):
            row_shift = 18 if ((y // dot_spacing) % 2 == 1) else 0
            for x in range(self.board_area.left + 18 + row_shift, self.board_area.right - 10, dot_spacing):
                pygame.draw.circle(self.surface, COLOR_BG_ACCENT, (x, y), 3)

        blob_surf = pygame.Surface((self.board_area.width, self.board_area.height), pygame.SRCALPHA)
        pygame.draw.circle(blob_surf, (255, 218, 232, 70), (70, 70), 95)
        pygame.draw.circle(blob_surf, (208, 240, 236, 75), (self.board_area.width - 80, self.board_area.height - 75), 110)
        pygame.draw.circle(blob_surf, (230, 218, 255, 65), (self.board_area.width - 90, 85), 80)
        self.surface.blit(blob_surf, self.board_area.topleft)

        mat_rect = pygame.Rect(
            self.board_area.left + 20,
            self.board_area.top + 16,
            self.board_area.width - 40,
            self.board_area.height - 32,
        )
        draw_pastel_card(
            self.surface,
            mat_rect,
            bg_color=COLOR_BOARD_MAT,
            border_color=COLOR_BOARD_MAT_BORDER,
            radius=22,
            shadow=True,
        )

        header_rect = pygame.Rect(mat_rect.left + 16, mat_rect.top + 14, mat_rect.width - 32, 42)
        pygame.draw.rect(self.surface, (240, 245, 255), header_rect, border_radius=12)
        pygame.draw.rect(self.surface, (216, 226, 246), header_rect, width=1, border_radius=12)

        mode_badge_rect = pygame.Rect(header_rect.left + 8, header_rect.top + 6, 208, 30)
        if mode == VIEW_MODE_25D:
            badge_bg = (255, 226, 236)
            badge_border = (244, 162, 188)
            badge_txt_col = (188, 56, 98)
            badge_str = "3D / 2.5D Orbit View"
        else:
            badge_bg = (218, 238, 255)
            badge_border = (138, 190, 248)
            badge_txt_col = (44, 108, 186)
            badge_str = "2D Algorithm Vis Mode"

        pygame.draw.rect(self.surface, badge_bg, mode_badge_rect, border_radius=8)
        pygame.draw.rect(self.surface, badge_border, mode_badge_rect, width=1, border_radius=8)
        badge_surf = self.font_badge.render(badge_str, True, badge_txt_col)
        self.surface.blit(badge_surf, badge_surf.get_rect(center=mode_badge_rect.center))

        info_parts = [f"Grid: {board.rows}x{board.cols}", f"Zoom: {int(round(self.cam_zoom * 100))}%"]
        if mode == VIEW_MODE_25D:
            info_parts.append(f"3D Angle: {int(round(self.cam_yaw))}° / {int(round(self.cam_pitch))}°")
        if explored_cells:
            info_parts.append(f"Visited: {len(explored_cells)}")
        if replay_states and len(replay_states) > 1:
            info_parts.append(f"Step: {replay_idx}/{len(replay_states) - 1}")
        info_str = "  |  ".join(info_parts)
        info_surf = self.font_tiny.render(info_str, True, COLOR_TEXT_MUTED)
        self.surface.blit(
            info_surf,
            (header_rect.right - info_surf.get_width() - 14, header_rect.centery - info_surf.get_height() // 2),
        )

    def _draw_camera_hud_strip(self, mode: str):
        """Draws a clean camera gesture hint badge at the bottom-left above the legend bar."""
        hint_rect = pygame.Rect(self.board_area.left + 36, self.board_area.bottom - 90, 428, 24)
        hint_surf = pygame.Surface((hint_rect.width, hint_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(hint_surf, (238, 244, 255, 215), hint_surf.get_rect(), border_radius=8)
        self.surface.blit(hint_surf, hint_rect.topleft)
        pygame.draw.rect(self.surface, (212, 224, 246), hint_rect, width=1, border_radius=8)

        if mode == VIEW_MODE_25D:
            txt = "LMB Drag: Pan  |  RMB Drag (Q/E/W/S): 3D Orbit  |  Wheel: Zoom"
        else:
            txt = "LMB Drag: Pan Screen  |  Mouse Wheel (+/-): Zoom  |  C: Center"
        lbl = self.font_tiny.render(txt, True, COLOR_TEXT_MUTED)
        self.surface.blit(lbl, (hint_rect.left + 10, hint_rect.centery - lbl.get_height() // 2))

    def _draw_legend_bar(self, mode: str):
        """Draws a cute compact legend strip along the bottom of the playmat."""
        mat_left = self.board_area.left + 36
        mat_w = self.board_area.width - 72
        leg_rect = pygame.Rect(mat_left, self.board_area.bottom - 58, mat_w, 32)
        pygame.draw.rect(self.surface, (242, 246, 254), leg_rect, border_radius=10)
        pygame.draw.rect(self.surface, (220, 228, 245), leg_rect, width=1, border_radius=10)

        items = [
            (COLOR_FLOOR, COLOR_FLOOR_BORDER, "Floor"),
            (COLOR_FRAGILE, COLOR_FRAGILE_BORDER, "Fragile"),
            (COLOR_BRIDGE_OPEN, COLOR_BRIDGE_OPEN_BORDER, "Bridge"),
            (COLOR_SWITCH_SOFT, COLOR_SWITCH_SOFT_RIM, "Soft (O)"),
            (COLOR_SWITCH_HEAVY, COLOR_SWITCH_HEAVY_RIM, "Heavy (X)"),
            (COLOR_SWITCH_SPLIT, COLOR_SWITCH_SPLIT_RIM, "Split ( )"),
            (COLOR_GOAL_GLOW, COLOR_GOAL, "Goal"),
        ]
        if mode == VIEW_MODE_2D:
            items.append((COLOR_VIS_EXPLORED, COLOR_VIS_EXPLORED_BORDER, "Visited"))
            items.append((COLOR_VIS_PATH, (200, 60, 100), "Path"))

        spacing = leg_rect.width // len(items)
        for i, (fill_c, border_c, label) in enumerate(items):
            ix = leg_rect.left + i * spacing + 10
            iy = leg_rect.centery
            swatch = pygame.Rect(ix, iy - 7, 14, 14)
            pygame.draw.rect(self.surface, fill_c, swatch, border_radius=4)
            pygame.draw.rect(self.surface, border_c, swatch, width=1, border_radius=4)
            lbl_surf = self.font_tiny.render(label, True, COLOR_TEXT)
            self.surface.blit(lbl_surf, (ix + 18, iy - lbl_surf.get_height() // 2))

    # ========================================================================
    # MODE 1: TRUE 3D / 2.5D ORBITABLE VIEWPOINT RENDERER
    # ========================================================================

    def _draw_board_3d_viewpoint(
        self,
        board: Board,
        state: GameState,
        prev_state: Optional[GameState],
        anim_progress: float,
        anim_time: float,
        bridge_dict: dict,
        is_lost: bool,
        is_won: bool,
        explored_cells: Optional[Dict[Tuple[int, int], int]],
        replay_states: Optional[List[GameState]],
        replay_idx: int,
    ):
        """
        Renders the entire puzzle island and animated block using true 3D viewpoint projection
        with full 360-degree camera yaw & pitch orbit and depth-sorted Painter's algorithm.
        """
        scale, csx, csy, cx_g, cy_g, yaw_rad, pitch_rad = self._get_3d_params(board)
        slab_dz = 0.28  # 3D thickness of board tiles in grid units

        def proj(gx: float, gy: float, gz: float) -> Tuple[int, int]:
            return self._project_pt(gx, gy, gz, scale, csx, csy, cx_g, cy_g, yaw_rad, pitch_rad)

        # 1. Pass 1: Soft floating-island shadow on a plane beneath the tiles (gz = -0.52)
        shadow_hover = 0.03 * math.sin(anim_time * 2.2)
        sh_plane_z = -0.50 + shadow_hover
        for r in range(board.rows):
            for c in range(board.cols):
                tile = board.get_base_tile(r, c)
                if tile == TileType.VOID:
                    continue
                if tile == TileType.BRIDGE:
                    b_id = board.cell_to_bridge.get((r, c))
                    if not (bridge_dict.get(b_id, False) if b_id else False):
                        continue
                pts = [
                    proj(c + 0.04, r + 0.04, sh_plane_z),
                    proj(c + 0.96, r + 0.04, sh_plane_z),
                    proj(c + 0.96, r + 0.96, sh_plane_z),
                    proj(c + 0.04, r + 0.96, sh_plane_z),
                ]
                pygame.draw.polygon(self.surface, (206, 216, 238), pts)

        # 2. Render Board Tiles and Block:
        # NORMAL PLAY: Block is ALWAYS drawn in front of board tiles (Pass 2 = tiles, Pass 4 = block).
        # WHEN DYING (is_lost): The entire board platform is drawn IN FRONT of the falling block
        # (Pass 2 = falling block, Pass 3 = board tiles), so the platform occludes the block as it
        # falls off into the abyss, and the block disappears completely once behind the platform.
        if is_lost:
            # First draw the falling block (deep below), disappearing when fully plunged
            death_phase = max(0.0, min(1.0, getattr(self, "_death_anim_t_cache", 0.0)))
            if state is not None and death_phase < 0.65:
                self._draw_animated_block_3d(
                    state=state,
                    prev_state=prev_state,
                    anim_progress=anim_progress,
                    anim_time=anim_time,
                    is_lost=is_lost,
                    is_won=is_won,
                    proj=proj,
                    cx_g=cx_g,
                    cy_g=cy_g,
                    yaw_rad=yaw_rad,
                    pitch_rad=pitch_rad,
                    scale=scale,
                )

            # Then draw all platform tiles ON TOP of the falling block
            tiles_to_draw = []
            for r in range(board.rows):
                for c in range(board.cols):
                    tile = board.get_base_tile(r, c)
                    if tile == TileType.VOID:
                        continue
                    d_key = self._depth_of(c + 0.5, r + 0.5, 0.0, cx_g, cy_g, yaw_rad, pitch_rad)
                    tiles_to_draw.append((d_key, r, c, tile))
            tiles_to_draw.sort(key=lambda item: item[0])

            for _, r, c, tile in tiles_to_draw:
                is_explored = explored_cells is not None and (r, c) in explored_cells
                self._draw_tile_3d(
                    r=r,
                    c=c,
                    tile=tile,
                    board=board,
                    bridge_dict=bridge_dict,
                    slab_dz=slab_dz,
                    proj=proj,
                    yaw_rad=yaw_rad,
                    scale=scale,
                    anim_time=anim_time,
                    is_explored=is_explored,
                )
                if (r, c) in board.switches:
                    self._draw_switch_3d(r, c, board.switches[(r, c)], proj, scale, anim_time)

        else:
            # NORMAL PLAY: Draw all board tiles first
            tiles_to_draw = []
            for r in range(board.rows):
                for c in range(board.cols):
                    tile = board.get_base_tile(r, c)
                    if tile == TileType.VOID:
                        continue
                    d_key = self._depth_of(c + 0.5, r + 0.5, 0.0, cx_g, cy_g, yaw_rad, pitch_rad)
                    tiles_to_draw.append((d_key, r, c, tile))
            tiles_to_draw.sort(key=lambda item: item[0])

            for _, r, c, tile in tiles_to_draw:
                is_explored = explored_cells is not None and (r, c) in explored_cells
                self._draw_tile_3d(
                    r=r,
                    c=c,
                    tile=tile,
                    board=board,
                    bridge_dict=bridge_dict,
                    slab_dz=slab_dz,
                    proj=proj,
                    yaw_rad=yaw_rad,
                    scale=scale,
                    anim_time=anim_time,
                    is_explored=is_explored,
                )
                if (r, c) in board.switches:
                    self._draw_switch_3d(r, c, board.switches[(r, c)], proj, scale, anim_time)

            # Pass 3: Replay Path
            if replay_states and len(replay_states) > 1:
                self._draw_path_3d(replay_states, replay_idx, proj, anim_time)

            # Pass 4: Block is drawn safely ON TOP of all tiles while playing
            if state is not None:
                self._draw_animated_block_3d(
                    state=state,
                    prev_state=prev_state,
                    anim_progress=anim_progress,
                    anim_time=anim_time,
                    is_lost=is_lost,
                    is_won=is_won,
                    proj=proj,
                    cx_g=cx_g,
                    cy_g=cy_g,
                    yaw_rad=yaw_rad,
                    pitch_rad=pitch_rad,
                    scale=scale,
                )



    def _draw_3d_box_faces(
        self,
        gx0: float,
        gy0: float,
        gx1: float,
        gy1: float,
        gz0: float,
        gz1: float,
        top_color: Tuple[int, int, int],
        side_color_a: Tuple[int, int, int],
        side_color_b: Tuple[int, int, int],
        border_color: Tuple[int, int, int],
        proj,
        yaw_rad: float,
        border_width: int = 2,
    ) -> List[Tuple[int, int]]:
        """
        Draws a 3D axis-aligned box [gx0..gx1] x [gy0..gy1] x [gz0..gz1] in 3D space,
        automatically culling back-faces and rendering the 2 camera-facing vertical walls
        followed by the top face. Returns the projected 4 corners of the top face.
        """
        sin_y = math.sin(yaw_rad)
        cos_y = math.cos(yaw_rad)

        t00 = proj(gx0, gy0, gz1)
        t10 = proj(gx1, gy0, gz1)
        t11 = proj(gx1, gy1, gz1)
        t01 = proj(gx0, gy1, gz1)

        b00 = proj(gx0, gy0, gz0)
        b10 = proj(gx1, gy0, gz0)
        b11 = proj(gx1, gy1, gz0)
        b01 = proj(gx0, gy1, gz0)

        if sin_y >= 0:
            east_quad = [t10, t11, b11, b10]
            pygame.draw.polygon(self.surface, side_color_b, east_quad)
            pygame.draw.polygon(self.surface, border_color, east_quad, width=border_width)
        else:
            west_quad = [t01, t00, b00, b01]
            pygame.draw.polygon(self.surface, side_color_b, west_quad)
            pygame.draw.polygon(self.surface, border_color, west_quad, width=border_width)

        if cos_y >= 0:
            south_quad = [t01, t11, b11, b01]
            pygame.draw.polygon(self.surface, side_color_a, south_quad)
            pygame.draw.polygon(self.surface, border_color, south_quad, width=border_width)
        else:
            north_quad = [t10, t00, b00, b10]
            pygame.draw.polygon(self.surface, side_color_a, north_quad)
            pygame.draw.polygon(self.surface, border_color, north_quad, width=border_width)

        top_quad = [t00, t10, t11, t01]
        pygame.draw.polygon(self.surface, top_color, top_quad)
        pygame.draw.polygon(self.surface, border_color, top_quad, width=border_width)
        return top_quad

    def _draw_tile_3d(
        self,
        r: int,
        c: int,
        tile: TileType,
        board: Board,
        bridge_dict: dict,
        slab_dz: float,
        proj,
        yaw_rad: float,
        scale: float,
        anim_time: float,
        is_explored: bool = False,
    ):
        """Renders a single board tile in 3D space with procedural surface textures."""
        pad = 0.04
        gx0, gy0 = c + pad, r + pad
        gx1, gy1 = c + 1.0 - pad, r + 1.0 - pad

        if tile == TileType.FLOOR:
            top_col = COLOR_FLOOR if (r + c) % 2 == 0 else COLOR_FLOOR_SHADE
            side_a = COLOR_FLOOR_SIDE if (r + c) % 2 == 0 else COLOR_FLOOR_SIDE_DARK
            side_b = _clamp_color(side_a, -16)
            self._draw_3d_box_faces(
                gx0, gy0, gx1, gy1, -slab_dz, 0.0,
                top_col, side_a, side_b, COLOR_FLOOR_BORDER, proj, yaw_rad, border_width=1,
            )
            in_quad = [
                proj(c + 0.16, r + 0.16, 0.0),
                proj(c + 0.84, r + 0.16, 0.0),
                proj(c + 0.84, r + 0.84, 0.0),
                proj(c + 0.16, r + 0.84, 0.0),
            ]
            pygame.draw.polygon(self.surface, (242, 235, 224), in_quad, width=1)
            shine_pt = proj(c + 0.22, r + 0.22, 0.0)
            pygame.draw.circle(self.surface, (255, 255, 255), shine_pt, max(1, int(scale * 0.05)))
            if is_explored:
                exp_pt = proj(c + 0.78, r + 0.22, 0.0)
                pygame.draw.circle(self.surface, (135, 195, 255), exp_pt, max(2, int(scale * 0.07)))

        elif tile == TileType.FRAGILE:
            side_a = COLOR_FRAGILE_SIDE
            side_b = _clamp_color(side_a, -20)
            self._draw_3d_box_faces(
                gx0, gy0, gx1, gy1, -slab_dz, 0.0,
                COLOR_FRAGILE, side_a, side_b, COLOR_FRAGILE_BORDER, proj, yaw_rad, border_width=2,
            )
            p1 = proj(c + 0.16, r + 0.16, 0.0)
            p2 = proj(c + 0.84, r + 0.84, 0.0)
            p3 = proj(c + 0.84, r + 0.16, 0.0)
            p4 = proj(c + 0.16, r + 0.84, 0.0)
            pygame.draw.line(self.surface, COLOR_FRAGILE_STRIPE, p1, p2, 2)
            pygame.draw.line(self.surface, COLOR_FRAGILE_STRIPE, p3, p4, 2)

        elif tile == TileType.GOAL:
            self._draw_3d_box_faces(
                gx0, gy0, gx1, gy1, -slab_dz, 0.0,
                COLOR_GOAL_GLOW, (198, 148, 38), (168, 120, 24), COLOR_GOAL_BORDER, proj, yaw_rad, border_width=2,
            )
            pit_quad = [
                proj(c + 0.15, r + 0.15, 0.0),
                proj(c + 0.85, r + 0.15, 0.0),
                proj(c + 0.85, r + 0.85, 0.0),
                proj(c + 0.15, r + 0.85, 0.0),
            ]
            pygame.draw.polygon(self.surface, COLOR_GOAL, pit_quad)
            cx_p, cy_p = proj(c + 0.5, r + 0.5, -0.04)
            pulse = 1.0 + 0.18 * math.sin(anim_time * 4.5)
            star_r = max(4, int(scale * 0.22 * pulse))
            rot = anim_time * 1.4
            star_pts = []
            for k in range(8):
                ang = rot + k * (math.pi / 4.0)
                rad_k = star_r if k % 2 == 0 else star_r * 0.38
                star_pts.append((int(cx_p + rad_k * math.cos(ang)), int(cy_p + rad_k * math.sin(ang))))
            pygame.draw.polygon(self.surface, COLOR_GOAL_GLOW, star_pts)

        elif tile == TileType.BRIDGE:
            b_id = board.cell_to_bridge.get((r, c))
            is_open = bridge_dict.get(b_id, False) if b_id else False
            if is_open:
                side_a = COLOR_BRIDGE_OPEN_SIDE
                side_b = _clamp_color(side_a, -18)
                self._draw_3d_box_faces(
                    gx0, gy0, gx1, gy1, -slab_dz * 0.75, 0.0,
                    COLOR_BRIDGE_OPEN, side_a, side_b, COLOR_BRIDGE_OPEN_BORDER, proj, yaw_rad, border_width=2,
                )
                for p_i in (0.28, 0.50, 0.72):
                    la = proj(c + 0.14, r + p_i, 0.0)
                    lb = proj(c + 0.86, r + p_i, 0.0)
                    pygame.draw.line(self.surface, COLOR_BRIDGE_OPEN_PLANK, la, lb, 2)
            else:
                ghost_quad = [
                    proj(c + 0.12, r + 0.12, 0.0),
                    proj(c + 0.88, r + 0.12, 0.0),
                    proj(c + 0.88, r + 0.88, 0.0),
                    proj(c + 0.12, r + 0.88, 0.0),
                ]
                pygame.draw.polygon(self.surface, COLOR_BRIDGE_CLOSED, ghost_quad)
                pygame.draw.polygon(self.surface, COLOR_BRIDGE_CLOSED_BORDER, ghost_quad, width=1)

    def _draw_switch_3d(self, r: int, c: int, switch: Switch, proj, scale: float, anim_time: float):
        """Draws a raised 3D tactile switch pad with a gentle animated glow pulse."""
        cx, cy = proj(c + 0.5, r + 0.5, 0.04)
        pulse = 1.0 + 0.08 * math.sin(anim_time * 4.0 + r + c)

        if switch.type == SwitchType.SOFT:
            outer_r = max(5, int(scale * 0.28 * pulse))
            inner_r = max(3, int(scale * 0.20))
            pygame.draw.circle(self.surface, (195, 165, 95), (cx, cy + 2), outer_r)
            pygame.draw.circle(self.surface, COLOR_SWITCH_SOFT_RIM, (cx, cy), outer_r)
            pygame.draw.circle(self.surface, COLOR_SWITCH_SOFT, (cx, cy - 1), inner_r)
            pygame.draw.circle(self.surface, (255, 250, 215), (cx - 2, cy - 3), max(1, inner_r // 3))

        elif switch.type == SwitchType.HEAVY:
            arm = max(4, int(scale * 0.20 * pulse))
            w = max(2, int(scale * 0.09))
            pygame.draw.circle(self.surface, (255, 228, 236), (cx, cy), arm + 4)
            pygame.draw.circle(self.surface, COLOR_SWITCH_HEAVY_RIM, (cx, cy), arm + 4, width=2)
            pygame.draw.line(self.surface, COLOR_SWITCH_HEAVY, (cx - arm, cy - arm), (cx + arm, cy + arm), w)
            pygame.draw.line(self.surface, COLOR_SWITCH_HEAVY, (cx - arm, cy + arm), (cx + arm, cy - arm), w)

        elif switch.type == SwitchType.SPLIT:
            arm = max(4, int(scale * 0.20 * pulse))
            pygame.draw.circle(self.surface, (232, 255, 242), (cx, cy), arm + 4)
            pygame.draw.circle(self.surface, COLOR_SWITCH_SPLIT_RIM, (cx, cy), arm + 4, width=2)
            pygame.draw.circle(self.surface, COLOR_SWITCH_SPLIT, (cx, cy), max(2, arm // 3))

    def _draw_path_3d(self, replay_states: List[GameState], replay_idx: int, proj, anim_time: float):
        """Draws 3D stepping-stone nodes and animated flowing energy beads along the solved path."""
        waypoints: List[Tuple[float, float, str]] = []
        for i, st in enumerate(replay_states):
            b = st.block
            if not b.is_split:
                cells = b.occupied_cells()
                avg_r = sum(cell[0] for cell in cells) / len(cells)
                avg_c = sum(cell[1] for cell in cells) / len(cells)
                waypoints.append((avg_c + 0.5, avg_r + 0.5, "STD"))
            else:
                chosen = b.cube1 if b.active_cube == 0 else b.cube2
                tag = "C1" if b.active_cube == 0 else "C2"
                if i > 0 and replay_states[i - 1].block.is_split:
                    prev_b = replay_states[i - 1].block
                    if b.cube1 != prev_b.cube1:
                        chosen, tag = b.cube1, "C1"
                    elif b.cube2 != prev_b.cube2:
                        chosen, tag = b.cube2, "C2"
                waypoints.append((chosen[1] + 0.5, chosen[0] + 0.5, tag))

        pulse_phase = (anim_time * 2.5) % 1.0
        for i in range(len(waypoints) - 1):
            gx1, gy1, _ = waypoints[i]
            gx2, gy2, _ = waypoints[i + 1]
            dist = math.hypot(gx2 - gx1, gy2 - gy1)
            if dist < 0.05 or dist > 2.35:
                continue
            p1 = proj(gx1, gy1, 0.03)
            p2 = proj(gx2, gy2, 0.03)
            is_past = i < replay_idx
            col = COLOR_VIS_PATH if is_past else (225, 185, 210)
            pygame.draw.line(self.surface, col, p1, p2, 3 if is_past else 2)

            bx = _lerp(p1[0], p2[0], pulse_phase)
            by = _lerp(p1[1], p2[1], pulse_phase)
            pygame.draw.circle(self.surface, (255, 240, 130), (int(bx), int(by)), 3)

    @staticmethod
    def _block_box_3d(block: Block) -> List[Tuple[float, float, float, float, float, Tuple[int, int, int], bool, Optional[str]]]:
        """Returns a list of 3D prism descriptors for the block."""
        if block.is_split:
            r1, c1 = block.cube1
            r2, c2 = block.cube2
            return [
                (float(c1), float(r1), float(c1 + 1), float(r1 + 1), 0.85, COLOR_SPLIT_CUBE_1, block.active_cube == 0, "#1"),
                (float(c2), float(r2), float(c2 + 1), float(r2 + 1), 0.85, COLOR_SPLIT_CUBE_2, block.active_cube == 1, "#2"),
            ]
        if block.orientation == Orientation.STANDING:
            return [(float(block.c), float(block.r), float(block.c + 1), float(block.r + 1), 1.65, COLOR_BLOCK_TOP, False, None)]
        elif block.orientation == Orientation.LYING_H:
            return [(float(block.c), float(block.r), float(block.c + 2), float(block.r + 1), 0.85, COLOR_BLOCK_TOP, False, None)]
        else:
            return [(float(block.c), float(block.r), float(block.c + 1), float(block.r + 2), 0.85, COLOR_BLOCK_TOP, False, None)]

    def _draw_animated_block_3d(
        self,
        state: GameState,
        prev_state: Optional[GameState],
        anim_progress: float,
        anim_time: float,
        is_lost: bool,
        is_won: bool,
        proj,
        cx_g: float,
        cy_g: float,
        yaw_rad: float,
        pitch_rad: float,
        scale: float,
    ):
        """
        Renders the 3D toy block with smooth interpolation between `prev_state` and `state`,
        parabolic roll hop, squash-and-stretch landing bounce, and cute blinking kawaii eyes.
        """
        curr_boxes = self._block_box_3d(state.block)
        prev_boxes = self._block_box_3d(prev_state.block) if (prev_state is not None and anim_progress < 0.999) else curr_boxes

        t = max(0.0, min(1.0, anim_progress))
        t_smooth = _ease_out_Back(t) if t < 1.0 else 1.0

        hop_z = math.sin(math.pi * t) * 0.45 if t < 1.0 else 0.0
        if prev_state is not None and (not prev_state.block.is_split) and state.block.is_split and t < 1.0:
            hop_z = math.sin(math.pi * t) * 1.45

        idle_breath = 0.025 * math.sin(anim_time * 3.6) if t >= 1.0 else 0.0
        sink_z = -0.35 * math.sin(min(1.0, (anim_time % 2.0)) * math.pi * 0.5) if is_won else 0.0

        # ── Dramatic Death Animation: Tumbling, spinning off the edge into abyss ──
        death_phase = max(0.0, min(1.0, getattr(self, "_death_anim_t_cache", 0.0)))
        tumble_rot = 0.0
        if is_lost:
            # Gravity acceleration: begins slow, then plunges deep
            fall_z = -(death_phase ** 2.2) * 8.5
            # Rapid tumbling rotation and drift as it falls off into space
            tumble_rot = death_phase * 6.5
            drift_x = math.sin(tumble_rot) * 0.45 * death_phase
            drift_y = math.cos(tumble_rot) * 0.30 * death_phase
        else:
            fall_z = 0.0
            drift_x = 0.0
            drift_y = 0.0

        interp_boxes = []
        for idx, c_box in enumerate(curr_boxes):
            p_box = prev_boxes[min(idx, len(prev_boxes) - 1)]
            gx0 = _lerp(p_box[0], c_box[0], t_smooth) + drift_x
            gy0 = _lerp(p_box[1], c_box[1], t_smooth) + drift_y
            gx1 = _lerp(p_box[2], c_box[2], t_smooth) + drift_x
            gy1 = _lerp(p_box[3], c_box[3], t_smooth) + drift_y
            gz_h = _lerp(p_box[4], c_box[4], t_smooth) + idle_breath
            depth = self._depth_of((gx0 + gx1) * 0.5, (gy0 + gy1) * 0.5, gz_h, cx_g, cy_g, yaw_rad, pitch_rad)
            interp_boxes.append((depth, gx0, gy0, gx1, gy1, gz_h, c_box[5], c_box[6], c_box[7]))

        interp_boxes.sort(key=lambda item: item[0])

        for _, gx0, gy0, gx1, gy1, gz_h, top_col, is_active_split, label in interp_boxes:
            # Plumper, softer block geometry
            pad = 0.04
            bx0, by0 = gx0 + pad, gy0 + pad
            bx1, by1 = gx1 - pad, gy1 - pad
            z_base = max(0.0, hop_z) + sink_z + fall_z
            z_top = z_base + gz_h

            # Shadow fades out quickly as block falls into the abyss
            if death_phase < 0.6:
                sh_alpha = int(175 * max(0.0, 1.0 - death_phase * 1.8))
                sh_col = (175, 160, 190)
                sh_quad = [
                    proj(bx0 + 0.05, by0 + 0.05, 0.01),
                    proj(bx1 + 0.05, by0 + 0.05, 0.01),
                    proj(bx1 + 0.05, by1 + 0.05, 0.01),
                    proj(bx0 + 0.05, by1 + 0.05, 0.01),
                ]
                pygame.draw.polygon(self.surface, sh_col, sh_quad)

            # Death tint: cute alarmed strawberry / purple fade as it falls into shadow
            if is_lost and death_phase > 0:
                shadow_fade = max(0.2, 1.0 - death_phase * 0.8)
                top_col = (
                    int(top_col[0] * shadow_fade),
                    int(top_col[1] * shadow_fade),
                    int(top_col[2] * shadow_fade),
                )

            side_a = _clamp_color(top_col, -24)
            side_b = _clamp_color(top_col, -44)
            top_quad = self._draw_3d_box_faces(
                bx0, by0, bx1, by1, z_base, z_top,
                top_col, side_a, side_b, COLOR_BLOCK_BORDER, proj, yaw_rad, border_width=2,
            )

            # Glossy curved highlight
            in_pad = 0.12
            shine_quad = [
                proj(bx0 + in_pad, by0 + in_pad, z_top),
                proj(bx1 - in_pad, by0 + in_pad, z_top),
                proj(bx1 - in_pad, by1 - in_pad, z_top),
                proj(bx0 + in_pad, by1 - in_pad, z_top),
            ]
            pygame.draw.polygon(self.surface, _clamp_color(top_col, 36), shine_quad, width=2)

            # Secondary concentric bevel ring makes the top face look rounded & cushioned
            in_pad2 = 0.24
            bevel_quad = [
                proj(bx0 + in_pad2, by0 + in_pad2, z_top),
                proj(bx1 - in_pad2, by0 + in_pad2, z_top),
                proj(bx1 - in_pad2, by1 - in_pad2, z_top),
                proj(bx0 + in_pad2, by1 - in_pad2, z_top),
            ]
            pygame.draw.polygon(self.surface, _clamp_color(top_col, 18), bevel_quad, width=1)

            if is_active_split:
                pygame.draw.polygon(self.surface, COLOR_ACTIVE_HIGHLIGHT, top_quad, width=3)
                bob = 0.12 * math.sin(anim_time * 6.0)
                px, py = proj((bx0 + bx1) * 0.5, (by0 + by1) * 0.5, z_top + 0.35 + bob)
                tri = [(px, py), (px - 7, py - 11), (px + 7, py - 11)]
                pygame.draw.polygon(self.surface, COLOR_ACTIVE_HIGHLIGHT, tri)
                pygame.draw.polygon(self.surface, COLOR_BLOCK_BORDER, tri, width=1)

            fcx, fcy = proj((bx0 + bx1) * 0.5, (by0 + by1) * 0.5, z_top)
            eye_sep = max(5, int(scale * 0.18))
            eye_r = max(2, int(scale * 0.06))
            eye_col = (58, 32, 48)

            # When falling, cute panicked / dizzy X_X or >_< eyes!
            if is_lost:
                # Alarmed dizzy eyes (X_X)
                ex_arm = max(3, int(scale * 0.06))
                for ex_c in (fcx - eye_sep, fcx + eye_sep):
                    pygame.draw.line(self.surface, eye_col, (ex_c - ex_arm, fcy - 2 - ex_arm), (ex_c + ex_arm, fcy - 2 + ex_arm), 2)
                    pygame.draw.line(self.surface, eye_col, (ex_c - ex_arm, fcy - 2 + ex_arm), (ex_c + ex_arm, fcy - 2 - ex_arm), 2)
                # O-shaped open shocked mouth
                pygame.draw.circle(self.surface, eye_col, (fcx, fcy + 4), max(2, int(scale * 0.05)))
                pygame.draw.circle(self.surface, (255, 120, 140), (fcx, fcy + 4), max(1, int(scale * 0.03)))
            else:
                blush_col = (255, 90, 125)
                pygame.draw.circle(self.surface, blush_col, (fcx - eye_sep - 3, fcy + 3), eye_r + 1)
                pygame.draw.circle(self.surface, blush_col, (fcx + eye_sep + 3, fcy + 3), eye_r + 1)

                is_blinking = (anim_time % 3.4) > 3.22
                if is_blinking:
                    pygame.draw.line(self.surface, eye_col, (fcx - eye_sep - 3, fcy - 1), (fcx - eye_sep + 3, fcy - 1), 2)
                    pygame.draw.line(self.surface, eye_col, (fcx + eye_sep - 3, fcy - 1), (fcx + eye_sep + 3, fcy - 1), 2)
                else:
                    pygame.draw.circle(self.surface, eye_col, (fcx - eye_sep, fcy - 1), eye_r)
                    pygame.draw.circle(self.surface, eye_col, (fcx + eye_sep, fcy - 1), eye_r)
                    pygame.draw.circle(self.surface, (255, 255, 255), (fcx - eye_sep - 1, fcy - 2), max(1, eye_r // 2))
                    pygame.draw.circle(self.surface, (255, 255, 255), (fcx + eye_sep - 1, fcy - 2), max(1, eye_r // 2))

                smile_rect = pygame.Rect(fcx - 4, fcy + 1, 8, 5)
                pygame.draw.arc(self.surface, eye_col, smile_rect, math.pi, 2 * math.pi, 2)

            if label:
                lbl_s = self.font_tiny.render(label, True, (255, 255, 255))
                self.surface.blit(lbl_s, (fcx - lbl_s.get_width() // 2, fcy - int(scale * 0.34)))


    # ========================================================================
    # MODE 2: 2D ALGORITHM VISUALIZATION RENDERER (WITH PAN, ZOOM & ANIMATION)
    # ========================================================================

    def _draw_board_2d(
        self,
        board: Board,
        state: GameState,
        prev_state: Optional[GameState],
        anim_progress: float,
        anim_time: float,
        bridge_dict: dict,
        cell_size: int,
        offset_x: int,
        offset_y: int,
        is_lost: bool,
        explored_cells: Optional[Dict[Tuple[int, int], int]],
        replay_states: Optional[List[GameState]],
        replay_idx: int,
    ):
        """Renders the zoomable/pannable 2D Top-Down Algorithm Visualization Mode with smooth block animation."""
        for c in range(board.cols):
            cx = offset_x + c * cell_size + cell_size // 2
            cy = offset_y - 12
            lbl = self.font_tiny.render(str(c), True, COLOR_TEXT_MUTED)
            self.surface.blit(lbl, lbl.get_rect(center=(cx, cy)))

        for r in range(board.rows):
            cx = offset_x - 14
            cy = offset_y + r * cell_size + cell_size // 2
            lbl = self.font_tiny.render(str(r), True, COLOR_TEXT_MUTED)
            self.surface.blit(lbl, lbl.get_rect(center=(cx, cy)))

        max_visit = max(explored_cells.values()) if (explored_cells and len(explored_cells) > 0) else 1
        for r in range(board.rows):
            for c in range(board.cols):
                tile = board.get_base_tile(r, c)
                x = offset_x + c * cell_size
                y = offset_y + r * cell_size
                cell_rect = pygame.Rect(x, y, cell_size, cell_size)

                if tile == TileType.VOID:
                    pygame.draw.circle(self.surface, (224, 232, 246), cell_rect.center, 2)
                    continue

                visit_step = explored_cells.get((r, c)) if explored_cells else None
                self._draw_tile_2d(cell_rect, tile, (r, c), board, bridge_dict, visit_step, max_visit)

                if (r, c) in board.switches:
                    self._draw_switch_2d(cell_rect, board.switches[(r, c)], anim_time)

        self._draw_switch_links_2d(board, cell_size, offset_x, offset_y)

        sr, sc = board.start_pos
        s_rect = pygame.Rect(offset_x + sc * cell_size + 4, offset_y + sr * cell_size + 4, 16, 14)
        pygame.draw.rect(self.surface, COLOR_VIS_START, s_rect, border_radius=4)
        s_lbl = self.font_tiny.render("S", True, (25, 85, 45))
        self.surface.blit(s_lbl, s_lbl.get_rect(center=s_rect.center))

        if replay_states and len(replay_states) > 1:
            self._draw_solution_trajectory_2d(replay_states, replay_idx, cell_size, offset_x, offset_y, anim_time)

        if state is not None and not is_lost:
            self._draw_animated_block_2d(state, prev_state, anim_progress, cell_size, offset_x, offset_y)

    def _draw_switch_2d(self, rect: pygame.Rect, switch: Switch, anim_time: float):
        """Draws a crisp 2D switch icon with subtle pulse."""
        cx, cy = rect.center
        size = rect.width
        pulse = 1.0 + 0.06 * math.sin(anim_time * 4.0)
        if switch.type == SwitchType.SOFT:
            outer_r = max(5, int(size * 0.30 * pulse))
            inner_r = max(3, int(size * 0.21))
            pygame.draw.circle(self.surface, COLOR_SWITCH_SOFT_RIM, (cx, cy), outer_r)
            pygame.draw.circle(self.surface, COLOR_SWITCH_SOFT, (cx, cy), inner_r)
        elif switch.type == SwitchType.HEAVY:
            pad_r = max(10, int(size * 0.58))
            plate_rect = pygame.Rect(cx - pad_r // 2, cy - pad_r // 2, pad_r, pad_r)
            pygame.draw.rect(self.surface, (255, 228, 235), plate_rect, border_radius=12)
            pygame.draw.rect(self.surface, COLOR_SWITCH_HEAVY_RIM, plate_rect, width=2, border_radius=12)
            arm = max(3, int(size * 0.17))
            w = max(2, size // 11)
            pygame.draw.line(self.surface, COLOR_SWITCH_HEAVY, (cx - arm, cy - arm), (cx + arm, cy + arm), w)
            pygame.draw.line(self.surface, COLOR_SWITCH_HEAVY, (cx - arm, cy + arm), (cx + arm, cy - arm), w)
        elif switch.type == SwitchType.SPLIT:
            pad_r = max(10, int(size * 0.60))
            plate_rect = pygame.Rect(cx - pad_r // 2, cy - pad_r // 2, pad_r, pad_r)
            pygame.draw.rect(self.surface, (232, 255, 242), plate_rect, border_radius=12)
            pygame.draw.rect(self.surface, COLOR_SWITCH_SPLIT_RIM, plate_rect, width=2, border_radius=12)
            pygame.draw.circle(self.surface, COLOR_SWITCH_SPLIT, (cx, cy), max(2, size // 10))

    def _draw_tile_2d(
        self,
        rect: pygame.Rect,
        tile: TileType,
        pos: Tuple[int, int],
        board: Board,
        bridge_dict: dict,
        visit_step: Optional[int],
        max_visit: int,
    ):
        """Draws a cute, distinctly rounded top-down 2D cell with soft borders."""
        r, c = pos
        inner = rect.inflate(-4, -4)
        rad = max(8, inner.width // 4)  # Generously rounded, smooth pebble/cushion tiles

        if tile == TileType.FLOOR:
            fill = COLOR_FLOOR if (r + c) % 2 == 0 else COLOR_FLOOR_SHADE
            border = COLOR_FLOOR_BORDER
            if visit_step is not None:
                ratio = min(1.0, visit_step / max(1, max_visit))
                fill = (
                    int(196 + 34 * ratio),
                    int(236 - 24 * ratio),
                    255,
                )
                border = COLOR_VIS_EXPLORED_BORDER
            pygame.draw.rect(self.surface, fill, inner, border_radius=rad)
            pygame.draw.rect(self.surface, border, inner, width=2, border_radius=rad)

        elif tile == TileType.FRAGILE:
            pygame.draw.rect(self.surface, COLOR_FRAGILE, inner, border_radius=rad)
            pygame.draw.line(self.surface, COLOR_FRAGILE_STRIPE, inner.topleft, inner.bottomright, 2)
            pygame.draw.line(self.surface, COLOR_FRAGILE_STRIPE, inner.bottomleft, inner.topright, 2)
            pygame.draw.rect(self.surface, COLOR_FRAGILE_BORDER, inner, width=2, border_radius=rad)

        elif tile == TileType.GOAL:
            pygame.draw.rect(self.surface, COLOR_GOAL, inner, border_radius=rad)
            pygame.draw.rect(self.surface, COLOR_GOAL_BORDER, inner, width=3, border_radius=rad)
            cx, cy = inner.center
            pygame.draw.circle(self.surface, COLOR_GOAL_GLOW, (cx, cy), max(4, inner.width // 4))
            g_lbl = self.font_tiny.render("G", True, COLOR_GOAL)
            self.surface.blit(g_lbl, g_lbl.get_rect(center=(cx, cy)))

        elif tile == TileType.BRIDGE:
            b_id = board.cell_to_bridge.get(pos)
            is_open = bridge_dict.get(b_id, False) if b_id else False
            if is_open:
                pygame.draw.rect(self.surface, COLOR_BRIDGE_OPEN, inner, border_radius=rad)
                pygame.draw.rect(self.surface, COLOR_BRIDGE_OPEN_BORDER, inner, width=2, border_radius=rad)
            else:
                pygame.draw.rect(self.surface, COLOR_BRIDGE_CLOSED, inner, border_radius=rad)
                pygame.draw.rect(self.surface, COLOR_BRIDGE_CLOSED_BORDER, inner, width=1, border_radius=rad)


        if rect.width >= 34 and tile in (TileType.FLOOR, TileType.FRAGILE, TileType.BRIDGE):
            gr, gc = board.goal_pos
            h_val = (abs(r - gr) + abs(c - gc)) / 2.0
            h_str = f"{h_val:.1f}" if h_val % 1 != 0 else f"{int(h_val)}"
            h_surf = self.font_tiny.render(h_str, True, (150, 142, 172))
            self.surface.blit(h_surf, (inner.right - h_surf.get_width() - 3, inner.bottom - h_surf.get_height() - 1))

    def _draw_switch_links_2d(self, board: Board, cell_size: int, offset_x: int, offset_y: int):
        """Draws dashed causal connection lines between switches and their linked bridges / split targets."""
        for sw_pos, sw in board.switches.items():
            sx = offset_x + sw_pos[1] * cell_size + cell_size // 2
            sy = offset_y + sw_pos[0] * cell_size + cell_size // 2

            for b_id in sw.linked_bridges:
                bridge = board.bridges.get(b_id)
                if not bridge:
                    continue
                for br, bc in bridge.cells:
                    tx = offset_x + bc * cell_size + cell_size // 2
                    ty = offset_y + br * cell_size + cell_size // 2
                    self._draw_dashed_line((sx, sy), (tx, ty), COLOR_VIS_LINK, dash_len=5, width=2)
                    pygame.draw.circle(self.surface, COLOR_VIS_LINK, (tx, ty), 4)

            if sw.split_targets:
                for tr, tc in sw.split_targets:
                    tx = offset_x + tc * cell_size + cell_size // 2
                    ty = offset_y + tr * cell_size + cell_size // 2
                    self._draw_dashed_line((sx, sy), (tx, ty), COLOR_SWITCH_SPLIT_RIM, dash_len=5, width=2)

    def _extract_step_waypoints(
        self,
        replay_states: List[GameState],
        cell_size: int,
        offset_x: int,
        offset_y: int,
    ) -> List[Tuple[int, int, str]]:
        """Computes per-step waypoints on actual board tiles (split-aware)."""
        waypoints: List[Tuple[int, int, str]] = []
        for i, st in enumerate(replay_states):
            b = st.block
            if not b.is_split:
                px, py = self._state_center_px(b, cell_size, offset_x, offset_y)
                waypoints.append((px, py, "STD"))
            else:
                chosen_cell = b.cube1 if b.active_cube == 0 else b.cube2
                tag = "C1" if b.active_cube == 0 else "C2"
                if i > 0 and replay_states[i - 1].block.is_split:
                    prev_b = replay_states[i - 1].block
                    if b.cube1 != prev_b.cube1:
                        chosen_cell = b.cube1
                        tag = "C1"
                    elif b.cube2 != prev_b.cube2:
                        chosen_cell = b.cube2
                        tag = "C2"
                px = int(offset_x + (chosen_cell[1] + 0.5) * cell_size)
                py = int(offset_y + (chosen_cell[0] + 0.5) * cell_size)
                waypoints.append((px, py, tag))
        return waypoints

    def _draw_solution_trajectory_2d(
        self,
        replay_states: List[GameState],
        replay_idx: int,
        cell_size: int,
        offset_x: int,
        offset_y: int,
        anim_time: float,
    ):
        """Draws the full algorithm path with directional arrows, flowing pulses, and step badges."""
        waypoints = self._extract_step_waypoints(replay_states, cell_size, offset_x, offset_y)
        max_step_dist = cell_size * 2.35

        if replay_idx + 1 < len(replay_states):
            next_block = replay_states[replay_idx + 1].block
            for gr, gc in next_block.occupied_cells():
                g_rect = pygame.Rect(
                    offset_x + gc * cell_size + 4,
                    offset_y + gr * cell_size + 4,
                    cell_size - 8,
                    cell_size - 8,
                )
                g_surf = pygame.Surface((max(1, g_rect.width), max(1, g_rect.height)), pygame.SRCALPHA)
                pygame.draw.rect(g_surf, (255, 112, 150, 75), g_surf.get_rect(), border_radius=8)
                self.surface.blit(g_surf, g_rect.topleft)
                pygame.draw.rect(self.surface, COLOR_VIS_PATH, g_rect, width=2, border_radius=8)

        pulse_phase = (anim_time * 2.5) % 1.0
        for i in range(len(waypoints) - 1):
            x1, y1, _ = waypoints[i]
            x2, y2, tag2 = waypoints[i + 1]
            dist = math.hypot(x2 - x1, y2 - y1)
            if dist < 2 or dist > max_step_dist:
                continue

            is_past = i < replay_idx
            if tag2 == "C1":
                col = COLOR_SPLIT_CUBE_1 if is_past else (242, 196, 176)
            elif tag2 == "C2":
                col = COLOR_SPLIT_CUBE_2 if is_past else (182, 212, 245)
            else:
                col = COLOR_VIS_PATH if is_past else (238, 175, 198)

            width = 4 if is_past else 2
            pygame.draw.line(self.surface, col, (x1, y1), (x2, y2), width)

            mx = _lerp(x1, x2, 0.5)
            my = _lerp(y1, y2, 0.5)
            ang = math.atan2(y2 - y1, x2 - x1)
            arr_len = 7
            left_pt = (int(mx - arr_len * math.cos(ang - 0.55)), int(my - arr_len * math.sin(ang - 0.55)))
            right_pt = (int(mx - arr_len * math.cos(ang + 0.55)), int(my - arr_len * math.sin(ang + 0.55)))
            pygame.draw.polygon(self.surface, col, [(int(mx), int(my)), left_pt, right_pt])

            px_flow = int(_lerp(x1, x2, pulse_phase))
            py_flow = int(_lerp(y1, y2, pulse_phase))
            pygame.draw.circle(self.surface, (255, 235, 110), (px_flow, py_flow), 3)

        badge_by_pos: Dict[Tuple[int, int], Tuple[int, str]] = {}
        for i, (px, py, tag) in enumerate(waypoints):
            if i == 0:
                continue
            if (px, py) not in badge_by_pos or i <= replay_idx:
                badge_by_pos[(px, py)] = (i, tag)

        for (px, py), (step_num, tag) in badge_by_pos.items():
            is_visited_step = step_num <= replay_idx
            bg = COLOR_VIS_PATH_NODE if is_visited_step else (246, 238, 250)
            if tag == "C1":
                border = COLOR_SPLIT_CUBE_1_SIDE if is_visited_step else (225, 180, 160)
            elif tag == "C2":
                border = COLOR_SPLIT_CUBE_2_SIDE if is_visited_step else (165, 195, 230)
            else:
                border = COLOR_VIS_PATH if is_visited_step else (195, 175, 210)
            pygame.draw.circle(self.surface, bg, (px, py), 8)
            pygame.draw.circle(self.surface, border, (px, py), 8, width=2)
            num_surf = self.font_tiny.render(str(step_num), True, COLOR_TEXT)
            self.surface.blit(num_surf, num_surf.get_rect(center=(px, py)))

    def _draw_animated_block_2d(
        self,
        state: GameState,
        prev_state: Optional[GameState],
        anim_progress: float,
        cell_size: int,
        offset_x: int,
        offset_y: int,
    ):
        """Draws the smoothly interpolated 2D footprint of the block."""
        pad = 4
        t = _ease_out_Back(anim_progress) if anim_progress < 1.0 else 1.0
        block = state.block
        p_block = prev_state.block if (prev_state is not None and anim_progress < 0.999) else block

        if block.is_split:
            p_c1 = p_block.cube1 if p_block.is_split else (p_block.r, p_block.c)
            p_c2 = p_block.cube2 if p_block.is_split else (p_block.r, p_block.c)
            cubes = [
                (p_c1, block.cube1, COLOR_SPLIT_CUBE_1, 0),
                (p_c2, block.cube2, COLOR_SPLIT_CUBE_2, 1),
            ]
            for (pr, pc), (cr, cc), col, c_idx in cubes:
                ir = _lerp(pr, cr, t)
                ic = _lerp(pc, cc, t)
                rect = pygame.Rect(
                    int(offset_x + ic * cell_size + pad),
                    int(offset_y + ir * cell_size + pad),
                    cell_size - 2 * pad,
                    cell_size - 2 * pad,
                )
                cube_rad = max(8, rect.width // 3)
                draw_soft_shadow(self.surface, rect, radius=cube_rad, offset=(0, 3), alpha=45, spread=1)
                pygame.draw.rect(self.surface, col, rect, border_radius=cube_rad)
                # Inner highlight ring for rounder feel
                pygame.draw.rect(self.surface, _clamp_color(col, 35), rect.inflate(-6, -6), width=2, border_radius=max(4, cube_rad - 3))
                is_active = block.active_cube == c_idx
                border_c = COLOR_ACTIVE_HIGHLIGHT if is_active else COLOR_BLOCK_BORDER
                pygame.draw.rect(self.surface, border_c, rect, width=3 if is_active else 2, border_radius=cube_rad)
                lbl = self.font_badge.render(f"C{c_idx + 1}", True, (255, 255, 255))
                self.surface.blit(lbl, lbl.get_rect(center=rect.center))
        else:
            ir = _lerp(p_block.r, block.r, t)
            ic = _lerp(p_block.c, block.c, t)
            pw = 2.0 if p_block.orientation == Orientation.LYING_H else 1.0
            ph = 2.0 if p_block.orientation == Orientation.LYING_V else 1.0
            cw = 2.0 if block.orientation == Orientation.LYING_H else 1.0
            ch = 2.0 if block.orientation == Orientation.LYING_V else 1.0
            iw = _lerp(pw, cw, t)
            ih = _lerp(ph, ch, t)

            if block.orientation == Orientation.STANDING:
                badge_txt = "1x1"
            elif block.orientation == Orientation.LYING_H:
                badge_txt = "1x2 H"
            else:
                badge_txt = "2x1 V"

            footprint = pygame.Rect(
                int(offset_x + ic * cell_size + pad),
                int(offset_y + ir * cell_size + pad),
                int(iw * cell_size - 2 * pad),
                int(ih * cell_size - 2 * pad),
            )
            block_rad = max(10, min(footprint.width, footprint.height) // 3)
            draw_soft_shadow(self.surface, footprint, radius=block_rad, offset=(0, 3), alpha=50, spread=2)
            pygame.draw.rect(self.surface, COLOR_BLOCK_TOP, footprint, border_radius=block_rad)
            # Inner bevel highlight for extra soft round appearance
            pygame.draw.rect(self.surface, COLOR_BLOCK_SHINE, footprint.inflate(-6, -6), width=2, border_radius=max(6, block_rad - 3))
            pygame.draw.rect(self.surface, _clamp_color(COLOR_BLOCK_TOP, 28), footprint.inflate(-12, -12), width=1, border_radius=max(4, block_rad - 6))
            pygame.draw.rect(self.surface, COLOR_BLOCK_BORDER, footprint, width=2, border_radius=block_rad)

            lbl = self.font_small.render(badge_txt, True, (255, 255, 255))
            self.surface.blit(lbl, lbl.get_rect(center=footprint.center))



    # ========================================================================
    # HELPERS, CONFETTI & OVERLAYS
    # ========================================================================

    def _draw_victory_confetti(self, anim_time: float):
        """Renders cute animated pastel confetti sparkles across the playmat when won."""
        colors = [
            (255, 136, 156),
            (132, 226, 212),
            (255, 218, 88),
            (176, 142, 248),
            (122, 188, 255),
        ]
        for i in range(28):
            seed = i * 37.3
            px = self.board_area.left + 60 + int((seed * 19 + anim_time * 40 * ((i % 3) - 1)) % max(100, self.board_area.width - 120))
            py = self.board_area.top + 80 + int((seed * 13 + anim_time * 75 * (1 + (i % 3) * 0.3)) % max(100, self.board_area.height - 160))
            col = colors[i % len(colors)]
            pygame.draw.circle(self.surface, col, (px, py), 4 + (i % 3))

    @staticmethod
    def _state_center_px(block: Block, cell_size: int, offset_x: int, offset_y: int) -> Tuple[int, int]:
        """Computes the pixel center of mass of a block state on the 2D grid."""
        cells = block.occupied_cells()
        avg_r = sum(c[0] for c in cells) / len(cells)
        avg_c = sum(c[1] for c in cells) / len(cells)
        px = int(offset_x + (avg_c + 0.5) * cell_size)
        py = int(offset_y + (avg_r + 0.5) * cell_size)
        return (px, py)

    def _draw_dashed_line(
        self,
        p1: Tuple[int, int],
        p2: Tuple[int, int],
        color: Tuple[int, int, int],
        dash_len: int = 6,
        width: int = 2,
    ):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        steps = max(1, int(dist // (dash_len * 2)))
        for i in range(steps):
            t1 = (i * 2 * dash_len) / dist
            t2 = min(1.0, ((i * 2 + 1) * dash_len) / dist)
            start = (int(p1[0] + dx * t1), int(p1[1] + dy * t1))
            end = (int(p1[0] + dx * t2), int(p1[1] + dy * t2))
            pygame.draw.line(self.surface, color, start, end, width)

    def _draw_death_effects(self, death_anim_t: float, anim_time: float, block_pos: Optional[Tuple[int, int]] = None):
        """
        Clean, stylized cartoon death sequence centered right on the block that fell:
          - Expanding shockwave & wind vortex trails bursting from the block's exact position.
          - Falling tear drops & star sparks tumbling down into the void with the block.
          - Subtle dramatic vignette that darkens the edges without an ugly red explosion.
        """
        from ..config import DEATH_ANIM_DURATION as _DAD
        phase = max(0.0, min(1.0, death_anim_t / max(0.001, _DAD)))

        # Use actual block screen position (not screen center!)
        if block_pos is not None:
            cx, cy = block_pos
        else:
            cx, cy = self.board_area.centerx, self.board_area.centery

        # ── 1. Soft ripple at the moment of slipping off (brief, fades by 0.35s) ──
        if death_anim_t < 0.35:
            ring_t = death_anim_t / 0.35
            ring_r = int(8 + ring_t * 45)
            ring_alpha = int(180 * (1.0 - ring_t ** 1.5))
            if ring_r > 1 and ring_alpha > 0:
                ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    ring_surf,
                    (255, 140, 160, ring_alpha),
                    (ring_r + 2, ring_r + 2),
                    ring_r,
                    width=max(1, int(3 * (1.0 - ring_t))),
                )
                self.surface.blit(ring_surf, (cx - ring_r - 2, cy - ring_r - 2))

        # ── 2. Wind trails / falling lines rushing upward around the block ─────────
        # Gives a high-speed sense of plunging downward into the abyss
        if death_anim_t < 1.0:
            wind_lines = 10
            for i in range(wind_lines):
                seed = i * 47.9 + 5.1
                x_spread = ((seed * 19.3) % 70.0) - 35.0
                wx = int(cx + x_spread)
                speed_y = 100.0 + (seed * 13.0) % 140.0
                line_len = 12 + int(phase * 35.0)
                wy = int(cy - (death_anim_t * speed_y) % max(100, self.board_area.height // 2))
                alpha_w = int(120 * max(0.0, 1.0 - death_anim_t / 1.0))
                if alpha_w > 5 and self.board_area.collidepoint((wx, wy)):
                    w_surf = pygame.Surface((2, line_len), pygame.SRCALPHA)
                    w_surf.fill((255, 230, 240, alpha_w))
                    self.surface.blit(w_surf, (wx, wy))

        # ── 3. Cute tumbling sparks / sweat drops flying off the block ────────────
        spark_colors = [
            (255, 170, 190),  # sakura
            (255, 220, 110),  # dizzy yellow star
            (140, 205, 255),  # sweat drop blue
        ]
        num_sparks = 14
        for i in range(num_sparks):
            seed = i * 83.3 + 9.1
            angle = (seed % (2 * math.pi))
            spd = 30.0 + (seed * 11.0) % 65.0
            spark_age = death_anim_t - (i % 3) * 0.05
            if spark_age < 0 or spark_age > 0.9:
                continue
            s_t = spark_age / 0.9
            px = int(cx + math.cos(angle) * spd * s_t)
            py = int(cy + math.sin(angle) * spd * s_t * 0.5 + (s_t ** 2) * 90.0)
            col = spark_colors[i % len(spark_colors)]
            spark_alpha = int(200 * max(0.0, 1.0 - s_t ** 1.3))
            if spark_alpha > 5:
                sz = max(2, int(3 * (1.0 - s_t * 0.5)))
                sp_surf = pygame.Surface((sz * 2 + 2, sz * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(sp_surf, (*col, spark_alpha), (sz + 1, sz + 1), sz)
                self.surface.blit(sp_surf, (px - sz - 1, py - sz - 1))


    def _draw_level_transition(self, transition_t: float, direction: int):
        """
        Smooth, cinematic multi-curtain swipe transition between stages:
          - Eased cubic motion with a gentle deceleration into full-screen hold.
          - Multi-layer pastel ribbons (peach, lavender, berry) for a luscious modern feel.
          - Large elegant typography with glowing pill card.
        """
        from ..config import LEVEL_TRANSITION_DURATION as _LTD
        phase = max(0.0, min(1.0, transition_t / max(0.001, _LTD)))

        W = self.board_area.width
        H = self.board_area.height
        lx = self.board_area.left
        ty = self.board_area.top

        # S-curve smoothstep for organic cinematic acceleration and deceleration
        # 0.0 -> 0.48: Swipe in and cover
        # 0.48 -> 0.52: Subtle hold while stage content swaps cleanly
        # 0.52 -> 1.0: Swipe out to reveal new stage
        if phase < 0.48:
            t = phase / 0.48
            # Smooth cubic ease-out
            progress = 1.0 - (1.0 - t) ** 3
            entering = True
        elif phase <= 0.52:
            progress = 1.0
            entering = True
        else:
            t = (phase - 0.52) / 0.48
            # Smooth cubic ease-in
            progress = 1.0 - (t ** 3)
            entering = False

        clip_rect = pygame.Rect(lx, ty, W, H)
        old_clip = self.surface.get_clip()
        self.surface.set_clip(clip_rect)

        # Multi-layer layered ribbon colors
        layers = [
            ((255, 185, 205), 0.88),  # Rose pastel outer leading trim
            ((248, 225, 238), 0.94),  # Soft lavender shimmer trim
            ((255, 118, 155), 1.00),  # Main vibrant berry canvas
        ]

        slant = int(H * 0.16)
        total_span = W + slant + 60

        for col, speed_scale in layers:
            cur_prog = min(1.0, progress * speed_scale)
            cur_w = int(total_span * cur_prog)
            if cur_w <= 0:
                continue

            if direction > 0:
                # Sliding from right to left
                x_start = lx + W - cur_w
                poly_pts = [
                    (x_start + slant, ty),
                    (lx + W + 10, ty),
                    (lx + W + 10, ty + H),
                    (x_start, ty + H),
                ]
            else:
                # Sliding from left to right
                x_end = lx + cur_w
                poly_pts = [
                    (lx - 10, ty),
                    (x_end, ty),
                    (x_end + slant, ty + H),
                    (lx - 10, ty + H),
                ]

            pygame.draw.polygon(self.surface, col, poly_pts)

        # Draw cute stage banner card at full cover
        if progress > 0.45:
            banner_alpha = int(255 * min(1.0, (progress - 0.45) / 0.40))
            b_w = min(420, W - 60)
            b_h = 76
            card_rect = pygame.Rect(lx + (W - b_w) // 2, ty + (H - b_h) // 2, b_w, b_h)

            card_surf = pygame.Surface((b_w, b_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (255, 255, 255, int(banner_alpha * 0.92)), card_surf.get_rect(), border_radius=22)
            pygame.draw.rect(card_surf, (244, 168, 192, banner_alpha), card_surf.get_rect(), width=3, border_radius=22)
            self.surface.blit(card_surf, card_rect.topleft)

            st_name = getattr(self, "_transition_stage_name", "Bloxorz Stage")
            txt_surf = self.font_big.render(st_name, True, (214, 65, 110))
            sub_surf = self.font_tiny.render("GET READY!", True, (138, 112, 142))

            self.surface.blit(txt_surf, txt_surf.get_rect(center=(card_rect.centerx, card_rect.centery - 10)))
            self.surface.blit(sub_surf, sub_surf.get_rect(center=(card_rect.centerx, card_rect.centery + 18)))

        self.surface.set_clip(old_clip)



    def _draw_overlay(
        self,
        title: str,
        subtitle: str,
        bg_color: Tuple[int, int, int],
        border_color: Tuple[int, int, int],
        title_color: Tuple[int, int, int],
    ):
        w = min(480, self.board_area.width - 80)
        h = 104
        banner_rect = pygame.Rect(
            self.board_area.centerx - w // 2,
            self.board_area.centery - h // 2,
            w,
            h,
        )
        draw_soft_shadow(self.surface, banner_rect, radius=18, offset=(0, 6), alpha=55, spread=4)
        pygame.draw.rect(self.surface, bg_color, banner_rect, border_radius=18)
        pygame.draw.rect(self.surface, border_color, banner_rect, width=3, border_radius=18)

        t_surf = self.font_big.render(title, True, title_color)
        s_surf = self.font_sub.render(subtitle, True, COLOR_TEXT_MUTED)

        self.surface.blit(t_surf, t_surf.get_rect(center=(banner_rect.centerx, banner_rect.centery - 14)))
        self.surface.blit(s_surf, s_surf.get_rect(center=(banner_rect.centerx, banner_rect.centery + 22)))