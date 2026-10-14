"""
Unit tests for StageLoader JSON parsing.
"""

import unittest
from pathlib import Path
from Source.config import STAGES_DIR
from Source.game.stage_loader import StageLoader
from Source.game.constants import TileType


class TestStageLoader(unittest.TestCase):

    def test_load_stage_01(self):
        stage_file = STAGES_DIR / "stage_01_core.json"
        self.assertTrue(stage_file.exists(), f"Stage file missing: {stage_file}")

        board = StageLoader.load_from_file(stage_file)
        self.assertEqual(board.start_pos, (1, 1))
        self.assertEqual(board.goal_pos, (3, 4))
        self.assertEqual(board.get_base_tile(3, 4), TileType.GOAL)
        self.assertEqual(board.get_base_tile(1, 1), TileType.FLOOR)

    def test_load_stage_03_bridges(self):
        stage_file = STAGES_DIR / "stage_03_bridge.json"
        self.assertTrue(stage_file.exists(), f"Stage file missing: {stage_file}")

        board = StageLoader.load_from_file(stage_file)
        self.assertIn("bridge_1", board.bridges)
        self.assertIn((3, 4), board.switches)


if __name__ == "__main__":
    unittest.main()
