"""
Main Pygame GUI Application for Bloxorz.
Assigned to: Member 4 (GUI & Visualization)

Features a cute & bright pastel UI with:
- Dual View Modes: '2.5D' (Rotatable 3D / 2.5D Diorama Viewpoint) and '2D' (Algorithm Vis Viewpoint)
- Smooth Block Roll, Parabolic Hop, Split-Teleport, and Ambient Animations
- Interactive Mouse Drag Panning (LMB/MMB), 3D Viewpoint Orbiting (RMB or Shift+LMB), and Scroll Wheel Zoom
- Floating Camera Control Toolbar on the Playmat Canvas (+Zoom, -Zoom, Orbit L/R, Tilt, Reset Cam)
- Real-time AI solver execution (BFS, DFS, UCS, A*) with explored-cell heatmap tracking
- Stage Selection Dropdown beside Prev / Next to switch stages
- Bottom-right Camera Buttons occluded behind scene switch transition when changing levels
- Flexible & Responsive Screen Resizing (pygame.RESIZABLE)
- Benchmark Mode & Comparison Modal for all 4 algorithms on the active stage
- Non-blocking Asynchronous Solver execution with Animated 3D Waiting Screen
"""

import sys
import math
import time
import queue
import threading
from collections import deque
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any
import pygame
import json
import re

from ..config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SIDEBAR_WIDTH,
    FPS,
    VIEW_MODE_25D,
    VIEW_MODE_2D,
    MOVE_ANIM_DURATION,
    REPLAY_STEP_INTERVAL,
    DEATH_ANIM_DURATION,
    LEVEL_TRANSITION_DURATION,
    COLOR_BG,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_CARD_BG,
    COLOR_CARD_ALT_BG,
    COLOR_CARD_MINT_BG,
    COLOR_CARD_BORDER,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_ACCENT,
    BTN_PRIMARY,
    BTN_MINT,
    BTN_CORAL,
    BTN_SUNNY,
    BTN_LAVENDER,
    BTN_NEUTRAL,
    STAGES_DIR,
)
from ..game.constants import Direction
from ..game.stage_loader import StageLoader
from ..game.environment import BloxorzEnv
from ..game.state import GameState
from ..solvers.bfs import BFSSolver
from ..solvers.dfs import DFSSolver
from ..solvers.ucs import UCSSolver, custom_cost_function
from ..solvers.astar import AStarSolver
from ..solvers.heuristics import orientation_aware_heuristic
from ..solvers.base import SearchResult
from .renderer import GameRenderer
from .widgets import Button, ModeToggleSwitch, draw_pastel_card, Dropdown, BenchmarkModal


def _stage_sort_key(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            name = json.load(f).get("name", "")
    except Exception:
        name = ""
    stem = path.stem.lower()
    m = re.search(r"\d+", name)
    num = int(m.group()) if m else 10**9
    prefix_order = {
        "stage_": 0,
        "pro_dfs_": 1,
        "pro_bfs_": 2,
        "pro_ucs_": 3,
        "pro_astar_": 4,
        "con_astar_": 5,
    }
    group = 6
    for prefix, rank in prefix_order.items():
        if stem.startswith(prefix):
            group = rank
            break
    return (group, num, path.name)


class BloxorzApp:
    """
    Interactive Cute & Bright GUI application for Bloxorz Solver & 3D/2D Algorithm Visualizer.
    """

    def __init__(self, stages_dir: Optional[Path] = None):
        pygame.init()
        pygame.display.set_caption("Bloxorz AI Studio ✨ 3D/2.5D Orbit Diorama & 2D Algorithm Visualizer")

        # Responsive window dimensions
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.sidebar_width = SIDEBAR_WIDTH

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_title = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 21, bold=True)
        self.font_section = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 14, bold=True)
        self.font_main = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 13, bold=False)
        self.font_bold = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 13, bold=True)
        self.font_metric = pygame.font.SysFont("Consolas, Courier New, Monospace", 12, bold=True)
        self.font_tiny = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 11, bold=False)
        self.font_badge = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 10, bold=True)

        # Stage management
        self.stages_dir = stages_dir or STAGES_DIR
        self.stage_files = sorted(self.stages_dir.glob("*.json"), key=_stage_sort_key)
        if not self.stage_files:
            raise RuntimeError(f"No stage JSON files found in {self.stages_dir}")
        self.current_stage_idx = 0

        # Layout Areas
        self.board_area = pygame.Rect(0, 0, self.screen_width - self.sidebar_width, self.screen_height)
        self.sidebar_area = pygame.Rect(self.screen_width - self.sidebar_width, 0, self.sidebar_width, self.screen_height)

        self.renderer = GameRenderer(self.screen, self.board_area)
        self.view_mode = VIEW_MODE_25D

        # Game & Animation state
        self.env: Optional[BloxorzEnv] = None
        self.state: Optional[GameState] = None
        self.prev_state: Optional[GameState] = None
        self.anim_progress: float = 1.0
        self.anim_duration: float = MOVE_ANIM_DURATION
        self.anim_time: float = 0.0
        self.is_won = False
        self.is_lost = False
        self.move_count = 0

        # Death animation
        self.death_anim_t: float = -1.0

        # Level-swipe transition
        self.level_transition_t: float = -1.0
        self.level_transition_dir: int = 1
        self._pending_stage_idx: Optional[int] = None

        # Mouse Drag Pan & 3D Orbit Interaction State
        self.is_panning: bool = False
        self.is_orbiting: bool = False
        self.last_mouse_pos: Tuple[int, int] = (0, 0)

        # Solvers, Replay & Algorithm Visualization Overlays
        self.last_result: Optional[SearchResult] = None
        self.replay_states: List[GameState] = []
        self.explored_cells: Dict[Tuple[int, int], int] = {}
        self.replay_idx = 0
        self.is_replaying = False
        self.replay_timer = 0
        self.replay_interval = REPLAY_STEP_INTERVAL

        # Asynchronous worker thread & Waiting Screen state
        self.is_waiting: bool = False
        self.waiting_task_type: Optional[str] = None  # "single" or "benchmark"
        self.waiting_title: str = ""
        self.waiting_subtitle: str = ""
        self.waiting_start_time: float = 0.0
        self.waiting_cancel_event = threading.Event()
        self.async_worker_queue = queue.Queue()
        self.async_thread: Optional[threading.Thread] = None

        # Benchmark comparison modal state
        self.benchmark_modal: Optional[BenchmarkModal] = None

        # Initialize UI controls
        self.buttons: List[Button] = []
        self.cam_buttons: List[Button] = []
        self.mode_switch: Optional[ModeToggleSwitch] = None
        self.stage_dropdown: Optional[Dropdown] = None
        self.btn_wait_cancel: Optional[Button] = None

        self._init_widgets()

        # Load initial stage
        self.load_stage(self.current_stage_idx)

    def _get_stage_display_name(self, idx: int) -> str:
        path = self.stage_files[idx % len(self.stage_files)]
        cache = self.__dict__.setdefault("_stage_name_cache", {})
        if path not in cache:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cache[path] = json.load(f).get("name") or path.stem.replace("_", " ").title()
            except Exception:
                cache[path] = path.stem.replace("_", " ").title()
        return cache[path]

    def _init_widgets(self):
        """Constructs all cute pastel sidebar controls, dropdown, benchmark button, and camera HUD."""
        sb_x = self.sidebar_area.left + 14
        card_w = self.sidebar_area.width - 28
        inner_x = self.sidebar_area.left + 22
        w = card_w - 16

        # 1. Header & Stage Selector Card (Title, Reset on top right; Prev, Dropdown, Next below)
        stage_items = [f"{i+1}. {self._get_stage_display_name(i)}" for i in range(len(self.stage_files))]
        btn_nav_w = 54
        dd_w = w - 2 * (btn_nav_w + 6)

        self.btn_restart = Button(
            rect=(sb_x + card_w - 82, 17, 72, 26),
            text="↺ Reset",
            on_click=self.restart_stage,
            bg_color=BTN_CORAL[0],
            hover_color=BTN_CORAL[1],
            shadow_color=BTN_CORAL[2],
            text_color=BTN_CORAL[3],
            font_size=12,
            border_radius=8,
        )

        self.btn_prev_stage = Button(
            rect=(inner_x, 56, btn_nav_w, 32),
            text="< Prev",
            on_click=self.prev_stage,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=12,
            border_radius=8,
        )

        self.stage_dropdown = Dropdown(
            rect=(inner_x + btn_nav_w + 6, 56, dd_w, 32),
            items=stage_items,
            selected_idx=self.current_stage_idx,
            on_select=self.on_dropdown_stage_select,
            max_visible_items=8,
            item_height=28,
            font_size=12,
        )

        self.btn_next_stage = Button(
            rect=(inner_x + btn_nav_w + 6 + dd_w + 6, 56, btn_nav_w, 32),
            text="Next >",
            on_click=self.next_stage,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=12,
            border_radius=8,
        )

        # 2. View Mode Segmented Switch (3D/2.5D vs 2D Algo Vis)
        y_mode = 112
        self.mode_switch = ModeToggleSwitch(
            rect=(inner_x, y_mode + 24, w, 34),
            mode=self.view_mode,
            on_change=self.set_view_mode,
        )

        # 3. AI Search Solvers & Benchmark Card
        y_solv = 186
        half_w = (w - 8) // 2
        solv_h = 32

        self.btn_bfs = Button(
            rect=(inner_x, y_solv + 26, half_w, solv_h),
            text="Solve BFS",
            on_click=lambda: self.start_solver_async(BFSSolver()),
            bg_color=BTN_PRIMARY[0],
            hover_color=BTN_PRIMARY[1],
            shadow_color=BTN_PRIMARY[2],
            text_color=BTN_PRIMARY[3],
            font_size=13,
            border_radius=8,
        )
        self.btn_dfs = Button(
            rect=(inner_x + half_w + 8, y_solv + 26, half_w, solv_h),
            text="Solve DFS",
            on_click=lambda: self.start_solver_async(DFSSolver(max_depth=400)),
            bg_color=BTN_LAVENDER[0],
            hover_color=BTN_LAVENDER[1],
            shadow_color=BTN_LAVENDER[2],
            text_color=BTN_LAVENDER[3],
            font_size=13,
            border_radius=8,
        )
        self.btn_ucs = Button(
            rect=(inner_x, y_solv + 64, half_w, solv_h),
            text="Solve UCS",
            on_click=lambda: self.start_solver_async(UCSSolver(cost_fn=custom_cost_function)),
            bg_color=BTN_SUNNY[0],
            hover_color=BTN_SUNNY[1],
            shadow_color=BTN_SUNNY[2],
            text_color=BTN_SUNNY[3],
            font_size=13,
            border_radius=8,
        )
        self.btn_astar = Button(
            rect=(inner_x + half_w + 8, y_solv + 64, half_w, solv_h),
            text="Solve A*",
            on_click=lambda: self.start_solver_async(AStarSolver(heuristic_fn=orientation_aware_heuristic)),
            bg_color=BTN_MINT[0],
            hover_color=BTN_MINT[1],
            shadow_color=BTN_MINT[2],
            text_color=BTN_MINT[3],
            font_size=13,
            border_radius=8,
        )

        # 4. Benchmark Stage Button (runs BFS, DFS, UCS, A* & displays comparison modal)
        self.btn_benchmark = Button(
            rect=(inner_x, y_solv + 104, w, 32),
            text="⚡ Benchmark All 4 Algorithms",
            on_click=self.start_benchmark_async,
            bg_color=(255, 128, 148),
            hover_color=(255, 150, 168),
            shadow_color=(214, 88, 108),
            text_color=(255, 255, 255),
            font_size=12,
            border_radius=8,
        )

        # 5. Replay Controller Buttons (Play/Pause, < Step, Step >, Start)
        y_rep = 348
        btn_w4 = (w - 18) // 4
        self.btn_replay_toggle = Button(
            rect=(inner_x, y_rep + 26, btn_w4, 32),
            text="Play",
            on_click=self.toggle_replay,
            bg_color=BTN_MINT[0],
            hover_color=BTN_MINT[1],
            shadow_color=BTN_MINT[2],
            text_color=BTN_MINT[3],
            font_size=12,
            border_radius=8,
        )
        self.btn_replay_prev = Button(
            rect=(inner_x + (btn_w4 + 6), y_rep + 26, btn_w4, 32),
            text="< Step",
            on_click=self.step_backward_replay,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=12,
            border_radius=8,
        )
        self.btn_replay_step = Button(
            rect=(inner_x + 2 * (btn_w4 + 6), y_rep + 26, btn_w4, 32),
            text="Step >",
            on_click=self.step_forward_replay,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=12,
            border_radius=8,
        )
        self.btn_replay_reset = Button(
            rect=(inner_x + 3 * (btn_w4 + 6), y_rep + 26, btn_w4, 32),
            text="Start",
            on_click=self.reset_replay,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=12,
            border_radius=8,
        )

        # 6. Waiting screen cancel button
        self.btn_wait_cancel = Button(
            rect=(0, 0, 96, 28),
            text="Cancel",
            on_click=self.cancel_waiting,
            bg_color=BTN_CORAL[0],
            hover_color=BTN_CORAL[1],
            shadow_color=BTN_CORAL[2],
            text_color=BTN_CORAL[3],
            font_size=12,
            border_radius=8,
        )

        # 7. Floating Camera Toolbar Buttons inside Playmat Bottom-Right
        self._layout_cam_buttons()

        self.buttons = [
            self.btn_restart,
            self.btn_prev_stage,
            self.btn_next_stage,
            self.btn_bfs,
            self.btn_dfs,
            self.btn_ucs,
            self.btn_astar,
            self.btn_benchmark,
            self.btn_replay_toggle,
            self.btn_replay_prev,
            self.btn_replay_step,
            self.btn_replay_reset,
        ] + self.cam_buttons

    def _layout_cam_buttons(self):
        """Positions floating camera buttons anchored cleanly to bottom-right of playmat."""
        cam_y = self.board_area.bottom - 94
        cam_right = self.board_area.right - 36

        if not hasattr(self, "btn_cam_zoom_in") or self.btn_cam_zoom_in is None:
            self.btn_cam_zoom_in = Button(
                rect=(cam_right - 310, cam_y, 48, 28),
                text="Zoom+",
                on_click=lambda: self.renderer.zoom_camera(1.18),
                bg_color=BTN_NEUTRAL[0],
                hover_color=BTN_NEUTRAL[1],
                shadow_color=BTN_NEUTRAL[2],
                text_color=BTN_NEUTRAL[3],
                font_size=11,
                border_radius=8,
            )
            self.btn_cam_zoom_out = Button(
                rect=(cam_right - 258, cam_y, 48, 28),
                text="Zoom-",
                on_click=lambda: self.renderer.zoom_camera(1.0 / 1.18),
                bg_color=BTN_NEUTRAL[0],
                hover_color=BTN_NEUTRAL[1],
                shadow_color=BTN_NEUTRAL[2],
                text_color=BTN_NEUTRAL[3],
                font_size=11,
                border_radius=8,
            )
            self.btn_cam_orbit_l = Button(
                rect=(cam_right - 206, cam_y, 48, 28),
                text="Orbit L",
                on_click=lambda: self.renderer.orbit_camera(-22.5, 0.0),
                bg_color=BTN_LAVENDER[0],
                hover_color=BTN_LAVENDER[1],
                shadow_color=BTN_LAVENDER[2],
                text_color=BTN_LAVENDER[3],
                font_size=11,
                border_radius=8,
            )
            self.btn_cam_orbit_r = Button(
                rect=(cam_right - 154, cam_y, 48, 28),
                text="Orbit R",
                on_click=lambda: self.renderer.orbit_camera(22.5, 0.0),
                bg_color=BTN_LAVENDER[0],
                hover_color=BTN_LAVENDER[1],
                shadow_color=BTN_LAVENDER[2],
                text_color=BTN_LAVENDER[3],
                font_size=11,
                border_radius=8,
            )
            self.btn_cam_tilt = Button(
                rect=(cam_right - 102, cam_y, 46, 28),
                text="3D Tilt",
                on_click=self._cycle_camera_tilt,
                bg_color=BTN_PRIMARY[0],
                hover_color=BTN_PRIMARY[1],
                shadow_color=BTN_PRIMARY[2],
                text_color=BTN_PRIMARY[3],
                font_size=11,
                border_radius=8,
            )
            self.btn_cam_reset = Button(
                rect=(cam_right - 52, cam_y, 52, 28),
                text="Center",
                on_click=self.renderer.reset_camera,
                bg_color=BTN_SUNNY[0],
                hover_color=BTN_SUNNY[1],
                shadow_color=BTN_SUNNY[2],
                text_color=BTN_SUNNY[3],
                font_size=11,
                border_radius=8,
            )
            self.cam_buttons = [
                self.btn_cam_zoom_in,
                self.btn_cam_zoom_out,
                self.btn_cam_orbit_l,
                self.btn_cam_orbit_r,
                self.btn_cam_tilt,
                self.btn_cam_reset,
            ]
        else:
            self.btn_cam_zoom_in.rect = pygame.Rect(cam_right - 310, cam_y, 48, 28)
            self.btn_cam_zoom_out.rect = pygame.Rect(cam_right - 258, cam_y, 48, 28)
            self.btn_cam_orbit_l.rect = pygame.Rect(cam_right - 206, cam_y, 48, 28)
            self.btn_cam_orbit_r.rect = pygame.Rect(cam_right - 154, cam_y, 48, 28)
            self.btn_cam_tilt.rect = pygame.Rect(cam_right - 102, cam_y, 46, 28)
            self.btn_cam_reset.rect = pygame.Rect(cam_right - 52, cam_y, 52, 28)

    def recompute_layout(self, new_w: int, new_h: int):
        """Dynamically adapts all UI elements, cards, and viewport to window resize."""
        self.screen_width = max(1000, new_w)
        self.screen_height = max(680, new_h)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

        self.sidebar_width = min(390, max(330, int(self.screen_width * 0.28)))
        self.board_area = pygame.Rect(0, 0, self.screen_width - self.sidebar_width, self.screen_height)
        self.sidebar_area = pygame.Rect(self.screen_width - self.sidebar_width, 0, self.sidebar_width, self.screen_height)

        self.renderer.update_dimensions(self.screen, self.board_area)

        # Re-layout sidebar widgets
        sb_x = self.sidebar_area.left + 14
        card_w = self.sidebar_area.width - 28
        inner_x = self.sidebar_area.left + 22
        w = card_w - 16

        btn_nav_w = 54
        dd_w = w - 2 * (btn_nav_w + 6)

        self.btn_restart.rect = pygame.Rect(sb_x + card_w - 82, 17, 72, 26)
        self.btn_prev_stage.rect = pygame.Rect(inner_x, 56, btn_nav_w, 32)
        if self.stage_dropdown:
            self.stage_dropdown.set_rect((inner_x + btn_nav_w + 6, 56, dd_w, 32))
        self.btn_next_stage.rect = pygame.Rect(inner_x + btn_nav_w + 6 + dd_w + 6, 56, btn_nav_w, 32)

        y_mode = 112
        if self.mode_switch:
            self.mode_switch.rect = pygame.Rect(inner_x, y_mode + 24, w, 34)

        y_solv = 186
        half_w = (w - 8) // 2
        solv_h = 32
        self.btn_bfs.rect = pygame.Rect(inner_x, y_solv + 26, half_w, solv_h)
        self.btn_dfs.rect = pygame.Rect(inner_x + half_w + 8, y_solv + 26, half_w, solv_h)
        self.btn_ucs.rect = pygame.Rect(inner_x, y_solv + 64, half_w, solv_h)
        self.btn_astar.rect = pygame.Rect(inner_x + half_w + 8, y_solv + 64, half_w, solv_h)
        self.btn_benchmark.rect = pygame.Rect(inner_x, y_solv + 104, w, 32)

        y_rep = 348
        btn_w4 = (w - 18) // 4
        self.btn_replay_toggle.rect = pygame.Rect(inner_x, y_rep + 26, btn_w4, 32)
        self.btn_replay_prev.rect = pygame.Rect(inner_x + (btn_w4 + 6), y_rep + 26, btn_w4, 32)
        self.btn_replay_step.rect = pygame.Rect(inner_x + 2 * (btn_w4 + 6), y_rep + 26, btn_w4, 32)
        self.btn_replay_reset.rect = pygame.Rect(inner_x + 3 * (btn_w4 + 6), y_rep + 26, btn_w4, 32)

        self._layout_cam_buttons()

    def _cycle_camera_tilt(self):
        """Cycles through 3D viewpoint pitch presets (Low 3D -> Classic Iso -> High Overview)."""
        presets = [34.0, 54.0, 74.0]
        cur = self.renderer.cam_pitch
        nxt = presets[0]
        for p in presets:
            if cur < p - 4.0:
                nxt = p
                break
        self.renderer.cam_pitch = nxt

    def _trigger_state_transition(self, new_state: GameState, duration: float = MOVE_ANIM_DURATION):
        """Starts a smooth block roll/hop animation from the current state to `new_state`."""
        self.prev_state = self.state
        self.state = new_state
        self.anim_duration = max(0.05, duration)
        self.anim_progress = 0.0

    def set_view_mode(self, mode: str):
        """Updates view mode ('2.5D' or '2D') across app, renderer, and toggle widget."""
        self.view_mode = mode
        self.renderer.set_view_mode(mode)
        if self.mode_switch:
            self.mode_switch.mode = mode

    def toggle_view_mode(self):
        """Flips between 2.5D and 2D view modes."""
        new_mode = VIEW_MODE_2D if self.view_mode == VIEW_MODE_25D else VIEW_MODE_25D
        self.set_view_mode(new_mode)

    def load_stage(self, idx: int):
        """Loads stage at index and resets camera. Called directly OR by the swipe-transition."""
        self.current_stage_idx = idx % len(self.stage_files)
        stage_file = self.stage_files[self.current_stage_idx]
        board = StageLoader.load_from_file(stage_file)
        self.env = BloxorzEnv(board)
        self.renderer.reset_camera()
        if self.stage_dropdown:
            self.stage_dropdown.selected_idx = self.current_stage_idx
        self.restart_stage()

    def restart_stage(self):
        """Resets the current stage to start state."""
        self.state = self.env.get_initial_state()
        self.prev_state = self.state
        self.anim_progress = 1.0
        self.is_won = False
        self.is_lost = False
        self.death_anim_t = -1.0
        self.move_count = 0
        self.last_result = None
        self.replay_states = []
        self.explored_cells = {}
        self.replay_idx = 0
        self.is_replaying = False
        self.btn_replay_toggle.text = "Play"
        for b in (self.btn_bfs, self.btn_dfs, self.btn_ucs, self.btn_astar):
            b.is_active = False

    def _start_level_transition(self, target_idx: int, direction: int):
        """Begins the swipe-out phase of the level transition animation."""
        if self.level_transition_t >= 0:
            return
        self._pending_stage_idx = target_idx % len(self.stage_files)
        self.level_transition_dir = direction
        self.level_transition_t = 0.0
        stage_file = self.stage_files[self._pending_stage_idx]
        self.renderer._transition_stage_name = self._get_stage_display_name(self._pending_stage_idx)

    def _finish_level_transition(self):
        """Called at mid-point of the swipe animation to actually swap the stage."""
        if self._pending_stage_idx is not None:
            self.load_stage(self._pending_stage_idx)
            self._pending_stage_idx = None

    def next_stage(self):
        self._start_level_transition(self.current_stage_idx + 1, direction=+1)

    def prev_stage(self):
        self._start_level_transition(self.current_stage_idx - 1, direction=-1)

    def on_dropdown_stage_select(self, target_idx: int):
        """Handles user selecting a stage from the dropdown selector."""
        if target_idx != self.current_stage_idx:
            dir = +1 if target_idx > self.current_stage_idx else -1
            self._start_level_transition(target_idx, direction=dir)

    def _compute_explored_cells(self, max_states: int, path_states: List[GameState]) -> Dict[Tuple[int, int], int]:
        """Builds a cell visitation map `(r, c) -> order` for the search space heatmap."""
        explored: Dict[Tuple[int, int], int] = {}
        init_state = self.env.get_initial_state()
        queue_st = deque([init_state])
        visited = {init_state}
        step_counter = 0

        while queue_st and len(visited) <= max(12, max_states):
            curr = queue_st.popleft()
            step_counter += 1
            for cell in curr.block.occupied_cells():
                if cell not in explored:
                    explored[cell] = step_counter
            for _, nxt, _ in self.env.get_successors(curr):
                if nxt not in visited:
                    visited.add(nxt)
                    queue_st.append(nxt)

        for st in path_states:
            step_counter += 1
            for cell in st.block.occupied_cells():
                if cell not in explored:
                    explored[cell] = step_counter

        return explored

    # ========================================================================
    # ASYNCHRONOUS SOLVER & BENCHMARK THREADING
    # ========================================================================

    def start_solver_async(self, solver) -> None:
        """Starts asynchronous execution of a single solver with animated waiting screen."""
        if self.is_waiting:
            return

        self.is_waiting = True
        self.waiting_task_type = "single"
        self.waiting_title = f"Solving with {solver.name}..."
        stage_title = self._get_stage_display_name(self.current_stage_idx)
        self.waiting_subtitle = f"Searching for solution on {stage_title}..."
        self.waiting_start_time = time.time()
        self.waiting_cancel_event.clear()

        # Update solver button active state
        solver_btn_map = {
            "BFS": self.btn_bfs,
            "DFS": self.btn_dfs,
            "UCS": self.btn_ucs,
            "A*": self.btn_astar,
        }
        for name, btn in solver_btn_map.items():
            btn.is_active = (name == solver.name)

        def worker():
            res = solver.solve(self.env)
            if not self.waiting_cancel_event.is_set():
                self.async_worker_queue.put(("single", solver, res))

        self.async_thread = threading.Thread(target=worker, daemon=True)
        self.async_thread.start()

    def start_benchmark_async(self) -> None:
        """Starts asynchronous benchmark comparing BFS, DFS, UCS, A* on the current stage."""
        if self.is_waiting:
            return

        self.is_waiting = True
        self.waiting_task_type = "benchmark"
        self.waiting_title = "Benchmarking 4 Algorithms..."
        stage_title = self._get_stage_display_name(self.current_stage_idx)
        self.waiting_subtitle = f"Starting evaluation suite on {stage_title}..."
        self.waiting_start_time = time.time()
        self.waiting_cancel_event.clear()

        for b in (self.btn_bfs, self.btn_dfs, self.btn_ucs, self.btn_astar):
            b.is_active = False

        def worker():
            solvers = [
                BFSSolver(),
                DFSSolver(max_depth=400),
                UCSSolver(cost_fn=custom_cost_function),
                AStarSolver(heuristic_fn=orientation_aware_heuristic),
            ]
            results = []
            for i, s in enumerate(solvers):
                if self.waiting_cancel_event.is_set():
                    break
                self.waiting_subtitle = f"Evaluating {s.name} ({i+1}/4)..."
                res = s.solve(self.env, timeout=20.0)
                results.append({
                    "algorithm": s.name,
                    "success": res.success,
                    "moves": res.solution_length if res.success else None,
                    "cost": round(res.solution_cost, 2) if res.success else None,
                    "time_ms": round(res.search_time * 1000, 2),
                    "peak_mem_kb": round(res.peak_memory_kb, 2),
                    "expanded_nodes": res.expanded_nodes,
                    "generated_nodes": res.generated_nodes,
                    "status": res.status_message,
                    "result_obj": res,
                })
            if not self.waiting_cancel_event.is_set():
                self.async_worker_queue.put(("benchmark", results))

        self.async_thread = threading.Thread(target=worker, daemon=True)
        self.async_thread.start()

    def cancel_waiting(self):
        """Aborts current asynchronous search execution."""
        self.waiting_cancel_event.set()
        self.is_waiting = False
        for b in (self.btn_bfs, self.btn_dfs, self.btn_ucs, self.btn_astar):
            b.is_active = False

    def _on_single_solver_completed(self, solver, result: SearchResult):
        """Called when a single solver search finishes."""
        self.last_result = result
        if result.success and result.states:
            self.replay_states = result.states
            self.explored_cells = self._compute_explored_cells(
                result.expanded_nodes, result.states
            )
            self.replay_timer = 0
            self.is_lost = False
            self.reset_replay()
            self.toggle_replay()
        else:
            self.replay_states = []
            self.explored_cells = {}
            self.is_replaying = False
            self.btn_replay_toggle.text = "Play"

    def _on_benchmark_completed(self, results: List[Dict[str, Any]]):
        """Opens comparison benchmark modal upon completion of all 4 search algorithms."""
        stage_name = self._get_stage_display_name(self.current_stage_idx)
        self.benchmark_modal = BenchmarkModal(
            stage_name=stage_name,
            results=results,
            on_replay=self.apply_benchmark_solution,
            on_close=self.close_benchmark_modal,
        )

    def apply_benchmark_solution(self, algo_name: str):
        """Applies chosen algorithm's solution from the benchmark modal into the main view."""
        if not self.benchmark_modal:
            return
        match = next((r for r in self.benchmark_modal.results if r["algorithm"] == algo_name), None)
        if match and match.get("result_obj"):
            res: SearchResult = match["result_obj"]
            solver_btn_map = {
                "BFS": self.btn_bfs,
                "DFS": self.btn_dfs,
                "UCS": self.btn_ucs,
                "A*": self.btn_astar,
            }
            for name, btn in solver_btn_map.items():
                btn.is_active = (name == algo_name)
            self._on_single_solver_completed(None, res)
        self.close_benchmark_modal()

    def close_benchmark_modal(self):
        """Dismisses benchmark comparison modal."""
        self.benchmark_modal = None

    # ========================================================================
    # REPLAY & MANUAL CONTROLS
    # ========================================================================

    def toggle_replay(self):
        """Toggles between Play and Pause during solution replay."""
        if not self.replay_states:
            return
        if not self.is_replaying and self.replay_idx >= len(self.replay_states) - 1:
            self.replay_idx = 0
            self.state = self.replay_states[0]
            self.prev_state = self.state
            self.anim_progress = 1.0
            self.move_count = 0
            self.is_won = False
        self.is_replaying = not self.is_replaying
        self.btn_replay_toggle.text = "Pause" if self.is_replaying else "Play"

    def step_forward_replay(self):
        """Steps forward one move in the solution sequence with smooth animation."""
        if not self.replay_states:
            return
        self.is_replaying = False
        self.replay_timer = 0
        self.btn_replay_toggle.text = "Play"

        if self.replay_idx < len(self.replay_states) - 1:
            self.replay_idx += 1
            self._trigger_state_transition(self.replay_states[self.replay_idx], duration=MOVE_ANIM_DURATION)
            self.move_count = self.replay_idx
            self.is_won = self.state.is_goal(self.env.board)

    def step_backward_replay(self):
        """Steps backward one move in the solution sequence with smooth animation."""
        if not self.replay_states:
            return
        self.is_replaying = False
        self.replay_timer = 0
        self.btn_replay_toggle.text = "Play"

        if self.replay_idx > 0:
            self.replay_idx -= 1
            self._trigger_state_transition(self.replay_states[self.replay_idx], duration=MOVE_ANIM_DURATION)
            self.move_count = self.replay_idx
            self.is_won = self.state.is_goal(self.env.board)

    def reset_replay(self):
        """Resets replay back to the initial step."""
        if not self.replay_states:
            return
        self.is_replaying = False
        self.btn_replay_toggle.text = "Play"
        self.replay_idx = 0
        self.state = self.replay_states[0]
        self.prev_state = self.state
        self.anim_progress = 1.0
        self.move_count = 0
        self.is_won = False

    def handle_manual_move(self, direction: Direction):
        """Processes keyboard move from human player with smooth block roll animation."""
        if self.is_replaying or self.is_won or self.is_lost:
            return
        next_state = self.env.step(self.state, direction)
        if next_state is None:
            self.is_lost = True
            self.death_anim_t = 0.0
            failing_block = self.state.block.roll(direction)
            self.prev_state = self.state
            self.state = GameState(block=failing_block, bridge_states=self.state.bridge_states)
            self.anim_progress = 0.0
            self.anim_duration = 0.25
        else:
            self._trigger_state_transition(next_state, duration=MOVE_ANIM_DURATION)
            self.move_count += 1
            for cell in self.state.block.occupied_cells():
                if cell not in self.explored_cells:
                    self.explored_cells[cell] = self.move_count
            self.is_won = self.state.is_goal(self.env.board)

    # ========================================================================
    # RENDERING
    # ========================================================================

    def render_frame(self):
        """
        Renders complete frame with proper layering:
        1. Canvas & Playmat
        2. Board & Block
        3. Floating Camera HUD buttons (drawn BEFORE level transition overlay so transition occludes them!)
        4. Level transition swipe overlay
        5. Sidebar with cards & buttons
        6. Dropdown popup menu (if open)
        7. Benchmark comparison modal (if open)
        8. Animated 3D Waiting screen (if solving)
        """
        self.screen.fill(COLOR_BG)

        # Draw board scene + camera buttons + level transition
        # cam_buttons is passed directly to renderer.draw() so it renders BEHIND the transition swipe!
        self.renderer.draw(
            board=self.env.board,
            state=self.state,
            is_won=self.is_won,
            is_lost=self.is_lost,
            view_mode=self.view_mode,
            explored_cells=self.explored_cells,
            replay_states=self.replay_states,
            replay_idx=self.replay_idx,
            prev_state=self.prev_state,
            anim_progress=self.anim_progress,
            anim_time=self.anim_time,
            death_anim_t=self.death_anim_t,
            level_transition_t=self.level_transition_t,
            level_transition_dir=self.level_transition_dir,
            cam_buttons=self.cam_buttons,
        )

        self._draw_sidebar()

        # Overlays on top of everything
        if self.stage_dropdown and self.stage_dropdown.is_open:
            self.stage_dropdown.draw_popup(self.screen)

        if self.benchmark_modal:
            self.benchmark_modal.draw(self.screen)

        if self.is_waiting:
            self._draw_waiting_screen()

    def _draw_waiting_screen(self):
        """Renders an adorable animated 3D Bloxorz waiting screen overlay during search execution."""
        # 1. Dark pastel backdrop scrim
        dim = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim.fill((30, 22, 44, 160))
        self.screen.blit(dim, (0, 0))

        # 2. Centered modal card
        cw, ch = 440, 240
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        card_rect = pygame.Rect(cx - cw // 2, cy - ch // 2, cw, ch)

        draw_pastel_card(
            self.screen,
            card_rect,
            bg_color=(255, 252, 250),
            border_color=(230, 196, 218),
            radius=20,
            shadow=True,
        )

        # 3. Adorable spinning 3D Bloxorz Block animation
        bx = cx
        by = card_rect.top + 64
        bob = math.sin(self.anim_time * 5.0) * 7.0

        # Pulsing halo glow
        glow_r = int(34 + 6 * math.sin(self.anim_time * 7.0))
        glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 148, 178, 65), (glow_r + 2, glow_r + 2), glow_r)
        self.screen.blit(glow_surf, (bx - glow_r - 2, int(by + bob - glow_r - 2)))

        # 3D Rotating Isometric Block
        theta = self.anim_time * 2.8
        scale_u = 16.0

        def proj3d(gx, gy, gz):
            rx = gx * math.cos(theta) - gy * math.sin(theta)
            ry = gx * math.sin(theta) + gy * math.cos(theta)
            px = bx + rx * scale_u
            py = by + bob + ry * (scale_u * 0.55) - gz * (scale_u * 0.95)
            return (int(round(px)), int(round(py)))

        # Draw a 1x1x2 Bloxorz standing block
        # Corners at z=0 (bottom) and z=2 (top)
        b00 = proj3d(-0.7, -0.7, -0.4)
        b10 = proj3d(0.7, -0.7, -0.4)
        b11 = proj3d(0.7, 0.7, -0.4)
        b01 = proj3d(-0.7, 0.7, -0.4)

        t00 = proj3d(-0.7, -0.7, 1.6)
        t10 = proj3d(0.7, -0.7, 1.6)
        t11 = proj3d(0.7, 0.7, 1.6)
        t01 = proj3d(-0.7, 0.7, 1.6)

        sin_t = math.sin(theta)
        cos_t = math.cos(theta)

        # Render visible side walls based on rotation angle
        border_col = (148, 48, 72)
        if sin_t >= 0:
            east_q = [t10, t11, b11, b10]
            pygame.draw.polygon(self.screen, (212, 82, 108), east_q)
            pygame.draw.polygon(self.screen, border_col, east_q, width=2)
        else:
            west_q = [t01, t00, b00, b01]
            pygame.draw.polygon(self.screen, (212, 82, 108), west_q)
            pygame.draw.polygon(self.screen, border_col, west_q, width=2)

        if cos_t >= 0:
            south_q = [t01, t11, b11, b01]
            pygame.draw.polygon(self.screen, (238, 104, 128), south_q)
            pygame.draw.polygon(self.screen, border_col, south_q, width=2)
        else:
            north_q = [t10, t00, b00, b10]
            pygame.draw.polygon(self.screen, (238, 104, 128), north_q)
            pygame.draw.polygon(self.screen, border_col, north_q, width=2)

        top_q = [t00, t10, t11, t01]
        pygame.draw.polygon(self.screen, (255, 142, 168), top_q)
        pygame.draw.polygon(self.screen, border_col, top_q, width=2)

        # Glossy highlight on top
        shine_pt = ((t00[0] + t10[0] + t11[0] + t01[0]) // 4, (t00[1] + t10[1] + t11[1] + t01[1]) // 4)
        pygame.draw.circle(self.screen, (255, 230, 240), shine_pt, 3)

        # 4. Title, Subtitle, and Timer
        t_surf = self.font_title.render(self.waiting_title, True, (218, 68, 108))
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, card_rect.top + 130)))

        sub_surf = self.font_main.render(self.waiting_subtitle, True, COLOR_TEXT_MUTED)
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(cx, card_rect.top + 154)))

        elapsed = time.time() - self.waiting_start_time
        time_txt = f"Search Time Elapsed: {elapsed:.1f}s"
        time_surf = self.font_metric.render(time_txt, True, (118, 102, 138))
        self.screen.blit(time_surf, time_surf.get_rect(center=(cx, card_rect.top + 176)))

        # 5. Cancel Button
        if self.btn_wait_cancel:
            self.btn_wait_cancel.rect = pygame.Rect(cx - 48, card_rect.bottom - 38, 96, 28)
            self.btn_wait_cancel.draw(self.screen)

    def _draw_sidebar(self):
        """Renders the cute & bright pastel sidebar with organized cards, dropdown, and metrics."""
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.sidebar_area)
        pygame.draw.line(
            self.screen,
            COLOR_PANEL_BORDER,
            self.sidebar_area.topleft,
            self.sidebar_area.bottomleft,
            3,
        )

        sb_x = self.sidebar_area.left + 14
        card_w = self.sidebar_area.width - 28
        inner_x = self.sidebar_area.left + 22
        w = card_w - 16

        # 1. Header & Stage Selector Card (Title, Reset on top right; Prev, Dropdown, Next below)
        stage_card = pygame.Rect(sb_x, 12, card_w, 92)
        draw_pastel_card(self.screen, stage_card, bg_color=COLOR_CARD_ALT_BG, border_color=(244, 214, 206), radius=16)

        title_surf = self.font_title.render("Bloxorz AI Studio", True, COLOR_TEXT_ACCENT)
        self.screen.blit(title_surf, (inner_x, 18))

        self.btn_restart.draw(self.screen)
        self.btn_prev_stage.draw(self.screen)
        if self.stage_dropdown:
            self.stage_dropdown.draw(self.screen)
        self.btn_next_stage.draw(self.screen)

        # 2. View Mode Switcher Card (3D/2.5D vs 2D Algo Vis)
        y_mode = 112
        mode_card = pygame.Rect(sb_x, y_mode, card_w, 66)
        draw_pastel_card(self.screen, mode_card, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER, radius=16)
        mode_hdr = self.font_tiny.render("VIEWPOINT & VISUALIZATION MODE (KEY: M)", True, COLOR_TEXT_MUTED)
        self.screen.blit(mode_hdr, (inner_x, y_mode + 8))
        if self.mode_switch:
            self.mode_switch.draw(self.screen)

        # 3. AI Search Solvers & Benchmark Card
        y_solv = 186
        solv_card = pygame.Rect(sb_x, y_solv, card_w, 154)
        draw_pastel_card(self.screen, solv_card, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER, radius=16)
        solv_hdr = self.font_section.render("Search Algorithms & Benchmark", True, COLOR_TEXT)
        self.screen.blit(solv_hdr, (inner_x, y_solv + 7))

        self.btn_bfs.draw(self.screen)
        self.btn_dfs.draw(self.screen)
        self.btn_ucs.draw(self.screen)
        self.btn_astar.draw(self.screen)
        self.btn_benchmark.draw(self.screen)

        # 4. Replay & Trajectory Controller Card
        y_rep = 348
        rep_card = pygame.Rect(sb_x, y_rep, card_w, 110)
        draw_pastel_card(self.screen, rep_card, bg_color=COLOR_CARD_MINT_BG, border_color=(196, 234, 220), radius=16)
        rep_hdr = self.font_section.render("Animated Solution Replay", True, COLOR_TEXT)
        self.screen.blit(rep_hdr, (inner_x, y_rep + 7))

        self.btn_replay_toggle.draw(self.screen)
        self.btn_replay_prev.draw(self.screen)
        self.btn_replay_step.draw(self.screen)
        self.btn_replay_reset.draw(self.screen)

        # Replay Progress Bar
        prog_bg = pygame.Rect(inner_x, y_rep + 66, w, 10)
        pygame.draw.rect(self.screen, (214, 238, 228), prog_bg, border_radius=5)
        if self.replay_states and len(self.replay_states) > 1:
            ratio = self.replay_idx / float(len(self.replay_states) - 1)
            fill_w = max(6, int(prog_bg.width * ratio))
            prog_fill = pygame.Rect(prog_bg.left, prog_bg.top, fill_w, prog_bg.height)
            pygame.draw.rect(self.screen, (72, 198, 152), prog_fill, border_radius=5)

            if self.last_result and self.last_result.actions:
                acts = [a.value.replace("SWITCH_CUBE", "SW") for a in self.last_result.actions]
                start_i = max(0, self.replay_idx - 2)
                snippet = acts[start_i : start_i + 5]
                seq_str = " > ".join(snippet)
                if start_i + 5 < len(acts):
                    seq_str += " ..."
            else:
                seq_str = "Solved Path Ready"
        else:
            seq_str = "Run a solver or benchmark to animate path"

        seq_surf = self.font_tiny.render(seq_str, True, COLOR_TEXT_MUTED)
        self.screen.blit(seq_surf, (inner_x, y_rep + 82))

        # 5. Performance Metrics Card
        y_met = 466
        avail_h_met = max(160, self.screen_height - y_met - 104)
        met_card = pygame.Rect(sb_x, y_met, card_w, 172)
        draw_pastel_card(self.screen, met_card, bg_color=(255, 255, 255), border_color=COLOR_CARD_BORDER, radius=16)
        met_hdr = self.font_section.render("Algorithm Telemetry", True, COLOR_TEXT)
        self.screen.blit(met_hdr, (inner_x, y_met + 8))

        status_pill = pygame.Rect(met_card.right - 98, y_met + 7, 84, 22)
        if self.last_result:
            ok = self.last_result.success
            st_bg = (214, 248, 230) if ok else (255, 220, 226)
            st_col = (28, 134, 82) if ok else (188, 48, 72)
            st_txt = f"{self.last_result.algorithm} OK" if ok else "FAILED"
        else:
            st_bg = (238, 234, 248)
            st_col = COLOR_TEXT_MUTED
            st_txt = "MANUAL"
        pygame.draw.rect(self.screen, st_bg, status_pill, border_radius=8)
        st_surf = self.font_tiny.render(st_txt, True, st_col)
        self.screen.blit(st_surf, st_surf.get_rect(center=status_pill.center))

        r = self.last_result
        metrics_rows = [
            ("Current Move", f"{self.move_count}"),
            ("Solution Moves", f"{r.solution_length} steps (cost {r.solution_cost:.1f})" if (r and r.success) else "-"),
            ("Search Time", f"{r.search_time * 1000:.2f} ms" if r else "-"),
            ("Peak Memory", f"{r.peak_memory_kb:.2f} KB" if r else "-"),
            ("Nodes Exp / Gen", f"{r.expanded_nodes} / {r.generated_nodes}" if r else "-"),
            ("Block State", "SPLIT (2 Cubes)" if (self.state and self.state.block.is_split) else (self.state.block.orientation.value.upper() if self.state else "-")),
        ]
        for i, (k_label, v_val) in enumerate(metrics_rows):
            ry = y_met + 34 + i * 22
            if i % 2 == 0:
                row_bg = pygame.Rect(inner_x - 2, ry - 1, card_w - 12, 20)
                pygame.draw.rect(self.screen, (248, 245, 255), row_bg, border_radius=5)
            k_surf = self.font_tiny.render(k_label, True, COLOR_TEXT_MUTED)
            v_surf = self.font_metric.render(v_val, True, COLOR_TEXT)
            self.screen.blit(k_surf, (inner_x + 4, ry + 1))
            self.screen.blit(v_surf, (met_card.right - v_surf.get_width() - 14, ry + 1))

        # 6. Cute Controls & Camera Shortcuts Card
        y_hk = y_met + 180
        hk_card = pygame.Rect(sb_x, y_hk, card_w, 92)
        draw_pastel_card(self.screen, hk_card, bg_color=COLOR_CARD_ALT_BG, border_color=(244, 214, 206), radius=14)
        hk_lines = [
            "Controls & 3D Camera Shortcuts:",
            "• Arrows: Roll  |  Space: Cube  |  M: 3D/2D",
            "• Drag LMB: Pan |  Drag RMB / Q,E,W,S: Orbit",
            "• Scroll Wheel / +/-: Zoom      |  C: Center",
        ]
        for i, line in enumerate(hk_lines):
            font = self.font_bold if i == 0 else self.font_tiny
            col = COLOR_TEXT if i == 0 else COLOR_TEXT_MUTED
            surf = font.render(line, True, col)
            self.screen.blit(surf, (inner_x, y_hk + 6 + i * 20))

    # ========================================================================
    # MAIN APPLICATION LOOP
    # ========================================================================

    def run(self):
        """Main application game loop with delta-time animations & interactive 3D/2D camera controls."""
        while self.running:
            dt_ms = self.clock.tick(FPS)
            dt_sec = dt_ms / 1000.0
            self.anim_time += dt_sec

            if self.anim_progress < 1.0:
                self.anim_progress = min(1.0, self.anim_progress + dt_sec / max(0.01, self.anim_duration))

            # Advance death animation timer
            if self.death_anim_t >= 0:
                self.death_anim_t += dt_sec
                if self.death_anim_t >= DEATH_ANIM_DURATION:
                    self.death_anim_t = DEATH_ANIM_DURATION

            # Advance level-swipe transition timer
            if self.level_transition_t >= 0:
                mid = LEVEL_TRANSITION_DURATION * 0.5
                was_before_mid = self.level_transition_t < mid
                self.level_transition_t += dt_sec
                now_at_or_past_mid = self.level_transition_t >= mid
                if was_before_mid and now_at_or_past_mid:
                    self._finish_level_transition()
                if self.level_transition_t >= LEVEL_TRANSITION_DURATION:
                    self.level_transition_t = -1.0

            # Check asynchronous worker queue
            if not self.async_worker_queue.empty():
                payload = self.async_worker_queue.get_nowait()
                task_kind = payload[0]
                self.is_waiting = False
                if task_kind == "single":
                    _, solver, result = payload
                    self._on_single_solver_completed(solver, result)
                elif task_kind == "benchmark":
                    _, results = payload
                    self._on_benchmark_completed(results)

            mouse_pos = pygame.mouse.get_pos()

            # Handle replay animation timer
            if self.is_replaying and self.replay_states:
                self.replay_timer += dt_ms
                if self.replay_timer >= self.replay_interval:
                    self.replay_timer = 0
                    if self.replay_idx < len(self.replay_states) - 1:
                        self.replay_idx += 1
                        self._trigger_state_transition(
                            self.replay_states[self.replay_idx],
                            duration=min(MOVE_ANIM_DURATION, self.replay_interval / 1000.0 * 0.85),
                        )
                        self.move_count = self.replay_idx
                        self.is_won = self.state.is_goal(self.env.board)
                    else:
                        self.is_replaying = False
                        self.btn_replay_toggle.text = "Play"

            # EVENT PROCESSING
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.recompute_layout(event.w, event.h)
                    continue

                # 1. Waiting screen event interception
                if self.is_waiting:
                    if self.btn_wait_cancel and self.btn_wait_cancel.handle_event(event):
                        continue
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.cancel_waiting()
                        continue
                    # Swallow other clicks while solving
                    continue

                # 2. Benchmark modal event interception
                if self.benchmark_modal:
                    if self.benchmark_modal.handle_event(event):
                        continue

                # 3. Stage dropdown event interception
                if self.stage_dropdown and self.stage_dropdown.handle_event(event, self.screen.get_rect()):
                    continue

                # 4. View mode switch
                if self.mode_switch and self.mode_switch.handle_event(event):
                    continue

                # 5. Buttons handling (camera buttons ignored during level transition)
                btn_clicked = False
                is_transitioning = (self.level_transition_t >= 0)
                for btn in self.buttons:
                    if is_transitioning and btn in self.cam_buttons:
                        continue
                    if btn.handle_event(event):
                        btn_clicked = True
                        break
                if btn_clicked:
                    continue

                # 6. Mouse Drag Pan & 3D Orbit (only when not transitioning)
                if event.type == pygame.MOUSEBUTTONDOWN and hasattr(event, "pos"):
                    if self.board_area.collidepoint(event.pos) and not is_transitioning:
                        mods = pygame.key.get_mods() if hasattr(pygame, "key") and hasattr(pygame.key, "get_mods") else 0
                        shift_held = bool(mods & getattr(pygame, "KMOD_SHIFT", 1))
                        if event.button == 1 and not shift_held:
                            self.is_panning = True
                            self.last_mouse_pos = event.pos
                        elif event.button == 2:
                            self.is_panning = True
                            self.last_mouse_pos = event.pos
                        elif event.button == 3 or (event.button == 1 and shift_held):
                            self.is_orbiting = True
                            self.last_mouse_pos = event.pos
                        elif event.button == 4:
                            self.renderer.zoom_camera(1.12, pivot=event.pos)
                        elif event.button == 5:
                            self.renderer.zoom_camera(1.0 / 1.12, pivot=event.pos)

                elif event.type == getattr(pygame, "MOUSEBUTTONUP", None):
                    if event.button in (1, 2):
                        self.is_panning = False
                        self.is_orbiting = False
                    elif event.button == 3:
                        self.is_orbiting = False

                elif event.type == getattr(pygame, "MOUSEMOTION", None) and hasattr(event, "pos"):
                    if self.is_panning and not is_transitioning:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]
                        self.renderer.pan_camera(dx, dy)
                        self.last_mouse_pos = event.pos
                    elif self.is_orbiting and not is_transitioning:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]
                        self.renderer.orbit_camera(dx * 0.45, dy * 0.35)
                        self.last_mouse_pos = event.pos

                elif event.type == getattr(pygame, "MOUSEWHEEL", None) and not is_transitioning:
                    wy = getattr(event, "y", 0)
                    if wy > 0:
                        self.renderer.zoom_camera(1.12, pivot=mouse_pos)
                    elif wy < 0:
                        self.renderer.zoom_camera(1.0 / 1.12, pivot=mouse_pos)

                # 7. Keyboard Shortcuts
                elif event.type == pygame.KEYDOWN and not is_transitioning:
                    if event.key == pygame.K_UP:
                        self.handle_manual_move(Direction.UP)
                    elif event.key == pygame.K_DOWN:
                        self.handle_manual_move(Direction.DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.handle_manual_move(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.handle_manual_move(Direction.RIGHT)
                    elif event.key == pygame.K_SPACE:
                        self.handle_manual_move(Direction.SWITCH_CUBE)
                    elif event.key == pygame.K_r:
                        self.restart_stage()
                    elif event.key == pygame.K_n:
                        self.next_stage()
                    elif event.key == pygame.K_p:
                        self.prev_stage()
                    elif event.key in (pygame.K_m, pygame.K_v, pygame.K_TAB):
                        self.toggle_view_mode()
                    elif event.key == getattr(pygame, "K_q", 113):
                        self.renderer.orbit_camera(-15.0, 0.0)
                    elif event.key == getattr(pygame, "K_e", 101):
                        self.renderer.orbit_camera(15.0, 0.0)
                    elif event.key == getattr(pygame, "K_w", 119):
                        self.renderer.orbit_camera(0.0, 8.0)
                    elif event.key == getattr(pygame, "K_s", 115):
                        self.renderer.orbit_camera(0.0, -8.0)
                    elif event.key in (getattr(pygame, "K_EQUALS", 61), getattr(pygame, "K_PLUS", 43), getattr(pygame, "K_KP_PLUS", 270)):
                        self.renderer.zoom_camera(1.15)
                    elif event.key in (getattr(pygame, "K_MINUS", 45), getattr(pygame, "K_KP_MINUS", 269)):
                        self.renderer.zoom_camera(1.0 / 1.15)
                    elif event.key in (getattr(pygame, "K_c", 99), getattr(pygame, "K_HOME", 278)):
                        self.renderer.reset_camera()

            # Hover updates
            if self.is_waiting and self.btn_wait_cancel:
                self.btn_wait_cancel.update(mouse_pos)
            elif self.benchmark_modal:
                self.benchmark_modal.update(mouse_pos)
            else:
                if self.stage_dropdown:
                    self.stage_dropdown.update(mouse_pos)
                if self.mode_switch:
                    self.mode_switch.update(mouse_pos)
                is_trans = (self.level_transition_t >= 0)
                for btn in self.buttons:
                    if is_trans and btn in self.cam_buttons:
                        btn.is_hovered = False
                    else:
                        btn.update(mouse_pos)

            self.render_frame()
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)
