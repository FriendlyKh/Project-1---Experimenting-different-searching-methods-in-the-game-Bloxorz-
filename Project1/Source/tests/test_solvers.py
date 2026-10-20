"""
Unit tests for Search Solvers (BFS, DFS, UCS, A*).
"""

import unittest
from Source.config import STAGES_DIR
from Source.game.stage_loader import StageLoader
from Source.game.environment import BloxorzEnv
from Source.solvers.bfs import BFSSolver
from Source.solvers.dfs import DFSSolver
from Source.solvers.ucs import UCSSolver
from Source.solvers.astar import AStarSolver


class TestSolvers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        stage_file = STAGES_DIR / "stage_01_core.json"
        cls.board = StageLoader.load_from_file(stage_file)
        cls.env = BloxorzEnv(cls.board)

    def test_bfs_solver(self):
        solver = BFSSolver()
        res = solver.solve(self.env)
        self.assertTrue(res.success)
        self.assertGreater(res.solution_length, 0)
        # Verify the path actually reaches the goal
        last_state = res.states[-1]
        self.assertTrue(last_state.is_goal(self.board))

    def test_dfs_solver(self):
        solver = DFSSolver()
        res = solver.solve(self.env)
        self.assertTrue(res.success)
        self.assertGreater(res.solution_length, 0)
        last_state = res.states[-1]
        self.assertTrue(last_state.is_goal(self.board))

    def test_ucs_solver(self):
        solver = UCSSolver()
        res = solver.solve(self.env)
        self.assertTrue(res.success)
        self.assertGreater(res.solution_length, 0)
        last_state = res.states[-1]
        self.assertTrue(last_state.is_goal(self.board))

    def test_astar_solver(self):
        solver = AStarSolver()
        res = solver.solve(self.env)
        self.assertTrue(res.success)
        self.assertGreater(res.solution_length, 0)
        last_state = res.states[-1]
        self.assertTrue(last_state.is_goal(self.board))


if __name__ == "__main__":
    unittest.main()
