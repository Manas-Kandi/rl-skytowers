import numpy as np
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

class SkyTowersGame:
    """
    Game logic for SkyTowers.
    
    The game is played on a 5x5 grid.
    Players take turns moving and building.
    Goal: Reach level 3 or force opponent into stalemate.
    """
    def __init__(self):
        self.board_size = 5
        self.action_size = 64
        self.reset()

    def reset(self):
        """Reset the game state to initial conditions."""
        # 5x5 board
        # Levels: 0 (ground), 1, 2, 3, 4 (dome)
        self.board = np.zeros((self.board_size, self.board_size), dtype=int)
        
        # Player positions: (player_id, x, y)
        # Player 1 starts at (0,0), Player -1 starts at (4,4)
        self.p1_pos: Tuple[int, int] = (0, 0)
        self.p2_pos: Tuple[int, int] = (4, 4)
        self.current_player: int = 1 # 1 or -1
        self.winner: Optional[int] = None
        self.steps: int = 0
        self.max_steps: int = 100 # Avoid infinite games

    def get_state(self) -> np.ndarray:
        """
        Return a representation of the state for the neural network.
        
        Channels: 
        - 0: P1 position (1 at pos, 0 elsewhere)
        - 1: P2 position (1 at pos, 0 elsewhere)
        - 2: Board levels (normalized 0-4)
        - 3: Current player indicator
        
        Returns:
            np.ndarray: State tensor of shape (4, board_size, board_size)
        """
        state = np.zeros((4, self.board_size, self.board_size), dtype=np.float32)
        state[0, self.p1_pos[0], self.p1_pos[1]] = 1
        state[1, self.p2_pos[0], self.p2_pos[1]] = 1
        state[2] = self.board / 4.0
        state[3] = (self.current_player + 1) / 2  # 0 for player -1, 1 for player 1
        return state

    def get_valid_moves(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Get all valid moves for the current player.
        
        A valid move consists of:
        1. Moving to an adjacent cell (max 1 level up)
        2. Building on an adjacent cell (not occupied, not a dome)
        
        Returns:
            List of tuples: [((move_r, move_c), (build_r, build_c)), ...]
        """
        if self.winner is not None:
            return []

        moves = []
        curr_pos = self.p1_pos if self.current_player == 1 else self.p2_pos
        other_pos = self.p2_pos if self.current_player == 1 else self.p1_pos
        
        r, c = curr_pos
        
        # Move directions (including diagonals)
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            
            # Check bounds
            if not (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                continue
                
            # Check if occupied by other player
            if (nr, nc) == other_pos:
                continue
            
            # Check height difference (can only climb 1 level at a time)
            curr_height = self.board[r, c]
            next_height = self.board[nr, nc]
            
            # Cannot move onto a dome (level 4) or down more than 1 level
            # Actually, you can jump down any height, but only climb 1.
            # "A worker may move into an adjacent space... if the destination space is no more than one level higher than the worker's current level."
            if next_height > curr_height + 1 or next_height >= 4:
                continue
                    
            # Valid move found. Now check build options from new position
            for b_dr, b_dc in directions:
                br, bc = nr + b_dr, nc + b_dc
                
                # Check build position bounds
                if not (0 <= br < self.board_size and 0 <= bc < self.board_size):
                    continue
                    
                # Cannot build on other player
                if (br, bc) == other_pos:
                    continue
                    
                # Cannot build where you are standing (the new position)
                if (br, bc) == (nr, nc):
                    continue
                    
                # Can only build if not a dome
                if self.board[br, bc] < 4:
                    moves.append(((nr, nc), (br, bc)))
                    
        return moves

    def step(self, action: Tuple[Tuple[int, int], Tuple[int, int]]) -> Optional[int]:
        """
        Execute a move in the game.
        
        Args:
            action: Tuple of ((move_r, move_c), (build_r, build_c))
            
        Returns:
            Winner (1, -1, 0 for draw) or None if game continues
        
        Raises:
            ValueError: If the move is invalid (though usually checked before calling)
        """
        if self.winner is not None:
            return self.winner

        move_pos, build_pos = action
        
        # Basic validation could go here, but relying on get_valid_moves for perf
        
        # Update player position
        if self.current_player == 1:
            self.p1_pos = move_pos
        else:
            self.p2_pos = move_pos
            
        # Check win condition: If moved to level 3
        if self.board[move_pos[0], move_pos[1]] == 3:
            self.winner = self.current_player
            logger.info(f"Player {self.current_player} wins by reaching level 3")
            return self.winner
            
        # Build
        self.board[build_pos[0], build_pos[1]] += 1
        
        # Switch player
        self.current_player *= -1
        self.steps += 1
        
        # Check for draw (max steps reached)
        if self.steps >= self.max_steps:
            self.winner = 0  # Draw
            logger.info(f"Game ended in draw after {self.max_steps} steps")
            
        return self.winner

    def is_terminal(self) -> bool:
        """Check if the game has ended."""
        return self.getGameEnded() != 0

    def getGameEnded(self) -> int:
        """
        Get the game end state.
        
        Returns:
            1 if player 1 wins
            -1 if player -1 wins
            0 if player -1 has no valid moves (player 1 wins)
            0 if game continues
        """
        if self.winner is not None:
            return self.winner
        
        # Check for stalemate
        # If current player has no moves, they lose.
        # So if current_player is 1 and has no moves, winner is -1.
        if len(self.get_valid_moves()) == 0:
            logger.info(f"Player {self.current_player} has no valid moves - loses")
            self.winner = -self.current_player
            return self.winner
            
        return 0
