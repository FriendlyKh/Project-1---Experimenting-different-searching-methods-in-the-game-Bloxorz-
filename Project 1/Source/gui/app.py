"""
Main Pygame GUI Application for Bloxorz.
Assigned to: Member 4 (GUI & Visualization)

Handles user input, game state loop, stage switching, solver execution,
and animated solution replay.
"""

import sys
from pathlib import Path
from typing import List, Optional
import pygame

from ..config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SIDEBAR_WIDTH,
    FPS,
    COLOR_BG,
    COLOR_PANEL_BG,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    STAGES_DIR,
)
from ..game.constants import Direction
from ..game.stage_loader import StageLoader
from ..game.environment import BloxorzEnv
from ..game.state import GameState
from ..solvers.bfs import BFSSolver
from ..solvers.dfs import DFSSolver
from ..solvers.ucs import UCSSolver
from ..solvers.astar import AStarSolver
from ..solvers.base import SearchResult
from .renderer import GameRenderer
from .widgets import Button


class BloxorzApp:
    """
    Interactive GUI application for Bloxorz.
    """

    def __init__(self, stages_dir: Optional[Path] = None):
        pygame.init()
        pygame.display.set_caption("Bloxorz Solver - CSC14003 AI Project")
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_main = pygame.font.SysFont("Arial", 16)
        self.font_title = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_metric = pygame.font.SysFont("Courier New", 14)

        # Stage management
        self.stages_dir = stages_dir or STAGES_DIR
        self.stage_files = sorted(list(self.stages_dir.glob("*.json")))
        if not self.stage_files:
            raise RuntimeError(f"No stage JSON files found in {self.stages_dir}")
        self.current_stage_idx = 0

        # Layout Areas
        self.board_area = pygame.Rect(0, 0, SCREEN_WIDTH - SIDEBAR_WIDTH, SCREEN_HEIGHT)
        self.sidebar_area = pygame.Rect(SCREEN_WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)

        self.renderer = GameRenderer(self.screen, self.board_area)

        # Game state
        self.env: BloxorzEnv = None
        self.state: GameState = None
        self.is_won = False
        self.is_lost = False
        self.move_count = 0

        # Solvers & Replay
        self.last_result: Optional[SearchResult] = None
        self.replay_states: List[GameState] = []
        self.replay_idx = 0
        self.is_replaying = False
        self.replay_timer = 0
        self.replay_interval = 350  # milliseconds per step

        # Initialize buttons
        self.buttons: List[Button] = []
        self._init_buttons()

        # Load initial stage
        self.load_stage(self.current_stage_idx)

    def _init_buttons(self):
        """Constructs interactive sidebar buttons."""
        sb_x = self.sidebar_area.left + 20
        w = self.sidebar_area.width - 40
        h = 34

        # Stage Switchers
        self.btn_prev_stage = Button(
            rect=(sb_x, 70, w // 2 - 5, h),
            text="< Prev",
            on_click=self.prev_stage,
        )
        self.btn_next_stage = Button(
            rect=(sb_x + w // 2 + 5, 70, w // 2 - 5, h),
            text="Next >",
            on_click=self.next_stage,
        )

        # Restart
        self.btn_restart = Button(
            rect=(sb_x, 115, w, h),
            text="Restart Stage (R)",
            on_click=self.restart_stage,
            bg_color=(160, 60, 60),
            hover_color=(190, 80, 80),
        )

        # Solvers
        y_solvers = 195
        self.btn_bfs = Button(
            rect=(sb_x, y_solvers, w, h),
            text="Solve BFS",
            on_click=lambda: self.run_solver(BFSSolver()),
            bg_color=(45, 90, 160),
            hover_color=(60, 115, 200),
        )
        self.btn_dfs = Button(
            rect=(sb_x, y_solvers + 42, w, h),
            text="Solve DFS",
            on_click=lambda: self.run_solver(DFSSolver()),
            bg_color=(45, 90, 160),
            hover_color=(60, 115, 200),
        )
        self.btn_ucs = Button(
            rect=(sb_x, y_solvers + 84, w, h),
            text="Solve UCS",
            on_click=lambda: self.run_solver(UCSSolver()),
            bg_color=(45, 90, 160),
            hover_color=(60, 115, 200),
        )
        self.btn_astar = Button(
            rect=(sb_x, y_solvers + 126, w, h),
            text="Solve A*",
            on_click=lambda: self.run_solver(AStarSolver()),
            bg_color=(35, 130, 95),
            hover_color=(45, 160, 120),
        )

        # Replay Controller
        y_replay = 390
        btn_w3 = (w - 16) // 3
        self.btn_replay_toggle = Button(
            rect=(sb_x, y_replay, btn_w3, h),
            text="Play",
            on_click=self.toggle_replay,
        )
        self.btn_replay_step = Button(
            rect=(sb_x + btn_w3 + 8, y_replay, btn_w3, h),
            text="Step >",
            on_click=self.step_forward_replay,
        )
        self.btn_replay_reset = Button(
            rect=(sb_x + 2 * (btn_w3 + 8), y_replay, btn_w3, h),
            text="Reset",
            on_click=self.reset_replay,
        )

        self.buttons = [
            self.btn_prev_stage,
            self.btn_next_stage,
            self.btn_restart,
            self.btn_bfs,
            self.btn_dfs,
            self.btn_ucs,
            self.btn_astar,
            self.btn_replay_toggle,
            self.btn_replay_step,
            self.btn_replay_reset,
        ]

    def load_stage(self, idx: int):
        """Loads stage at index."""
        self.current_stage_idx = idx % len(self.stage_files)
        stage_file = self.stage_files[self.current_stage_idx]
        board = StageLoader.load_from_file(stage_file)
        self.env = BloxorzEnv(board)
        self.restart_stage()

    def restart_stage(self):
        """Resets the current stage to start state."""
        self.state = self.env.get_initial_state()
        self.is_won = False
        self.is_lost = False
        self.move_count = 0
        self.last_result = None
        self.replay_states = []
        self.replay_idx = 0
        self.is_replaying = False
        self.btn_replay_toggle.text = "Play"

    def next_stage(self):
        self.load_stage(self.current_stage_idx + 1)

    def prev_stage(self):
        self.load_stage(self.current_stage_idx - 1)

    def run_solver(self, solver):
        """
        Runs the chosen search solver and loads the solution path for replay.
        
        Guidelines for Member 4:
        1. Call `result = solver.solve(self.env)`.
        2. Store `self.last_result = result`.
        3. If `result.success`:
           Set `self.replay_states = result.states`, reset replay index, and start playback.
        """
        # TODO [Member 4]: Connect solver execution to replay controller and metrics.
        raise NotImplementedError("Member 4: Implement run_solver handler.")

    def toggle_replay(self):
        """Toggles between Play and Pause during solution replay."""
        if not self.replay_states:
            return
        self.is_replaying = not self.is_replaying
        self.btn_replay_toggle.text = "Pause" if self.is_replaying else "Play"

    def step_forward_replay(self):
        """Steps forward one move in the solution sequence."""
        # TODO [Member 4]: Implement single-step forward in replay.
        raise NotImplementedError("Member 4: Implement step_forward_replay.")

    def reset_replay(self):
        """Resets replay back to the initial step."""
        if not self.replay_states:
            return
        self.is_replaying = False
        self.btn_replay_toggle.text = "Play"
        self.replay_idx = 0
        self.state = self.replay_states[0]
        self.move_count = 0
        self.is_won = False

    def handle_manual_move(self, direction: Direction):
        """
        Processes keyboard move from human player (Arrow keys, Spacebar).
        
        Guidelines for Member 4:
        1. Call `next_state = self.env.step(self.state, direction)`.
        2. If `next_state is None`: set `self.is_lost = True` (block fell off).
        3. Else: update `self.state = next_state`, increment `self.move_count`,
           and check `self.is_won = self.state.is_goal(self.env.board)`.
        """
        # TODO [Member 4]: Implement manual keyboard roll handling and win/loss state updates.
        raise NotImplementedError("Member 4: Implement handle_manual_move.")

    def run(self):
        """Main application game loop."""
        while self.running:
            dt = self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()

            # Handle replay animation timer
            if self.is_replaying and self.replay_states:
                self.replay_timer += dt
                if self.replay_timer >= self.replay_interval:
                    self.replay_timer = 0
                    if self.replay_idx < len(self.replay_states) - 1:
                        self.replay_idx += 1
                        self.state = self.replay_states[self.replay_idx]
                        self.move_count = self.replay_idx
                        self.is_won = self.state.is_goal(self.env.board)
                    else:
                        self.is_replaying = False
                        self.btn_replay_toggle.text = "Play"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                for btn in self.buttons:
                    btn.handle_event(event)

                if event.type == pygame.KEYDOWN:
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

            for btn in self.buttons:
                btn.update(mouse_pos)

            self.screen.fill(COLOR_BG)
            self.renderer.draw(self.env.board, self.state, self.is_won, self.is_lost)
            self._draw_sidebar()

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)

    def _draw_sidebar(self):
        """Renders the UI sidebar controls, instructions, and metrics."""
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.sidebar_area)
        pygame.draw.line(self.screen, (60, 65, 85), self.sidebar_area.topleft, self.sidebar_area.bottomleft, 2)

        sb_x = self.sidebar_area.left + 20

        # Title
        title_surf = self.font_title.render("Bloxorz Solver", True, COLOR_TEXT)
        self.screen.blit(title_surf, (sb_x, 15))

        stage_name = self.stage_files[self.current_stage_idx].stem
        stage_surf = self.font_main.render(f"Stage: {stage_name}", True, COLOR_TEXT_MUTED)
        self.screen.blit(stage_surf, (sb_x, 42))

        # Solvers Header
        solv_header = self.font_title.render("Algorithms", True, COLOR_TEXT)
        self.screen.blit(solv_header, (sb_x, 165))

        # Replay Header
        rep_header = self.font_title.render("Solution Replay", True, COLOR_TEXT)
        self.screen.blit(rep_header, (sb_x, 360))

        # Draw all buttons
        for btn in self.buttons:
            btn.draw(self.screen)

        # Metrics Panel
        y_metrics = 445
        pygame.draw.rect(self.screen, (25, 27, 35), (sb_x, y_metrics, self.sidebar_area.width - 40, 140), border_radius=6)
        pygame.draw.rect(self.screen, (60, 65, 85), (sb_x, y_metrics, self.sidebar_area.width - 40, 140), width=1, border_radius=6)

        m_lines = [
            f"Moves: {self.move_count}",
        ]
        if self.last_result:
            r = self.last_result
            m_lines.append(f"Solver: {r.algorithm} ({'OK' if r.success else 'FAIL'})")
            m_lines.append(f"Sol Length: {r.solution_length} steps")
            m_lines.append(f"Time: {r.search_time * 1000:.1f} ms")
            m_lines.append(f"Memory: {r.peak_memory_kb:.1f} KB")
            m_lines.append(f"Expanded: {r.expanded_nodes}")
        else:
            m_lines.append("Solver: None")
            m_lines.append("Press a solver button to run.")

        for i, line in enumerate(m_lines):
            line_surf = self.font_metric.render(line, True, (210, 220, 240))
            self.screen.blit(line_surf, (sb_x + 10, y_metrics + 8 + i * 21))

        # Instructions / Hotkeys
        y_inst = 600
        inst_lines = [
            "Manual Controls:",
            "• Arrow Keys: Roll block",
            "• Space: Switch split cube",
            "• R: Restart | N: Next | P: Prev",
        ]
        for i, line in enumerate(inst_lines):
            surf = self.font_main.render(line, True, COLOR_TEXT_MUTED)
            self.screen.blit(surf, (sb_x, y_inst + i * 20))
