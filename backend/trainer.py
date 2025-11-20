import os
import numpy as np
import torch
import torch.optim as optim
from collections import deque
from random import shuffle
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from game import SkyTowersGame
from model import SkyNet
from mcts import MCTS, Args
import time



class Trainer:
    def __init__(self, callback=None):
        self.args = Args()
        self.game = SkyTowersGame() # Template game
        self.model = SkyNet()
        self.callback = callback
        
        if self.args.cuda:
            self.model = self.model.to('mps')
            
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.args.lr)
        self.mcts = MCTS(self.game, self.model, self.args)
        
        if not os.path.exists(self.args.checkpoint_dir):
            os.makedirs(self.args.checkpoint_dir)

    def execute_episode(self):
        train_examples = []
        game = SkyTowersGame()
        self.mcts = MCTS(game, self.model, self.args) # Reset MCTS tree for new game
        step = 0
        
        while True:
            step += 1
            temp = int(step < 10) # Temperature for exploration
            
            if game.getGameEnded() != 0:
                r = game.getGameEnded()
                return [(x[0], x[2], r * ((-1) ** (x[1] != game.current_player))) for x in train_examples]

            pi = self.mcts.getActionProb(game, temp=temp)
            sym = game.get_state() # Symmetries could be added here (rotation/flip)
            
            train_examples.append([sym, game.current_player, pi, None]) # Value filled later
            
            action_idx = np.random.choice(len(pi), p=pi)
            
            # Decode action
            m_idx = action_idx // 8
            b_idx = action_idx % 8
            dirs = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1)
            ]
            dr, dc = dirs[m_idx]
            curr = game.p1_pos if game.current_player == 1 else game.p2_pos
            move_pos = (curr[0] + dr, curr[1] + dc)
            b_dr, b_dc = dirs[b_idx]
            build_pos = (move_pos[0] + b_dr, move_pos[1] + b_dc)
            
            r = game.step((move_pos, build_pos))
            
            if self.callback:
                self.callback({
                    "board": game.board.tolist(),
                    "p1_pos": game.p1_pos,
                    "p2_pos": game.p2_pos,
                    "current_player": game.current_player,
                    "winner": game.winner,
                    "last_move": {
                        "move": (move_pos[0], move_pos[1]),
                        "build": (build_pos[0], build_pos[1])
                    },
                    "step": step
                })
                time.sleep(0.5) # Slow down for visualization
            
            if r is not None: # Game ended
                return [(x[0], x[2], r * ((-1) ** (x[1] != game.current_player))) for x in train_examples]

    def learn(self):
        for i in range(1, self.args.num_episodes + 1):
            print(f"Episode {i}/{self.args.num_episodes}")
            examples = self.execute_episode()
            self.train(examples)
            
            # Save checkpoint
            torch.save(self.model.state_dict(), os.path.join(self.args.checkpoint_dir, 'best.pth.tar'))

    def train(self, examples):
        # examples: list of (board, pi, v)
        # Flatten list
        # In a real scenario, we'd use a replay buffer
        
        shuffle(examples)
        
        for epoch in range(self.args.epochs):
            self.model.train()
            batch_idx = 0
            while batch_idx < len(examples):
                sample_ids = np.random.randint(len(examples), size=self.args.batch_size)
                boards, pis, vs = list(zip(*[examples[i] for i in sample_ids]))
                
                boards = torch.FloatTensor(np.array(boards).astype(np.float64))
                target_pis = torch.FloatTensor(np.array(pis))
                target_vs = torch.FloatTensor(np.array(vs).astype(np.float64))
                
                if self.args.cuda:
                    boards, target_pis, target_vs = boards.to('mps'), target_pis.to('mps'), target_vs.to('mps')
                
                out_pi, out_v = self.model(boards)
                
                l_pi = -torch.sum(target_pis * out_pi) / target_pis.size(0)
                l_v = torch.sum((target_vs - out_v.view(-1)) ** 2) / target_vs.size(0)
                total_loss = l_pi + l_v
                
                self.optimizer.zero_grad()
                total_loss.backward()
                self.optimizer.step()
                
                batch_idx += self.args.batch_size

if __name__ == "__main__":
    trainer = Trainer()
    trainer.learn()
