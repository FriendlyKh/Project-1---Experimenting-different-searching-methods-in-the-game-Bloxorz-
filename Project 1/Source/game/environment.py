"""
Bloxorz game environment and state transition model.
Assigned to: Member 1 (Core Game Mechanics & State Modeling)

Handles action application, switch activation, bridge toggling, and successor generation.
"""

from typing import List, Tuple, Optional
from .constants import Direction
from .board import Board
from .state import GameState


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
        
        Guidelines for Member 1:
        - If state.block.is_split: [UP, DOWN, LEFT, RIGHT, SWITCH_CUBE]
        - Otherwise: [UP, DOWN, LEFT, RIGHT]
        """
        # TODO [Member 1]: Return legal actions for current block mode.
        raise NotImplementedError("Member 1: Implement get_legal_actions.")

    def step(self, state: GameState, action: Direction) -> Optional[GameState]:
        """
        Applies an action to a state and returns the resulting successor state,
        or None if the move results in falling / invalid placement.
        
        Guidelines for Member 1:
        1. Roll the block: `next_block = state.block.roll(action)`.
        2. Copy current bridge states into a mutable dict.
        3. Check switch triggers on all occupied cells:
           - SOFT switch: triggered if any occupied cell lands on it.
           - HEAVY switch: triggered ONLY if block is STANDING upright.
           - SPLIT switch: triggered ONLY if standing upright; teleports and splits the block!
           - For triggered switches, update linked bridges (toggle or permanent).
        4. Construct candidate `GameState(next_block, tuple(bridges.items()))`.
        5. Verify validity with `next_state.is_valid(self.board)`.
           If valid, return `next_state`; otherwise return `None`.
        """
        # TODO [Member 1]: Implement transition physics and switch activation logic.
        raise NotImplementedError("Member 1: Implement step transition model.")

    def get_successors(
        self,
        state: GameState,
        step_cost_fn=None,
    ) -> List[Tuple[Direction, GameState, float]]:
        """
        Generates all valid (action, successor_state, cost) tuples.
        Used directly by search algorithms (BFS, DFS, UCS, A*).
        
        Guidelines for Member 1:
        Iterate over self.get_legal_actions(state), call self.step(state, action),
        and collect non-None states with their step cost.
        """
        # TODO [Member 1]: Implement successor generator for search solvers.
        raise NotImplementedError("Member 1: Implement get_successors.")
