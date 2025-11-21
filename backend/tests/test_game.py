import unittest
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import SkyTowersGame

class TestSkyTowersGame(unittest.TestCase):
    def setUp(self):
        self.game = SkyTowersGame()

    def test_initial_state(self):
        self.assertEqual(self.game.current_player, 1)
        self.assertEqual(self.game.p1_pos, (0, 0))
        self.assertEqual(self.game.p2_pos, (4, 4))
        self.assertTrue(np.all(self.game.board == 0))

    def test_valid_moves_start(self):
        moves = self.game.get_valid_moves()
        # From (0,0), can move to (0,1), (1,0), (1,1)
        # For each move, can build in adjacent squares
        # This is a basic check that moves exist
        self.assertTrue(len(moves) > 0)
        
        # Check a specific valid move structure
        move = moves[0]
        self.assertEqual(len(move), 2) # (move_pos, build_pos)
        self.assertEqual(len(move[0]), 2) # (r, c)
        self.assertEqual(len(move[1]), 2) # (r, c)

    def test_win_condition(self):
        # Set up a win scenario
        self.game.board[0, 1] = 2
        self.game.board[1, 1] = 3
        
        # Move player 1 to (0, 1) (level 2)
        self.game.p1_pos = (0, 1)
        
        # Execute move to (1, 1) (level 3)
        # Mock action: move to (1,1), build at (1,2)
        action = ((1, 1), (1, 2))
        winner = self.game.step(action)
        
        self.assertEqual(winner, 1)
        self.assertEqual(self.game.getGameEnded(), 1)

    def test_dome_block(self):
        # Set up a dome at (0, 1)
        self.game.board[0, 1] = 4
        
        # Player 1 at (0, 0) should not be able to move to (0, 1)
        moves = self.game.get_valid_moves()
        for move_pos, build_pos in moves:
            self.assertNotEqual(move_pos, (0, 1))

if __name__ == '__main__':
    unittest.main()
