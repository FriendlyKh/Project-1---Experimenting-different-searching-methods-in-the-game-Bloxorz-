"""
Main Pygame GUI Application for Bloxorz.
Assigned to: Member 4 (GUI & Visualization)

Features a cute & bright pastel UI with:
- Dual View Modes: '2.5D' (Rotatable 3D / 2.5D Diorama Viewpoint) and '2D' (Algorithm Vis Viewpoint)
- Smooth Block Roll, Parabolic Hop, Split-Teleport, and Ambient Animations
- Interactive Mouse Drag Panning (LMB/MMB), 3D Viewpoint Orbiting (RMB or Shift+LMB), and Scroll Wheel Zoom
- Floating Camera Control Toolbar on the Playmat Canvas (+Zoom, -Zoom, Orbit L/R, Tilt, Reset Cam)
- Real-time AI solver execution (BFS, DFS, UCS, A*) with explored-cell heatmap tracking
"""

import sys
from collections import deque
from pathlib import Path
from typing import List, Optional, Dict, Tuple
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
from .widgets import Button, ModeToggleSwitch, draw_pastel_card


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

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_title = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 22, bold=True)
        self.font_section = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 15, bold=True)
        self.font_main = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 14, bold=False)
        self.font_bold = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 14, bold=True)
        self.font_metric = pygame.font.SysFont("Consolas, Courier New, Monospace", 13, bold=True)
        self.font_tiny = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 12, bold=False)

        # Stage management
        self.stages_dir = stages_dir or STAGES_DIR
        self.stage_files = sorted(self.stages_dir.glob("*.json"), key=_stage_sort_key)
        if not self.stage_files:
            raise RuntimeError(f"No stage JSON files found in {self.stages_dir}")
        self.current_stage_idx = 0

        # Layout Areas
        self.board_area = pygame.Rect(0, 0, SCREEN_WIDTH - SIDEBAR_WIDTH, SCREEN_HEIGHT)
        self.sidebar_area = pygame.Rect(SCREEN_WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)

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

        # ── Death animation ──────────────────────────────────────────────────
        # Counts from 0 → DEATH_ANIM_DURATION while playing; resets to -1 when idle.
        self.death_anim_t: float = -1.0

        # ── Level-swipe transition ───────────────────────────────────────────
        # Counts from 0 → LEVEL_TRANSITION_DURATION; direction: +1 = swipe left (next),
        # -1 = swipe right (prev).  -1.0 means no transition is playing.
        self.level_transition_t: float = -1.0
        self.level_transition_dir: int = 1           # +1 or -1
        self._pending_stage_idx: Optional[int] = None  # stage to load after swipe-out

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

        # Initialize UI controls
        self.buttons: List[Button] = []
        self.cam_buttons: List[Button] = []
        self.mode_switch: Optional[ModeToggleSwitch] = None
        self._init_widgets()

        # Load initial stage
        self.load_stage(self.current_stage_idx)

    def _init_widgets(self):
        """Constructs cute pastel sidebar buttons, mode switch, and floating camera HUD buttons."""
        sb_x = self.sidebar_area.left + 22
        w = self.sidebar_area.width - 44
        h = 34

        # 1. Stage Navigation & Restart
        btn_w3 = (w - 16) // 3
        self.btn_prev_stage = Button(
            rect=(sb_x, 88, btn_w3, h),
            text="< Prev",
            on_click=self.prev_stage,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=14,
        )
        self.btn_restart = Button(
            rect=(sb_x + btn_w3 + 8, 88, btn_w3, h),
            text="Reset (R)",
            on_click=self.restart_stage,
            bg_color=BTN_CORAL[0],
            hover_color=BTN_CORAL[1],
            shadow_color=BTN_CORAL[2],
            text_color=BTN_CORAL[3],
            font_size=14,
        )
        self.btn_next_stage = Button(
            rect=(sb_x + 2 * (btn_w3 + 8), 88, btn_w3, h),
            text="Next >",
            on_click=self.next_stage,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=14,
        )

        # 2. View Mode Segmented Switch (3D/2.5D Cute Block vs 2D Algo Vis)
        self.mode_switch = ModeToggleSwitch(
            rect=(sb_x, 162, w, 38),
            mode=self.view_mode,
            on_change=self.set_view_mode,
        )

        # 3. AI Search Solvers (2x2 Cute Tactile Grid)
        y_solv = 244
        half_w = (w - 10) // 2
        solv_h = 38
        self.btn_bfs = Button(
            rect=(sb_x, y_solv, half_w, solv_h),
            text="Solve BFS",
            on_click=lambda: self.run_solver(BFSSolver()),
            bg_color=BTN_PRIMARY[0],
            hover_color=BTN_PRIMARY[1],
            shadow_color=BTN_PRIMARY[2],
            text_color=BTN_PRIMARY[3],
            font_size=14,
        )
        self.btn_dfs = Button(
            rect=(sb_x + half_w + 10, y_solv, half_w, solv_h),
            text="Solve DFS",
            on_click=lambda: self.run_solver(DFSSolver()),
            bg_color=BTN_LAVENDER[0],
            hover_color=BTN_LAVENDER[1],
            shadow_color=BTN_LAVENDER[2],
            text_color=BTN_LAVENDER[3],
            font_size=14,
        )
        self.btn_ucs = Button(
            rect=(sb_x, y_solv + 46, half_w, solv_h),
            text="Solve UCS",
            on_click=lambda: self.run_solver(UCSSolver(cost_fn=custom_cost_function)),
            bg_color=BTN_SUNNY[0],
            hover_color=BTN_SUNNY[1],
            shadow_color=BTN_SUNNY[2],
            text_color=BTN_SUNNY[3],
            font_size=14,
        )
        self.btn_astar = Button(
            rect=(sb_x + half_w + 10, y_solv + 46, half_w, solv_h),
            text="Solve A*",
            on_click=lambda: self.run_solver(AStarSolver(heuristic_fn=orientation_aware_heuristic)),
            bg_color=BTN_MINT[0],
            hover_color=BTN_MINT[1],
            shadow_color=BTN_MINT[2],
            text_color=BTN_MINT[3],
            font_size=14,
        )

        # 4. Replay Controller Buttons (Play/Pause, < Step, Step >, Start)
        y_rep = 374
        btn_w4 = (w - 18) // 4
        self.btn_replay_toggle = Button(
            rect=(sb_x, y_rep, btn_w4, 34),
            text="Play",
            on_click=self.toggle_replay,
            bg_color=BTN_MINT[0],
            hover_color=BTN_MINT[1],
            shadow_color=BTN_MINT[2],
            text_color=BTN_MINT[3],
            font_size=13,
        )
        self.btn_replay_prev = Button(
            rect=(sb_x + (btn_w4 + 6), y_rep, btn_w4, 34),
            text="< Step",
            on_click=self.step_backward_replay,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=13,
        )
        self.btn_replay_step = Button(
            rect=(sb_x + 2 * (btn_w4 + 6), y_rep, btn_w4, 34),
            text="Step >",
            on_click=self.step_forward_replay,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=13,
        )
        self.btn_replay_reset = Button(
            rect=(sb_x + 3 * (btn_w4 + 6), y_rep, btn_w4, 34),
            text="Start",
            on_click=self.reset_replay,
            bg_color=BTN_NEUTRAL[0],
            hover_color=BTN_NEUTRAL[1],
            shadow_color=BTN_NEUTRAL[2],
            text_color=BTN_NEUTRAL[3],
            font_size=13,
        )

        # 5. Floating Camera Toolbar Buttons inside Playmat Bottom-Right
        cam_y = self.board_area.bottom - 94
        cam_right = self.board_area.right - 36
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

        self.cam_buttons = [
            self.btn_cam_zoom_in,
            self.btn_cam_zoom_out,
            self.btn_cam_orbit_l,
            self.btn_cam_orbit_r,
            self.btn_cam_tilt,
            self.btn_cam_reset,
        ]

        self.buttons = [
            self.btn_prev_stage,
            self.btn_restart,
            self.btn_next_stage,
            self.btn_bfs,
            self.btn_dfs,
            self.btn_ucs,
            self.btn_astar,
            self.btn_replay_toggle,
            self.btn_replay_prev,
            self.btn_replay_step,
            self.btn_replay_reset,
        ] + self.cam_buttons

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
        # Prevent double-triggering while a transition is already running
        if self.level_transition_t >= 0:
            return
        self._pending_stage_idx = target_idx % len(self.stage_files)
        self.level_transition_dir = direction
        self.level_transition_t = 0.0  # starts the timer
        # Give the renderer the name it should display in the swipe panel
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

    def _compute_explored_cells(self, max_states: int, path_states: List[GameState]) -> Dict[Tuple[int, int], int]:
        """Builds a cell visitation map `(r, c) -> order` for the search space heatmap."""
        explored: Dict[Tuple[int, int], int] = {}
        init_state = self.env.get_initial_state()
        queue = deque([init_state])
        visited = {init_state}
        step_counter = 0

        while queue and len(visited) <= max(12, max_states):
            curr = queue.popleft()
            step_counter += 1
            for cell in curr.block.occupied_cells():
                if cell not in explored:
                    explored[cell] = step_counter
            for _, nxt, _ in self.env.get_successors(curr):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

        for st in path_states:
            step_counter += 1
            for cell in st.block.occupied_cells():
                if cell not in explored:
                    explored[cell] = step_counter

        return explored

    def run_solver(self, solver) -> None:
        """Runs the chosen search solver and starts animated solution playback."""
        result = solver.solve(self.env)
        self.last_result = result

        solver_btn_map = {
            "BFS": self.btn_bfs,
            "DFS": self.btn_dfs,
            "UCS": self.btn_ucs,
            "A*": self.btn_astar,
        }
        for name, btn in solver_btn_map.items():
            btn.is_active = (name == solver.name)

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
            self.death_anim_t = 0.0   # ← kick off death animation
            # Animate the block actually tumbling in the direction it was rolled!
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



    def render_frame(self):
        """Renders the complete current frame (board + floating camera buttons + sidebar)."""
        self.screen.fill(COLOR_BG)
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
        )
        for c_btn in self.cam_buttons:
            c_btn.draw(self.screen)
        self._draw_sidebar()


    def run(self):
        """Main application game loop with delta-time animations & interactive 3D/2D camera controls."""
        while self.running:
            dt_ms = self.clock.tick(FPS)
            dt_sec = dt_ms / 1000.0
            self.anim_time += dt_sec

            if self.anim_progress < 1.0:
                self.anim_progress = min(1.0, self.anim_progress + dt_sec / max(0.01, self.anim_duration))

            # ── Advance death animation timer ────────────────────────────────
            if self.death_anim_t >= 0:
                self.death_anim_t += dt_sec
                if self.death_anim_t >= DEATH_ANIM_DURATION:
                    self.death_anim_t = DEATH_ANIM_DURATION  # clamp; overlay stays visible

            # ── Advance level-swipe transition timer ─────────────────────────
            if self.level_transition_t >= 0:
                mid = LEVEL_TRANSITION_DURATION * 0.5
                was_before_mid = self.level_transition_t < mid
                self.level_transition_t += dt_sec
                now_at_or_past_mid = self.level_transition_t >= mid
                # At the exact mid-point: swap the stage content
                if was_before_mid and now_at_or_past_mid:
                    self._finish_level_transition()
                if self.level_transition_t >= LEVEL_TRANSITION_DURATION:
                    self.level_transition_t = -1.0  # transition complete

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

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if self.mode_switch and self.mode_switch.handle_event(event):
                    continue

                btn_clicked = False
                for btn in self.buttons:
                    if btn.handle_event(event):
                        btn_clicked = True
                        break
                if btn_clicked:
                    continue

                # Mouse Drag Pan (Left/Middle Click) & 3D Viewpoint Orbit (Right Click or Shift+Left Click)
                if event.type == pygame.MOUSEBUTTONDOWN and hasattr(event, "pos"):
                    if self.board_area.collidepoint(event.pos):
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
                        elif event.button == 4:  # Scroll wheel up
                            self.renderer.zoom_camera(1.12, pivot=event.pos)
                        elif event.button == 5:  # Scroll wheel down
                            self.renderer.zoom_camera(1.0 / 1.12, pivot=event.pos)

                elif event.type == getattr(pygame, "MOUSEBUTTONUP", None):
                    if event.button in (1, 2):
                        self.is_panning = False
                        self.is_orbiting = False
                    elif event.button == 3:
                        self.is_orbiting = False

                elif event.type == getattr(pygame, "MOUSEMOTION", None) and hasattr(event, "pos"):
                    if self.is_panning:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]
                        self.renderer.pan_camera(dx, dy)
                        self.last_mouse_pos = event.pos
                    elif self.is_orbiting:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]
                        self.renderer.orbit_camera(dx * 0.45, dy * 0.35)
                        self.last_mouse_pos = event.pos

                elif event.type == getattr(pygame, "MOUSEWHEEL", None):
                    wy = getattr(event, "y", 0)
                    if wy > 0:
                        self.renderer.zoom_camera(1.12, pivot=mouse_pos)
                    elif wy < 0:
                        self.renderer.zoom_camera(1.0 / 1.12, pivot=mouse_pos)

                elif event.type == pygame.KEYDOWN:
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

            if self.mode_switch:
                self.mode_switch.update(mouse_pos)
            for btn in self.buttons:
                btn.update(mouse_pos)

            self.render_frame()
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)

    def _draw_sidebar(self):
        """Renders the cute & bright pastel sidebar with organized cards, progress bar, and metrics."""
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

        # 1. Header & Stage Selector Card
        stage_card = pygame.Rect(sb_x, 12, card_w, 120)
        draw_pastel_card(self.screen, stage_card, bg_color=COLOR_CARD_ALT_BG, border_color=(244, 214, 206), radius=16)

        title_surf = self.font_title.render("Bloxorz AI Studio", True, COLOR_TEXT_ACCENT)
        self.screen.blit(title_surf, (inner_x, 20))

        stage_name = self._get_stage_display_name(self.current_stage_idx)
        stage_pill = pygame.Rect(inner_x, 52, card_w - 16, 26)
        pygame.draw.rect(self.screen, (255, 255, 255), stage_pill, border_radius=8)
        pygame.draw.rect(self.screen, (238, 206, 198), stage_pill, width=1, border_radius=8)
        stage_lbl = self.font_bold.render(
            f"{stage_name}  ({self.current_stage_idx + 1}/{len(self.stage_files)})",
            True,
            COLOR_TEXT,
        )
        self.screen.blit(stage_lbl, stage_lbl.get_rect(center=stage_pill.center))

        # 2. View Mode Switcher Card (3D/2.5D vs 2D Algo Vis)
        mode_card = pygame.Rect(sb_x, 138, card_w, 70)
        draw_pastel_card(self.screen, mode_card, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER, radius=16)
        mode_hdr = self.font_tiny.render("VIEWPOINT & VISUALIZATION MODE (KEY: M)", True, COLOR_TEXT_MUTED)
        self.screen.blit(mode_hdr, (inner_x, 144))
        if self.mode_switch:
            self.mode_switch.draw(self.screen)

        # 3. AI Search Solvers Card
        solv_card = pygame.Rect(sb_x, 216, card_w, 122)
        draw_pastel_card(self.screen, solv_card, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER, radius=16)
        solv_hdr = self.font_section.render("Search Algorithms", True, COLOR_TEXT)
        self.screen.blit(solv_hdr, (inner_x, 222))

        # 4. Replay & Trajectory Controller Card
        rep_card = pygame.Rect(sb_x, 346, card_w, 114)
        draw_pastel_card(self.screen, rep_card, bg_color=COLOR_CARD_MINT_BG, border_color=(196, 234, 220), radius=16)
        rep_hdr = self.font_section.render("Animated Solution Replay", True, COLOR_TEXT)
        self.screen.blit(rep_hdr, (inner_x, 352))

        for btn in self.buttons:
            if btn not in self.cam_buttons:
                btn.draw(self.screen)

        prog_bg = pygame.Rect(inner_x, 418, card_w - 16, 12)
        pygame.draw.rect(self.screen, (214, 238, 228), prog_bg, border_radius=6)
        if self.replay_states and len(self.replay_states) > 1:
            ratio = self.replay_idx / float(len(self.replay_states) - 1)
            fill_w = max(8, int(prog_bg.width * ratio))
            prog_fill = pygame.Rect(prog_bg.left, prog_bg.top, fill_w, prog_bg.height)
            pygame.draw.rect(self.screen, (72, 198, 152), prog_fill, border_radius=6)

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
            seq_str = "Run a solver above to animate path"

        seq_surf = self.font_tiny.render(seq_str, True, COLOR_TEXT_MUTED)
        self.screen.blit(seq_surf, (inner_x, 435))

        # 5. Performance Metrics Card
        met_card = pygame.Rect(sb_x, 468, card_w, 174)
        draw_pastel_card(self.screen, met_card, bg_color=(255, 255, 255), border_color=COLOR_CARD_BORDER, radius=16)
        met_hdr = self.font_section.render("Algorithm Telemetry", True, COLOR_TEXT)
        self.screen.blit(met_hdr, (inner_x, 475))

        status_pill = pygame.Rect(met_card.right - 98, 474, 84, 22)
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
            ry = 502 + i * 22
            if i % 2 == 0:
                row_bg = pygame.Rect(inner_x - 2, ry - 1, card_w - 12, 20)
                pygame.draw.rect(self.screen, (248, 245, 255), row_bg, border_radius=5)
            k_surf = self.font_tiny.render(k_label, True, COLOR_TEXT_MUTED)
            v_surf = self.font_metric.render(v_val, True, COLOR_TEXT)
            self.screen.blit(k_surf, (inner_x + 4, ry + 1))
            self.screen.blit(v_surf, (met_card.right - v_surf.get_width() - 14, ry + 1))

        # 6. Cute Controls & Camera Shortcuts Card
        hk_card = pygame.Rect(sb_x, 650, card_w, 96)
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
            self.screen.blit(surf, (inner_x, 656 + i * 20))