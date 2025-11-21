import torch
import numpy as np
from game import SkyTowersGame
from model import SkyNet
from mcts import MCTS, Args
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Arena:
    """
    Arena to pit two agents against each other.
    """
    def __init__(self, player1, player2, game, display=None):
        """
        Args:
            player1: Function that takes board as input and returns action
            player2: Function that takes board as input and returns action
            game: Game object
            display: Function to display board
        """
        self.player1 = player1
        self.player2 = player2
        self.game = game
        self.display = display

    def play_game(self, verbose=False):
        """
        Execute one episode of a game.
        
        Returns:
            1 if player1 wins
            -1 if player2 wins
            0 if draw
        """
        players = [self.player2, None, self.player1]
        cur_player = 1
        self.game.reset()
        it = 0
        
        while self.game.getGameEnded() == 0:
            it += 1
            if verbose:
                logger.info(f"Turn {it}, Player {cur_player}")
                if self.display:
                    self.display(self.game.board)
            
            action = players[cur_player + 1](self.game)
            
            # Decode action if it's an index (from MCTS)
            if isinstance(action, int) or isinstance(action, np.int64):
                m_idx = action // 8
                b_idx = action % 8
                dirs = [
                    (-1, -1), (-1, 0), (-1, 1),
                    (0, -1),           (0, 1),
                    (1, -1),  (1, 0),  (1, 1)
                ]
                dr, dc = dirs[m_idx]
                curr = self.game.p1_pos if self.game.current_player == 1 else self.game.p2_pos
                move_pos = (curr[0] + dr, curr[1] + dc)
                b_dr, b_dc = dirs[b_idx]
                build_pos = (move_pos[0] + b_dr, move_pos[1] + b_dc)
                action = (move_pos, build_pos)

            valid_moves = self.game.get_valid_moves()
            if action not in valid_moves:
                logger.error(f"Invalid action by player {cur_player}: {action}")
                return -cur_player

            self.game.step(action)
            cur_player *= -1
            
        return self.game.getGameEnded()

    def play_games(self, num, verbose=False):
        """
        Play num games.
        """
        num = int(num / 2)
        one_won = 0
        two_won = 0
        draws = 0
        
        for _ in range(num):
            game_result = self.play_game(verbose=verbose)
            if game_result == 1:
                one_won += 1
            elif game_result == -1:
                two_won += 1
            else:
                draws += 1
                
        # Swap sides
        self.player1, self.player2 = self.player2, self.player1
        
        for _ in range(num):
            game_result = self.play_game(verbose=verbose)
            if game_result == -1: # Player 1 (original) is now player 2
                one_won += 1
            elif game_result == 1:
                two_won += 1
            else:
                draws += 1
                
        return one_won, two_won, draws

def random_player(game):
    moves = game.get_valid_moves()
    return moves[np.random.randint(len(moves))]

def mcts_player(game, model, args):
    mcts = MCTS(game, model, args)
    return lambda g: np.argmax(mcts.getActionProb(g, temp=0))

if __name__ == "__main__":
    # Example usage: Evaluate current model against random
    game = SkyTowersGame()
    args = Args()
    
    # Load model
    model = SkyNet()
    device = 'mps' if args.cuda else 'cpu'
    model = model.to(device)
    
    try:
        model.load_state_dict(torch.load('checkpoints/best.pth.tar', map_location=device)['state_dict'])
        print("Loaded best model")
    except:
        print("Using random model")
        
    model.eval()
    
    # Create MCTS player
    p1 = mcts_player(game, model, args)
    
    # Create Random player
    p2 = random_player
    
    arena = Arena(p1, p2, game)
    print("Starting evaluation...")
    p1_wins, p2_wins, draws = arena.play_games(20, verbose=False)
    
    print(f"Model Wins: {p1_wins}, Random Wins: {p2_wins}, Draws: {draws}")
