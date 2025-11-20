import numpy as np

class SkyTowersGame:
    def __init__(self):
        self.board_size = 5
        self.action_size = 64
        self.reset()

    def reset(self):
        # 5x5 board
        # Levels: 0 (ground), 1, 2, 3, 4 (dome)
        self.board = np.zeros((self.board_size, self.board_size), dtype=int)
        
        # Player positions: (player_id, x, y)
        # Player 1 starts at (0,0), Player -1 starts at (4,4)
        self.p1_pos = (0, 0)
        self.p2_pos = (4, 4)
        self.current_player = 1 # 1 or -1
        self.winner = None
        self.steps = 0
        self.max_steps = 100 # Avoid infinite games

    def get_state(self):
        # Return a representation of the state for the NN
        # Channels: 
        # 0: P1 position (1 at pos, 0 elsewhere)
        # 1: P2 position (1 at pos, 0 elsewhere)
        # 2: Board levels (normalized 0-4)
        state = np.zeros((3, self.board_size, self.board_size), dtype=np.float32)
        state[0, self.p1_pos[0], self.p1_pos[1]] = 1
        state[1, self.p2_pos[0], self.p2_pos[1]] = 1
        state[2] = self.board / 4.0
        return state

    def get_valid_moves(self):
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
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                # Check if occupied by other player
                if (nr, nc) == other_pos:
                    continue
                
                # Check height difference (can only climb 1 level at a time)
                curr_height = self.board[r, c]
                next_height = self.board[nr, nc]
                
                if next_height <= curr_height + 1 and next_height < 4: # Cannot move onto a dome (level 4)
                    # Valid Move found. Now checking Build options from new position
                    # For simplicity in this version, we combine Move+Build into a single action
                    # But to keep action space small for RL, let's simplify:
                    # Action = Move Direction (8) * Build Direction (8) = 64 actions?
                    # Or maybe just Move (8) and auto-build? No, strategy needs build choice.
                    # Let's do: Move to (nr, nc), then Build at (br, bc)
                    
                    for b_dr, b_dc in directions:
                        br, bc = nr + b_dr, nc + b_dc
                        if 0 <= br < self.board_size and 0 <= bc < self.board_size:
                            if (br, bc) == other_pos: # Cannot build on other player
                                continue
                            if (br, bc) == (nr, nc): # Cannot build where you are standing
                                continue
                            if self.board[br, bc] < 4: # Can only build if not a dome
                                moves.append(((nr, nc), (br, bc)))
        return moves

    def step(self, action):
        # action is tuple ((move_r, move_c), (build_r, build_c))
        move_pos, build_pos = action
        
        if self.current_player == 1:
            self.p1_pos = move_pos
        else:
            self.p2_pos = move_pos
            
        # Check win condition: If moved to level 3
        if self.board[move_pos[0], move_pos[1]] == 3:
            self.winner = self.current_player
            return self.winner
            
        # Build
        self.board[build_pos[0], build_pos[1]] += 1
        
        self.current_player *= -1
        self.steps += 1
        
        if self.steps >= self.max_steps:
            self.winner = 0 # Draw
            
        return self.winner

    def is_terminal(self):
        return self.getGameEnded() != 0

    def getGameEnded(self):
        if self.winner is not None:
            return self.winner
        
        if len(self.get_valid_moves()) == 0:
            # Stalemate: Current player loses
            return -self.current_player
            
        return 0
