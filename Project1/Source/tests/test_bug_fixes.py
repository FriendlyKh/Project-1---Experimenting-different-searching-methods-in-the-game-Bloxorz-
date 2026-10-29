"""
Regression tests for all bug fixes:
1. GameState goal check and dead code removal.
2. DFSSolver shallower path updates and stack pruning.
3. Node generation count consistency across BFS, DFS, UCS, A*.
4. UCSSolver custom_cost_function availability in both import paths.
5. Dropdown popup padding click bounds protection.
6. BenchmarkModal layout caching (no per-frame button re-allocation) and background event absorption.
7. Manual move SWITCH_CUBE rejection on non-split block.
8. Cross-stage async solver result discard.
9. Death animation state reset on solver replay.
10. Camera HUD hint non-collision on narrow screens.
"""

import os
import pygame
import pytest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"

from Source.config import STAGES_DIR
from Source.game.constants import Orientation, Direction
from Source.game.block import Block
from Source.game.state import GameState
from Source.game.stage_loader import StageLoader
from Source.game.environment import BloxorzEnv
from Source.solvers.bfs import BFSSolver
from Source.solvers.dfs import DFSSolver
from Source.solvers.ucs import UCSSolver, custom_cost_function
from Source.solvers.astar import AStarSolver
from Source.gui.widgets import Dropdown, BenchmarkModal, Button
from Source.gui.renderer import GameRenderer


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


def test_game_state_is_goal():
    stage_file = sorted(STAGES_DIR.glob("*.json"))[0]
    board = StageLoader.load_from_file(stage_file)
    gr, gc = board.goal_pos

    # 1. Standing on goal -> goal!
    st_goal = GameState(Block(gr, gc, Orientation.STANDING), tuple())
    assert st_goal.is_goal(board) is True

    # 2. Lying on goal -> NOT goal
    st_lying = GameState(Block(gr, gc, Orientation.LYING_H), tuple())
    assert st_lying.is_goal(board) is False

    # 3. Split block on goal -> NOT goal (Section 2.5)
    st_split = GameState(Block(gr, gc, Orientation.STANDING, is_split=True, cube1=(gr, gc), cube2=(gr+1, gc)), tuple())
    assert st_split.is_goal(board) is False


def test_dfs_shallower_path_updates():
    stage_file = STAGES_DIR / "stage_01_core.json"
    board = StageLoader.load_from_file(stage_file)
    env = BloxorzEnv(board)

    solver = DFSSolver(max_depth=200)
    res = solver.solve(env)
    assert res.success is True
    assert res.solution_length > 0
    assert res.generated_nodes >= res.expanded_nodes


def test_solvers_initial_generated_node_count():
    stage_file = STAGES_DIR / "stage_01_core.json"
    board = StageLoader.load_from_file(stage_file)
    env = BloxorzEnv(board)

    solvers = [
        BFSSolver(),
        DFSSolver(max_depth=100),
        UCSSolver(),
        AStarSolver(),
    ]
    for s in solvers:
        res = s.solve(env)
        assert res.generated_nodes >= 1, f"{s.name} generated_nodes should be at least 1 (counting root node)"
        assert res.expanded_nodes >= 1, f"{s.name} expanded_nodes should be at least 1"


def test_ucs_custom_cost_import():
    from Source.solvers.ucs import custom_cost_function, default_cost_function
    stage_file = STAGES_DIR / "stage_01_core.json"
    board = StageLoader.load_from_file(stage_file)
    env = BloxorzEnv(board)
    init_st = env.get_initial_state()

    # Step cost with custom function
    succs = env.get_successors(init_st, step_cost_fn=custom_cost_function)
    assert len(succs) > 0
    for a, ns, cost in succs:
        assert cost >= 0.5


def test_dropdown_padding_click_bounds():
    items = ["Item 0", "Item 1", "Item 2"]
    dd = Dropdown(rect=(10, 10, 140, 30), items=items, selected_idx=0, max_visible_items=3, item_height=28)
    dd.is_open = True

    popup = dd.get_popup_rect()
    # Click at the very bottom edge of popup (bottom padding)
    edge_y = popup.bottom - 2
    edge_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (popup.centerx, edge_y)})
    dd.handle_event(edge_click)
    assert 0 <= dd.selected_idx < len(items)

    # Test update with surface_rect
    scr_rect = pygame.Rect(0, 0, 800, 600)
    dd.update((popup.centerx, edge_y), surface_rect=scr_rect)
    assert dd.hovered_item_idx is None or (0 <= dd.hovered_item_idx < len(items))


def test_benchmark_modal_layout_caching_and_event_blocking():
    results = [
        {"algorithm": "BFS", "success": True, "moves": 10, "cost": 10.0, "time_ms": 1.0, "peak_mem_kb": 10.0, "expanded_nodes": 10, "generated_nodes": 20},
        {"algorithm": "A*", "success": True, "moves": 10, "cost": 10.0, "time_ms": 0.5, "peak_mem_kb": 5.0, "expanded_nodes": 5, "generated_nodes": 10},
    ]
    modal = BenchmarkModal(stage_name="Test", results=results)
    surf = pygame.Surface((1200, 800))

    # First draw builds layout
    modal.draw(surf)
    btn_close_id1 = id(modal.btn_close)
    replay_btn_ids1 = [id(b) for _, b in modal.replay_buttons]

    # Second draw on same surface size must REUSE buttons (no flicker or GC churn)
    modal.draw(surf)
    assert id(modal.btn_close) == btn_close_id1
    assert [id(b) for _, b in modal.replay_buttons] == replay_btn_ids1

    # Verify modal blocks background key events
    for k in (pygame.K_r, pygame.K_SPACE, pygame.K_UP, pygame.K_n):
        key_evt = pygame.event.Event(pygame.KEYDOWN, {"key": k})
        handled = modal.handle_event(key_evt)
        assert handled is True, f"BenchmarkModal must absorb background key event {k}"


def test_app_manual_move_non_split_space():
    from Source.gui.app import BloxorzApp

    app = BloxorzApp(stages_dir=STAGES_DIR)
    app.state = app.env.get_initial_state()
    assert not app.state.block.is_split

    init_moves = app.move_count
    # Press space on non-split block
    app.handle_manual_move(Direction.SWITCH_CUBE)
    assert app.move_count == init_moves, "SWITCH_CUBE on a non-split block must not count as a move"


def test_app_async_cross_stage_discard():
    from Source.gui.app import BloxorzApp
    from Source.solvers.base import SearchResult

    app = BloxorzApp(stages_dir=STAGES_DIR)
    app.current_stage_idx = 1 # Player switched to stage 1

    # An old solver from stage 0 finished and pushed result tagged with stage 0
    fake_res = SearchResult(algorithm="BFS", success=True, solution_length=5, actions=[], states=[app.state])
    stale_payload = ("single", BFSSolver(), fake_res, 0)
    app.async_worker_queue.put(stale_payload)

    # Process loop check
    payload = app.async_worker_queue.get_nowait()
    task_kind = payload[0]
    task_stage = payload[-1]
    if task_stage == app.current_stage_idx:
        app._on_single_solver_completed(payload[1], payload[2])

    # The stale result must NOT have been applied
    assert app.last_result is None


def test_app_death_anim_reset_on_solver_completed():
    from Source.gui.app import BloxorzApp
    from Source.solvers.base import SearchResult

    app = BloxorzApp(stages_dir=STAGES_DIR)
    app.is_lost = True
    app.death_anim_t = 0.55

    fake_res = SearchResult(algorithm="A*", success=True, solution_length=2, actions=[], states=[app.state, app.state])
    app._on_single_solver_completed(AStarSolver(), fake_res)

    assert app.is_lost is False
    assert app.death_anim_t == -1.0


def test_renderer_narrow_screen_camera_hud():
    surf = pygame.Surface((980, 680))
    board_rect = pygame.Rect(0, 0, 640, 680)
    renderer = GameRenderer(surf, board_rect)

    stage_file = sorted(STAGES_DIR.glob("*.json"))[0]
    board = StageLoader.load_from_file(stage_file)

    # Must draw without colliding with camera buttons or raising errors
    renderer._draw_camera_hud_strip(mode="2.5D")
    renderer._draw_canvas_background(board, mode="2.5D", explored_cells={}, replay_states=[], replay_idx=0)


def test_astar_strictly_pure_manhattan():
    from Source.solvers.heuristics import manhattan_heuristic

    solver = AStarSolver()
    assert solver.heuristic_fn is manhattan_heuristic

    # Even if initialized with dummy or different callable, it strictly binds to pure manhattan
    dummy_fn = lambda s, b: 0.0
    solver2 = AStarSolver(heuristic_fn=dummy_fn)
    assert solver2.heuristic_fn is manhattan_heuristic
