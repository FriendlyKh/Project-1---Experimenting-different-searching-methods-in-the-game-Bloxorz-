"""
Bloxorz game environment and state transition model.
Assigned to: Member 1 (Core Game Mechanics & State Modeling)

Handles action application, switch activation, bridge toggling, and successor generation.
"""

from typing import List, Tuple, Optional, Callable
from .constants import Orientation, Direction, SwitchOperation, SwitchType
from .board import Board, Switch
from .state import GameState
from .constants import SwitchType


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
        from .block import Block
        from .constants import Orientation
        start_r, start_c = self.board.start_pos
        init_block = Block(r=start_r, c=start_c, orientation=Orientation.STANDING)
        init_bridges = tuple(
            (b_id, bridge.initially_open)
            for b_id, bridge in self.board.bridges.items()
        )
        return GameState(block=init_block, bridge_states=init_bridges)

    def get_legal_actions(self, state: GameState) -> List[Direction]:
        """
        Returns candidate actions from this state.

        """
        if state.block.is_split:
            return [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT, Direction.SWITCH_CUBE]
        else:
            return [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]

    @staticmethod
    def _trigger_switch(sw: Switch, bridges: dict) -> None:
        """Update link_bridge state when switch is active"""
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
        bridge_states = dict(state.bridge_states)
        switches = self.board.switches


        if action != Direction.SWITCH_CUBE:
            if next_block.is_split:
                occupied_cell = next_block.cube1 if next_block.active_cube == 0 else next_block.cube2
                if occupied_cell in switches and switches[occupied_cell].type == SwitchType.SOFT:
                    self._trigger_switch(switches[occupied_cell], bridge_states)
            else:
                for cell in next_block.occupied_cells():
                    if cell in switches:
                        sw = switches[cell]
                        if sw.type == SwitchType.SOFT:
                            self._trigger_switch(sw, bridge_states)
                        elif sw.type == SwitchType.HEAVY and next_block.orientation == Orientation.STANDING:
                            self._trigger_switch(sw, bridge_states)
                        elif sw.type == SwitchType.SPLIT and next_block.orientation == Orientation.STANDING:
                            if sw.split_targets is not None:
                                #tele thi sw hien tai kich hoat neu la soft
                                self._trigger_switch(sw, bridge_states)
                                next_block = next_block.split_into(
                                    tuple(sw.split_targets[0]),
                                    tuple(sw.split_targets[1]),
                                    )
                            for split_cell in next_block.occupied_cells():
                                    if split_cell in switches and switches[split_cell].type == SwitchType.SOFT:
                                        self._trigger_switch(switches[split_cell], bridge_states)
                            #End loop when succesfully split
                            break

        next_state = GameState(block=next_block, bridge_states=tuple(bridge_states.items()))
        if next_state.is_valid(self.board):
            return next_state
        return None

    def get_successors(
        self,
        state: GameState,
        step_cost_fn: Optional[Callable[[GameState, Direction, GameState, Board], float]] = None,
    ) -> List[Tuple[Direction, GameState, float]]:
        """
        Generates all valid (action, successor_state, cost) tuples.
        Used directly by search algorithms (BFS, DFS, UCS, A*).
        
        Guidelines for Member 1:
        Iterate over self.get_legal_actions(state), call self.step(state, action),
        and collect non-None states with their step cost.
        """
        successors = []
        
        for action in self.get_legal_actions(state):
            next_state = self.step(state, action)

            if step_cost_fn is not None:
                step_cost = float(step_cost_fn(state, action, next_state, self.board))
            else:
                step_cost = 1.0

            if next_state is not None:
                successors.append((action, next_state, step_cost))

        return successors
