import math
import numpy as np
import torch

class Args:
    def __init__(self):
        self.numMCTSSims = 25
        self.cpuct = 1.0
        self.cuda = torch.backends.mps.is_available()
        self.lr = 0.001
        self.epochs = 5
        self.batch_size = 64
        self.num_episodes = 5
        self.checkpoint_dir = './checkpoints'

class MCTS:
    def __init__(self, game, model, args):
        self.game = game
        self.model = model
        self.args = args
        self.Qsa = {}       # stores Q values for s,a (as defined in the paper)
        self.Nsa = {}       # stores #times edge s,a was visited
        self.Ns = {}        # stores #times board s was visited
        self.Ps = {}        # stores initial policy (returned by neural net)
        self.Es = {}        # stores game.getGameEnded ended for board s
        self.Vs = {}        # stores game.getValidMoves for board s

    def getActionProb(self, canonicalBoard, temp=1):
        # This function is a bit tricky because my game state is complex (board + p1 + p2)
        # I need a way to hash the state.
        # Let's assume canonicalBoard is the game object itself for now, or a string rep.
        # Ideally, we pass the game instance.
        
        # For simplicity, let's do 50 simulations per move
        for i in range(self.args.numMCTSSims):
            self.search(canonicalBoard)

        s = self.stringRepresentation(canonicalBoard)
        counts = [self.Nsa.get((s, a), 0) for a in range(self.game.action_size)] # 64 actions

        if temp == 0:
            bestA = np.argmax(counts)
            probs = [0] * len(counts)
            probs[bestA] = 1
            return probs

        counts = [x ** (1. / temp) for x in counts]
        counts_sum = float(sum(counts))
        probs = [x / counts_sum for x in counts]
        return probs

    def search(self, game_state):
        s = self.stringRepresentation(game_state)

        if s not in self.Es:
            self.Es[s] = game_state.getGameEnded()
        
        if self.Es[s] != 0:
            return -self.Es[s] * game_state.current_player

        if s not in self.Ps:
            # Leaf node
            # Get valid moves
            valid_moves = game_state.get_valid_moves() # List of ((r,c), (br,bc))
            
            # Convert game state to tensor
            state_tensor = torch.FloatTensor(game_state.get_state()).unsqueeze(0)
            if self.args.cuda:
                state_tensor = state_tensor.to('mps')
                
            policy, v = self.model(state_tensor)
            policy = torch.exp(policy).data.cpu().numpy()[0]
            v = v.data.cpu().numpy()[0][0]
            
            # Mask invalid moves
            mask = np.zeros(self.game.action_size)
            
            # Mapping moves to action indices 0-63
            # We need a consistent mapping.
            # Let's define it: 
            # Move Dir (0-7) * 8 + Build Dir (0-7)
            # Dirs: 0:(-1,-1), 1:(-1,0), 2:(-1,1), 3:(0,-1), 4:(0,1), 5:(1,-1), 6:(1,0), 7:(1,1)
            
            dir_map = {
                (-1, -1): 0, (-1, 0): 1, (-1, 1): 2,
                (0, -1): 3,           (0, 1): 4,
                (1, -1): 5,  (1, 0): 6,  (1, 1): 7
            }
            
            for move, build in valid_moves:
                mr, mc = move
                # Calculate move direction
                curr = game_state.p1_pos if game_state.current_player == 1 else game_state.p2_pos
                dr, dc = mr - curr[0], mc - curr[1]
                m_idx = dir_map.get((dr, dc))
                
                # Calculate build direction from move pos
                b_dr, b_dc = build[0] - mr, build[1] - mc
                b_idx = dir_map.get((b_dr, b_dc))
                
                if m_idx is not None and b_idx is not None:
                    action_idx = m_idx * 8 + b_idx
                    mask[action_idx] = 1
            
            policy = policy * mask
            sum_policy = np.sum(policy)
            if sum_policy > 0:
                policy /= sum_policy
            else:
                # If all valid moves were masked (shouldn't happen if game logic is correct), uniform random
                print("All valid moves masked!")
                policy = mask / np.sum(mask)

            self.Ps[s] = policy
            self.Vs[s] = mask
            self.Ns[s] = 0
            return v

        # Pick action with highest UCB
        valid_mask = self.Vs[s]
        cur_best = -float('inf')
        best_act = -1

        # Iterate only over valid actions
        for a in range(self.game.action_size):
            if valid_mask[a]:
                if (s, a) in self.Qsa:
                    u = self.Qsa[(s, a)] + self.args.cpuct * self.Ps[s][a] * math.sqrt(self.Ns[s]) / (1 + self.Nsa[(s, a)])
                else:
                    u = self.args.cpuct * self.Ps[s][a] * math.sqrt(self.Ns[s] + 1e-8) # Q is 0 for unvisited

                if u > cur_best:
                    cur_best = u
                    best_act = a

        a = best_act
        
        # Execute move
        # Need to clone the game state to simulate
        # Since my game class is simple, I can probably just deepcopy it or implement a clone method
        import copy
        next_s = copy.deepcopy(game_state)
        
        # Decode action 'a' back to ((r,c), (br,bc))
        # This is the reverse of the mapping above
        m_idx = a // 8
        b_idx = a % 8
        
        dirs = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        dr, dc = dirs[m_idx]
        curr = next_s.p1_pos if next_s.current_player == 1 else next_s.p2_pos
        move_pos = (curr[0] + dr, curr[1] + dc)
        
        b_dr, b_dc = dirs[b_idx]
        build_pos = (move_pos[0] + b_dr, move_pos[1] + b_dc)
        
        if not (0 <= move_pos[0] < 5 and 0 <= move_pos[1] < 5):
            print(f"CRASH DEBUG: s={s}")
            print(f"curr={curr}, dr={dr}, dc={dc}, move_pos={move_pos}")
            print(f"a={a}, m_idx={m_idx}, b_idx={b_idx}")
            print(f"valid_mask[a]={valid_mask[a]}")
            print(f"Vs[s] len={len(valid_mask)}")
        
        next_s.step((move_pos, build_pos))

        v = self.search(next_s)

        if (s, a) in self.Qsa:
            self.Qsa[(s, a)] = (self.Nsa[(s, a)] * self.Qsa[(s, a)] + v) / (self.Nsa[(s, a)] + 1)
            self.Nsa[(s, a)] += 1
        else:
            self.Qsa[(s, a)] = v
            self.Nsa[(s, a)] = 1

        self.Ns[s] += 1
        return -v

    def stringRepresentation(self, game):
        # Simple string rep for hashing
        # Board + p1 + p2 + cur_player
        return f"{game.board.tobytes()}{game.p1_pos}{game.p2_pos}{game.current_player}"
