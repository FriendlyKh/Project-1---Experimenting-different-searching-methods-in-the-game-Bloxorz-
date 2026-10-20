"""
Unit tests for Block orientation transitions and rolling physics.
Crucial verification step recommended by Project 1 requirements (Section 3.1 & Page 4).
"""

import unittest
from Source.game.constants import Orientation, Direction
from Source.game.block import Block


class TestBlockTransitions(unittest.TestCase):
    """
    Tests all 12 orientation roll transitions plus split block mechanics.
    """

    def test_standing_rolls(self):
        # Standing at (5, 5)
        b = Block(5, 5, Orientation.STANDING)

        # UP -> LYING_V at (3, 5)
        up = b.roll(Direction.UP)
        self.assertEqual(up.orientation, Orientation.LYING_V)
        self.assertEqual((up.r, up.c), (3, 5))
        self.assertEqual(up.occupied_cells(), [(3, 5), (4, 5)])

        # DOWN -> LYING_V at (6, 5)
        down = b.roll(Direction.DOWN)
        self.assertEqual(down.orientation, Orientation.LYING_V)
        self.assertEqual((down.r, down.c), (6, 5))
        self.assertEqual(down.occupied_cells(), [(6, 5), (7, 5)])

        # LEFT -> LYING_H at (5, 3)
        left = b.roll(Direction.LEFT)
        self.assertEqual(left.orientation, Orientation.LYING_H)
        self.assertEqual((left.r, left.c), (5, 3))
        self.assertEqual(left.occupied_cells(), [(5, 3), (5, 4)])

        # RIGHT -> LYING_H at (5, 6)
        right = b.roll(Direction.RIGHT)
        self.assertEqual(right.orientation, Orientation.LYING_H)
        self.assertEqual((right.r, right.c), (5, 6))
        self.assertEqual(right.occupied_cells(), [(5, 6), (5, 7)])

    def test_lying_horizontal_rolls(self):
        # Lying horizontally at (5, 5) and (5, 6)
        b = Block(5, 5, Orientation.LYING_H)

        # UP -> LYING_H at (4, 5)
        up = b.roll(Direction.UP)
        self.assertEqual(up.orientation, Orientation.LYING_H)
        self.assertEqual((up.r, up.c), (4, 5))

        # DOWN -> LYING_H at (6, 5)
        down = b.roll(Direction.DOWN)
        self.assertEqual(down.orientation, Orientation.LYING_H)
        self.assertEqual((down.r, down.c), (6, 5))

        # LEFT -> STANDING at (5, 4)
        left = b.roll(Direction.LEFT)
        self.assertEqual(left.orientation, Orientation.STANDING)
        self.assertEqual((left.r, left.c), (5, 4))

        # RIGHT -> STANDING at (5, 7)
        right = b.roll(Direction.RIGHT)
        self.assertEqual(right.orientation, Orientation.STANDING)
        self.assertEqual((right.r, right.c), (5, 7))

    def test_lying_vertical_rolls(self):
        # Lying vertically at (5, 5) and (6, 5)
        b = Block(5, 5, Orientation.LYING_V)

        # UP -> STANDING at (4, 5)
        up = b.roll(Direction.UP)
        self.assertEqual(up.orientation, Orientation.STANDING)
        self.assertEqual((up.r, up.c), (4, 5))

        # DOWN -> STANDING at (7, 5)
        down = b.roll(Direction.DOWN)
        self.assertEqual(down.orientation, Orientation.STANDING)
        self.assertEqual((down.r, down.c), (7, 5))

        # LEFT -> LYING_V at (5, 4)
        left = b.roll(Direction.LEFT)
        self.assertEqual(left.orientation, Orientation.LYING_V)
        self.assertEqual((left.r, left.c), (5, 4))

        # RIGHT -> LYING_V at (5, 6)
        right = b.roll(Direction.RIGHT)
        self.assertEqual(right.orientation, Orientation.LYING_V)
        self.assertEqual((right.r, right.c), (5, 6))

    def test_split_and_merge(self):
        # Start split into (2, 2) and (2, 4)
        b = Block(r=2, c=2, is_split=True, cube1=(2, 2), cube2=(2, 4), active_cube=0)
        self.assertTrue(b.is_split)

        # Move active cube 0 to the RIGHT -> now at (2, 3)
        b_moved = b.roll(Direction.RIGHT)
        # Cube 1 is now at (2, 3), Cube 2 is at (2, 4). They are horizontally adjacent!
        # Should merge into a LYING_H block at (2, 3)
        self.assertFalse(b_moved.is_split)
        self.assertEqual(b_moved.orientation, Orientation.LYING_H)
        self.assertEqual((b_moved.r, b_moved.c), (2, 3))


if __name__ == "__main__":
    unittest.main()
