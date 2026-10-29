"""
Bloxorz game environment and state transition model.
Assigned to: Member 1 (Core Game Mechanics & State Modeling)

Handles action application, switch activation, bridge toggling, and successor generation.
"""

from typing import List, Tuple, Optional, Callable
from .constants import Orientation, Direction, SwitchOperation, SwitchType, TileType
from .board import Board, Switch
from .state import GameState
from .block import Block


_STANDARD_ACTIONS: Tuple[Direction, ...] = (
    Direction.UP,
    Direction.DOWN,
    Direction.LEFT,
    Direction.RIGHT,
)
_SPLIT_ACTIONS: Tuple[Direction, ...] = (
    Direction.UP,
    Direction.DOWN,
    Direction.LEFT,
    Direction.RIGHT,
    Direction.SWITCH_CUBE,
)


class BloxorzEnv:
    """
    Encapsulates board rules, action application, and successor generation.
    """

    def __init__(self, board: Board):
        self.board = board

    def get_initial_state(self) -> GameState:
        """
        Creates the starting game state.
        The block starts standing upright on the designated start tile.
        """
        start_r, start_c = self.board.start_pos
        init_block = Block(r=start_r, c=start_c, orientation=Orientation.STANDING)
        init_bridges = tuple(
            sorted(
                ((b_id, bridge.initially_open) for b_id, bridge in self.board.bridges.items()),
                key=lambda x: x[0],
            )
        )
        return GameState(block=init_block, bridge_states=init_bridges, _canonical=True)

    def get_legal_actions(self, state: GameState) -> Tuple[Direction, ...]:
        """
        Returns candidate actions from this state.
        """
        if state.block.is_split:
            return _SPLIT_ACTIONS
        return _STANDARD_ACTIONS

    @staticmethod
    def _trigger_switch(sw: Switch, bridges: dict) -> None:
        """Update linked_bridges state when switch is active."""
        for b_id in sw.linked_bridges:
            if b_id in bridges:
                if sw.operation == SwitchOperation.TOGGLE:
                    bridges[b_id] = not bridges[b_id]
                elif sw.operation == SwitchOperation.PERMANENT:
                    bridges[b_id] = True

    def step(self, state: GameState, action: Direction) -> Optional[GameState]:
        """
        Applies an action to a state and returns the resulting successor state,
        or None if the move results in falling / invalid placement.
        """
        next_block = state.block.roll(action)
        switches = self.board.switches
        bridge_states: Optional[dict] = None

        if action != Direction.SWITCH_CUBE and switches:
            # Nếu trạng thái TRƯỚC khi di chuyển là đang tách đôi (is_split),
            # chỉ có đúng 1 khối con vừa di chuyển (ngay cả khi bước này làm 2 khối gộp lại)
            if state.block.is_split:
                if next_block.is_split:
                    moved_cell = next_block.cube1 if state.block.active_cube == 0 else next_block.cube2
                else:
                    # Trường hợp 2 khối vừa gộp lại: tìm ô mới mà khối active vừa lăn tới
                    stationary_cell = state.block.cube2 if state.block.active_cube == 0 else state.block.cube1
                    moved_cell = None
                    for c in next_block._cells:
                        if c != stationary_cell:
                            moved_cell = c
                            break

                sw = switches.get(moved_cell)
                if sw is not None and sw.type == SwitchType.SOFT:
                    bridge_states = dict(state.bridge_states)
                    self._trigger_switch(sw, bridge_states)
            else:
                for cell in next_block._cells:
                    sw = switches.get(cell)
                    if sw is not None:
                        if sw.type == SwitchType.SOFT:
                            if bridge_states is None:
                                bridge_states = dict(state.bridge_states)
                            self._trigger_switch(sw, bridge_states)
                        elif sw.type == SwitchType.HEAVY and next_block.orientation == Orientation.STANDING:
                            if bridge_states is None:
                                bridge_states = dict(state.bridge_states)
                            self._trigger_switch(sw, bridge_states)
                        elif sw.type == SwitchType.SPLIT and next_block.orientation == Orientation.STANDING:
                            if sw.split_targets is not None:
                                if bridge_states is None:
                                    bridge_states = dict(state.bridge_states)
                                self._trigger_switch(sw, bridge_states)
                                next_block = next_block.split_into(
                                    tuple(sw.split_targets[0]),
                                    tuple(sw.split_targets[1]),
                                )
                                for split_cell in next_block._cells:
                                    sp_sw = switches.get(split_cell)
                                    if sp_sw is not None and sp_sw.type == SwitchType.SOFT:
                                        self._trigger_switch(sp_sw, bridge_states)
                                break

        # Fast inline board validation before constructing GameState
        board = self.board
        rows = board.rows
        cols = board.cols
        grid = board.grid
        for r, c in next_block._cells:
            if not (0 <= r < rows and 0 <= c < cols):
                return None
            tile = grid[r][c]
            if tile == TileType.VOID:
                return None
            if tile == TileType.BRIDGE:
                b_id = board.cell_to_bridge.get((r, c))
                if b_id is None:
                    return None
                if bridge_states is not None:
                    if not bridge_states.get(b_id, False):
                        return None
                else:
                    if not state.bridge_dict.get(b_id, False):
                        return None

        if (not next_block.is_split) and (next_block.orientation == Orientation.STANDING):
            if grid[next_block.r][next_block.c] == TileType.FRAGILE:
                return None

        next_bridges = (
            tuple(bridge_states.items()) if bridge_states is not None else state.bridge_states
        )
        return GameState(block=next_block, bridge_states=next_bridges, _canonical=True)

    def get_successors(
        self,
        state: GameState,
        step_cost_fn: Optional[Callable[[GameState, Direction, GameState, Board], float]] = None,
    ) -> List[Tuple[Direction, GameState, float]]:
        """
        Generates all valid (action, successor_state, cost) tuples.
        Used directly by search algorithms (BFS, DFS, UCS, A*).
        """
        successors = []
        actions = _SPLIT_ACTIONS if state.block.is_split else _STANDARD_ACTIONS

        for action in actions:
            next_state = self.step(state, action)
            if next_state is not None:
                if step_cost_fn is not None:
                    step_cost = float(step_cost_fn(state, action, next_state, self.board))
                else:
                    step_cost = 1.0
                successors.append((action, next_state, step_cost))

        return successors