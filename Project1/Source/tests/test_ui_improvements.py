"""
Tests for new UI improvements:
1. Stage selection dropdown
2. Camera buttons layer order & occlusion during level transitions
3. Flexible screen resize and layout adaptation
4. Benchmark stage runner & BenchmarkModal comparison
5. Asynchronous solver execution and waiting state
"""

import os
import pygame
import pytest
from pathlib import Path

# Ensure headless pygame for automated test execution
os.environ["SDL_VIDEODRIVER"] = "dummy"

from Source.config import STAGES_DIR
from Source.gui.widgets import Dropdown, BenchmarkModal, Button
from Source.gui.renderer import GameRenderer
from Source.game.stage_loader import StageLoader
from Source.game.environment import BloxorzEnv
from Source.solvers.base import SearchResult


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


def test_dropdown_initialization_and_selection():
    items = ["1. Core", "2. Fragile", "3. Bridge", "4. Split"]
    selected = []

    def on_sel(idx):
        selected.append(idx)

    dd = Dropdown(rect=(10, 10, 150, 30), items=items, selected_idx=0, on_select=on_sel)
    assert dd.selected_idx == 0
    assert dd.selected_text == "1. Core"
    assert not dd.is_open

    # Click to open
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (20, 20)})
    handled = dd.handle_event(click_event)
    assert handled is True
    assert dd.is_open is True

    # Click on item 2 ("3. Bridge", which is at index 2)
    # popup_y is rect.bottom + 4 = 44, item_height = 28 -> index 2 is around 44 + 4 + 2 * 28 + 10 = 114
    item_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (50, 48 + 2 * 28 + 10)})
    handled = dd.handle_event(item_click)
    assert handled is True
    assert dd.selected_idx == 2
    assert dd.selected_text == "3. Bridge"
    assert dd.is_open is False
    assert selected == [2]


def test_dropdown_click_outside_closes():
    items = ["A", "B", "C"]
    dd = Dropdown(rect=(10, 10, 100, 30), items=items, selected_idx=0)
    dd.is_open = True

    # Click far away
    click_outside = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (500, 500)})
    handled = dd.handle_event(click_outside)
    assert handled is True
    assert dd.is_open is False


def test_dropdown_mousewheel_scrolling():
    items = [f"Stage {i}" for i in range(20)]
    dd = Dropdown(rect=(10, 10, 100, 30), items=items, selected_idx=0, max_visible_items=5)
    dd.is_open = True
    assert dd.scroll_offset == 0

    # Wheel down event
    wheel_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 5, "pos": (20, 50)})
    handled = dd.handle_event(wheel_event)
    assert handled is True
    assert dd.scroll_offset == 1


def test_benchmark_modal_analysis_and_winner():
    results = [
        {
            "algorithm": "BFS",
            "success": True,
            "moves": 16,
            "cost": 16.0,
            "time_ms": 2.50,
            "peak_mem_kb": 45.0,
            "expanded_nodes": 120,
            "generated_nodes": 240,
            "status": "Solution found",
        },
        {
            "algorithm": "DFS",
            "success": True,
            "moves": 28,
            "cost": 28.0,
            "time_ms": 3.80,
            "peak_mem_kb": 22.0,
            "expanded_nodes": 85,
            "generated_nodes": 150,
            "status": "Solution found",
        },
        {
            "algorithm": "UCS",
            "success": True,
            "moves": 16,
            "cost": 16.0,
            "time_ms": 4.10,
            "peak_mem_kb": 55.0,
            "expanded_nodes": 140,
            "generated_nodes": 290,
            "status": "Solution found",
        },
        {
            "algorithm": "A*",
            "success": True,
            "moves": 16,
            "cost": 16.0,
            "time_ms": 1.10,
            "peak_mem_kb": 30.0,
            "expanded_nodes": 45,
            "generated_nodes": 95,
            "status": "Solution found",
        },
    ]

    replayed = []
    closed = []

    modal = BenchmarkModal(
        stage_name="Stage 01 Core",
        results=results,
        on_replay=lambda algo: replayed.append(algo),
        on_close=lambda: closed.append(True),
    )

    assert modal.best_time == 1.10
    assert modal.best_moves == 16
    assert modal.best_nodes == 45
    assert modal.best_mem == 22.0
    assert modal.winner_algo == "A*"
    assert "A*" in modal.winner_summary

    # Test ESC key closes modal
    esc_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    handled = modal.handle_event(esc_event)
    assert handled is True
    assert closed == [True]


def test_renderer_update_dimensions_and_cam_buttons():
    surf = pygame.Surface((1200, 800))
    board_rect = pygame.Rect(0, 0, 850, 800)
    renderer = GameRenderer(surf, board_rect)

    new_surf = pygame.Surface((1400, 900))
    new_rect = pygame.Rect(0, 0, 1000, 900)
    renderer.update_dimensions(new_surf, new_rect)

    assert renderer.surface == new_surf
    assert renderer.board_area == new_rect

    # Load a board and test that draw() accepts cam_buttons without errors
    stage_file = sorted(STAGES_DIR.glob("*.json"))[0]
    board = StageLoader.load_from_file(stage_file)
    env = BloxorzEnv(board)
    init_st = env.get_initial_state()

    dummy_btn = Button((100, 100, 50, 30), text="CamTest")
    renderer.draw(
        board=board,
        state=init_st,
        level_transition_t=0.5,
        cam_buttons=[dummy_btn],
    )


def test_bloxorz_app_initialization_and_responsive_layout():
    from Source.gui.app import BloxorzApp

    app = BloxorzApp(stages_dir=STAGES_DIR)
    assert app.stage_dropdown is not None
    assert len(app.stage_dropdown.items) == len(app.stage_files)
    assert app.btn_benchmark is not None

    # Test recompute_layout dynamically changes dimensions
    app.recompute_layout(1400, 900)
    assert app.screen_width == 1400
    assert app.screen_height == 900
    assert app.board_area.width == 1400 - app.sidebar_width

    # Verify camera buttons remain in board area
    for c_btn in app.cam_buttons:
        assert app.board_area.contains(c_btn.rect)


def test_bloxorz_app_async_solver_and_benchmark():
    from Source.gui.app import BloxorzApp
    from Source.solvers.bfs import BFSSolver

    app = BloxorzApp(stages_dir=STAGES_DIR)
    assert not app.is_waiting

    # Test starting solver asynchronously
    app.start_solver_async(BFSSolver())
    assert app.is_waiting
    assert app.waiting_task_type == "single"
    assert "BFS" in app.waiting_title

    # Wait for thread to finish
    if app.async_thread:
        app.async_thread.join(timeout=5.0)

    # Process queue payload
    assert not app.async_worker_queue.empty()
    payload = app.async_worker_queue.get_nowait()
    assert payload[0] == "single"
    app._on_single_solver_completed(payload[1], payload[2])
    assert app.last_result is not None
    assert app.last_result.success
    assert len(app.replay_states) > 0
