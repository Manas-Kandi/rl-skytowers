import math
import numpy as np
import torch
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class Args:
    """Configuration for MCTS and training."""
    
    def __init__(self):
        # MCTS parameters
        self.numMCTSSims = 100  # Increased from 25 for better search
        self.cpuct = 1.0  # UCB exploration constant
        
        # Device
        self.cuda = torch.backends.mps.is_available()
        
        # Training parameters
        self.lr = 0.001  # Learning rate
        self.epochs = 10  # Increased epochs per batch
        self.batch_size = 64  # Batch size
        self.num_episodes = 20  # Increased episodes per iteration
        self.num_iterations = 100 # Total number of training iterations
        self.checkpoint_dir = './checkpoints'  # Model checkpoint directory
        self.buffer_size = 20000 # Max examples in replay buffer

class MCTS:
    """
    Monte Carlo Tree Search implementation for SkyTowers.
    
    Uses neural network guidance for policy and value estimates.
    """
    
    def __init__(self, game, model, args):
        """
        Initialize MCTS.
        
        Args:
            game: Game instance
            model: Neural network model
            args: Configuration arguments
        """
        self.game = game
        self.model = model
        self.args = args
        self.Qsa = {}       # Q values for state-action pairs
        self.Nsa = {}       # Visit counts for state-action pairs
        self.Ns = {}        # Visit counts for states
        self.Ps = {}        # Prior policies from neural net
        self.Es = {}        # Game end states
        self.Vs = {}        # Valid action masks

    def getActionProb(self, game_state, temp: float = 1.0) -> List[float]:
        """
        Get action probabilities using MCTS.
        
        Args:
            game_state: Current game state
            temp: Temperature for exploration (0 = greedy, 1 = stochastic)
            
        Returns:
            Probability distribution over actions
        """
        # Run MCTS simulations
        for _ in range(self.args.numMCTSSims):
            self.search(game_state)

        s = self.stringRepresentation(game_state)
        counts = [self.Nsa.get((s, a), 0) for a in range(self.game.action_size)]

        if temp == 0:
            # Greedy: pick best action
            bestA = np.argmax(counts)
            probs = [0.0] * len(counts)
            probs[bestA] = 1.0
            return probs

        # Stochastic: temperature-scaled probabilities
        counts = np.array([x ** (1.0 / temp) for x in counts])
        counts_sum = float(np.sum(counts))
        if counts_sum > 0:
            probs = (counts / counts_sum).tolist()
        else:
            probs = [1.0 / len(counts)] * len(counts)
        return probs

    def search(self, game_state) -> float:
        """
        MCTS search step: selection, expansion, simulation, backpropagation.
        
        Args:
            game_state: Current game state
            
        Returns:
            Value estimate for the state
        """
        s = self.stringRepresentation(game_state)

        # Check if game is over
        if s not in self.Es:
            self.Es[s] = game_state.getGameEnded()
        
        if self.Es[s] != 0:
            return -self.Es[s] * game_state.current_player

        # Leaf node: expand
        if s not in self.Ps:
            return self._expand_node(game_state, s)

        # Internal node: select best action and recurse
        return self._select_and_recurse(game_state, s)

    def _expand_node(self, game_state, state_key: str) -> float:
        """
        Expand a leaf node: get policy and value from neural network.
        
        Args:
            game_state: Current game state
            state_key: String representation of state
            
        Returns:
            Value estimate from neural network
        """
        valid_moves = game_state.get_valid_moves()
        
        # Get neural network predictions
        state_tensor = torch.FloatTensor(game_state.get_state()).unsqueeze(0)
        if self.args.cuda:
            state_tensor = state_tensor.to('mps')
            
        with torch.no_grad():
            policy, v = self.model(state_tensor)
            policy = torch.exp(policy).data.cpu().numpy()[0]
            v = v.data.cpu().numpy()[0][0]
        
        # Create valid action mask
        mask = self._create_action_mask(game_state, valid_moves)
        
        # Apply mask to policy
        policy = policy * mask
        sum_policy = np.sum(policy)
        if sum_policy > 0:
            policy /= sum_policy
        else:
            # Fallback: uniform over valid moves
            logger.warning("No valid moves found in policy - using uniform distribution")
            policy = mask / np.sum(mask)

        self.Ps[state_key] = policy
        self.Vs[state_key] = mask
        self.Ns[state_key] = 0
        return v

    def _create_action_mask(self, game_state, valid_moves: List) -> np.ndarray:
        """
        Create a binary mask for valid actions.
        
        Args:
            game_state: Current game state
            valid_moves: List of valid (move, build) tuples
            
        Returns:
            Binary mask of shape (action_size,)
        """
        mask = np.zeros(self.game.action_size)
        
        dir_map = {
            (-1, -1): 0, (-1, 0): 1, (-1, 1): 2,
            (0, -1): 3,           (0, 1): 4,
            (1, -1): 5,  (1, 0): 6,  (1, 1): 7
        }
        
        curr = game_state.p1_pos if game_state.current_player == 1 else game_state.p2_pos
        
        for move, build in valid_moves:
            # Calculate move direction
            dr, dc = move[0] - curr[0], move[1] - curr[1]
            m_idx = dir_map.get((dr, dc))
            
            # Calculate build direction
            b_dr, b_dc = build[0] - move[0], build[1] - move[1]
            b_idx = dir_map.get((b_dr, b_dc))
            
            if m_idx is not None and b_idx is not None:
                action_idx = m_idx * 8 + b_idx
                mask[action_idx] = 1
        
        return mask

    def _select_and_recurse(self, game_state, state_key: str) -> float:
        """
        Select best action using UCB and recurse.
        
        Args:
            game_state: Current game state
            state_key: String representation of state
            
        Returns:
            Negated value from child node
        """
        valid_mask = self.Vs[state_key]
        cur_best = -float('inf')
        best_act = -1

        # Select action with highest UCB
        for a in range(self.game.action_size):
            if valid_mask[a]:
                if (state_key, a) in self.Qsa:
                    u = self.Qsa[(state_key, a)] + self.args.cpuct * self.Ps[state_key][a] * math.sqrt(self.Ns[state_key]) / (1 + self.Nsa[(state_key, a)])
                else:
                    u = self.args.cpuct * self.Ps[state_key][a] * math.sqrt(self.Ns[state_key] + 1e-8)

                if u > cur_best:
                    cur_best = u
                    best_act = a

        a = best_act
        
        # Execute move
        import copy
        next_state = copy.deepcopy(game_state)
        move_pos, build_pos = self._decode_action(next_state, a)
        next_state.step((move_pos, build_pos))

        # Recurse
        v = self.search(next_state)

        # Update statistics
        if (state_key, a) in self.Qsa:
            self.Qsa[(state_key, a)] = (self.Nsa[(state_key, a)] * self.Qsa[(state_key, a)] + v) / (self.Nsa[(state_key, a)] + 1)
            self.Nsa[(state_key, a)] += 1
        else:
            self.Qsa[(state_key, a)] = v
            self.Nsa[(state_key, a)] = 1

        self.Ns[state_key] += 1
        return -v

    def _decode_action(self, game_state, action_idx: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Decode action index to (move_pos, build_pos).
        
        Args:
            game_state: Current game state
            action_idx: Action index (0-63)
            
        Returns:
            Tuple of ((move_r, move_c), (build_r, build_c))
        """
        m_idx = action_idx // 8
        b_idx = action_idx % 8
        
        dirs = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        dr, dc = dirs[m_idx]
        curr = game_state.p1_pos if game_state.current_player == 1 else game_state.p2_pos
        move_pos = (curr[0] + dr, curr[1] + dc)
        
        b_dr, b_dc = dirs[b_idx]
        build_pos = (move_pos[0] + b_dr, move_pos[1] + b_dc)
        
        return move_pos, build_pos

    def stringRepresentation(self, game) -> str:
        """
        Create a hashable string representation of game state.
        
        Args:
            game: Game instance
            
        Returns:
            String representation
        """
        return f"{game.board.tobytes()}{game.p1_pos}{game.p2_pos}{game.current_player}"
