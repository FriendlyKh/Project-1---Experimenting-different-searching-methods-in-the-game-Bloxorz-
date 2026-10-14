"""
Unit tests for GameState immutability, hashing, goal checking, and bridge dynamics.
"""

import unittest
from Source.game.constants import Orientation, Direction, TileType, SwitchType, SwitchOperation
from Source.game.block import Block
from Source.game.board import Board, Bridge, Switch
from Source.game.state import GameState
from Source.game.environment import BloxorzEnv


class TestGameState(unittest.TestCase):

    def setUp(self):
        # Create a simple 4x4 test board
        # Row 0: 1 1 1 1
        # Row 1: 1 3 1 1 (Tile (1, 1) is FRAGILE)
        # Row 2: 1 4 1 1 (Tile (1, 2) is BRIDGE)
        # Row 3: 1 1 2 1 (Tile (3, 2) is GOAL)
        grid = [
            [TileType.FLOOR, TileType.FLOOR, TileType.FLOOR, TileType.FLOOR],
            [TileType.FLOOR, TileType.FRAGILE, TileType.FLOOR, TileType.FLOOR],
            [TileType.FLOOR, TileType.BRIDGE, TileType.FLOOR, TileType.FLOOR],
            [TileType.FLOOR, TileType.FLOOR, TileType.GOAL, TileType.FLOOR],
        ]
        bridge_b1 = Bridge(id="b1", cells=[(2, 1)], initially_open=False)
        switch_s1 = Switch(
            pos=(0, 0),
            type=SwitchType.SOFT,
            operation=SwitchOperation.TOGGLE,
            linked_bridges=["b1"],
        )
        self.board = Board(
            rows=4,
            cols=4,
            grid=grid,
            goal_pos=(3, 2),
            start_pos=(0, 0),
            bridges={"b1": bridge_b1},
            switches={(0, 0): switch_s1},
        )
        self.env = BloxorzEnv(self.board)

    def test_state_hashing_and_equality(self):
        b1 = Block(1, 1, Orientation.STANDING)
        b2 = Block(1, 1, Orientation.STANDING)
        b3 = Block(1, 1, Orientation.LYING_H)

        s1 = GameState(b1, (("b1", False),))
        s2 = GameState(b2, (("b1", False),))
        s3 = GameState(b1, (("b1", True),))  # Different bridge state
        s4 = GameState(b3, (("b1", False),))  # Different orientation

        # Equal states must hash equally
        self.assertEqual(s1, s2)
        self.assertEqual(hash(s1), hash(s2))
        self.assertEqual(len({s1, s2}), 1)

        # Different bridge state -> different state
        self.assertNotEqual(s1, s3)
        self.assertNotEqual(hash(s1), hash(s3))

        # Different orientation -> different state
        self.assertNotEqual(s1, s4)

    def test_goal_condition(self):
        # Goal is at (3, 2)
        # 1. Standing on goal -> WIN
        s_win = GameState(Block(3, 2, Orientation.STANDING), (("b1", False),))
        self.assertTrue(s_win.is_goal(self.board))

        # 2. Lying horizontally across goal -> NOT WIN
        s_lying_h = GameState(Block(3, 1, Orientation.LYING_H), (("b1", False),))
        self.assertFalse(s_lying_h.is_goal(self.board))

        # 3. Lying vertically across goal -> NOT WIN
        s_lying_v = GameState(Block(2, 2, Orientation.LYING_V), (("b1", False),))
        self.assertFalse(s_lying_v.is_goal(self.board))

    def test_fragile_tile(self):
        # Tile (1, 1) is FRAGILE
        # Standing on fragile tile -> INVALID (falls)
        s_standing_fragile = GameState(Block(1, 1, Orientation.STANDING), (("b1", False),))
        self.assertFalse(s_standing_fragile.is_valid(self.board))

        # Lying horizontally across (1, 1) and (1, 2) -> VALID (weight distributed)
        s_lying_fragile = GameState(Block(1, 0, Orientation.LYING_H), (("b1", False),))
        self.assertTrue(s_lying_fragile.is_valid(self.board))


if __name__ == "__main__":
    unittest.main()
