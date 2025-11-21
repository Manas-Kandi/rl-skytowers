import os
import numpy as np
import torch
import torch.optim as optim
from collections import deque
from random import shuffle
import sys
import logging
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from game import SkyTowersGame
from model import SkyNet
from mcts import MCTS, Args

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Trainer:
    """
    Self-play training loop for SkyTowers.
    
    Generates training data through self-play games and trains the neural network.
    """
    
    def __init__(self, callback=None):
        """
        Initialize trainer.
        
        Args:
            callback: Optional callback function for training updates
        """
        self.args = Args()
        self.game = SkyTowersGame()
        self.model = SkyNet()
        self.callback = callback
        
        # Move model to appropriate device
        device = 'mps' if self.args.cuda else 'cpu'
        self.model = self.model.to(device)
        logger.info(f"Model moved to device: {device}")
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.args.lr)
        self.mcts = MCTS(self.game, self.model, self.args)
        
        # Learning metrics
        self.loss_history = []
        self.win_history = []  # 1 for P1 win, -1 for P2 win
        self.episode_lengths = []
        self.elo_rating = 1500  # Starting ELO
        
        # Create checkpoint directory
        if not os.path.exists(self.args.checkpoint_dir):
            os.makedirs(self.args.checkpoint_dir)
            logger.info(f"Created checkpoint directory: {self.args.checkpoint_dir}")

    def execute_episode(self):
        """
        Execute a single self-play episode.
        
        Returns:
            List of (state, policy, value) tuples for training
        """
        train_examples = []
        game = SkyTowersGame()
        self.mcts = MCTS(game, self.model, self.args)
        step = 0
        
        logger.info("Starting new episode")
        
        while True:
            step += 1
            # Use high temperature for exploration in early moves
            temp = 1 if step < 10 else 0
            
            # Check for game end
            game_ended = game.getGameEnded()
            if game_ended != 0:
                final_value = game_ended
                logger.info(f"Episode ended after {step} steps. Winner: {final_value}")
                
                # Track metrics
                self.win_history.append(final_value)
                self.episode_lengths.append(step)
                
                # Assign final value to all states
                return [(x[0], x[2], final_value * ((-1) ** (x[1] != game.current_player))) 
                        for x in train_examples]

            # Get action probabilities from MCTS
            pi = self.mcts.getActionProb(game, temp=temp)
            state = game.get_state()
            
            # Store training example
            train_examples.append([state, game.current_player, pi, None])
            
            # Sample action from policy
            action_idx = np.random.choice(len(pi), p=pi)
            
            # Decode action to move and build positions
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
            
            # Execute move
            game.step((move_pos, build_pos))
            
            # Send callback for visualization
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
                time.sleep(0.5)  # Slow down for visualization

    def learn(self):
        """
        Main training loop: execute episodes and train model.
        """
        logger.info(f"Starting training for {self.args.num_episodes} episodes")
        
        for episode_num in range(1, self.args.num_episodes + 1):
            logger.info(f"=== Episode {episode_num}/{self.args.num_episodes} ===")
            
            # Execute self-play episode
            examples = self.execute_episode()
            logger.info(f"Collected {len(examples)} training examples")
            
            # Train model on collected data
            self.train(examples)
            
            # Save checkpoint
            checkpoint_path = os.path.join(self.args.checkpoint_dir, 'best.pth.tar')
            torch.save(self.model.state_dict(), checkpoint_path)
            logger.info(f"Saved checkpoint to {checkpoint_path}")
        
        logger.info("Training completed!")

    def train(self, examples):
        """
        Train the neural network on collected examples.
        
        Args:
            examples: List of (state, policy, value) tuples
        """
        logger.info(f"Training on {len(examples)} examples for {self.args.epochs} epochs")
        
        shuffle(examples)
        
        for epoch in range(self.args.epochs):
            self.model.train()
            batch_idx = 0
            total_loss = 0
            num_batches = 0
            
            while batch_idx < len(examples):
                # Sample random batch
                sample_ids = np.random.randint(len(examples), size=self.args.batch_size)
                boards, pis, vs = list(zip(*[examples[i] for i in sample_ids]))
                
                # Convert to tensors
                boards = torch.FloatTensor(np.array(boards).astype(np.float32))
                target_pis = torch.FloatTensor(np.array(pis))
                target_vs = torch.FloatTensor(np.array(vs).astype(np.float32))
                
                # Move to device
                device = 'mps' if self.args.cuda else 'cpu'
                boards = boards.to(device)
                target_pis = target_pis.to(device)
                target_vs = target_vs.to(device)
                
                # Forward pass
                out_pi, out_v = self.model(boards)
                
                # Compute loss
                l_pi = -torch.sum(target_pis * out_pi) / target_pis.size(0)
                l_v = torch.sum((target_vs - out_v.view(-1)) ** 2) / target_vs.size(0)
                loss = l_pi + l_v
                
                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
                num_batches += 1
                batch_idx += self.args.batch_size
            
            avg_loss = total_loss / num_batches if num_batches > 0 else 0
            logger.info(f"Epoch {epoch + 1}/{self.args.epochs} - Loss: {avg_loss:.4f}")
            
            # Track loss for last epoch
            if epoch == self.args.epochs - 1:
                self.loss_history.append(avg_loss)
        
        self.model.eval()
        logger.info("Training epoch completed")
        
        # Send learning metrics to frontend
        if self.callback and len(self.win_history) > 0:
            recent_wins = self.win_history[-20:] if len(self.win_history) >= 20 else self.win_history
            p1_win_rate = sum(1 for w in recent_wins if w == 1) / len(recent_wins)
            avg_episode_length = sum(self.episode_lengths[-20:]) / min(20, len(self.episode_lengths))
            
            # Update ELO based on recent performance
            if p1_win_rate > 0.55:
                self.elo_rating += 10
            elif p1_win_rate < 0.45:
                self.elo_rating -= 10
            
            self.callback({
                "type": "metrics",
                "total_episodes": len(self.win_history),
                "p1_win_rate": round(p1_win_rate * 100, 1),
                "avg_loss": round(avg_loss, 4),
                "avg_episode_length": round(avg_episode_length, 1),
                "elo_rating": round(self.elo_rating),
                "recent_losses": [round(l, 4) for l in self.loss_history[-10:]]
            })

if __name__ == "__main__":
    trainer = Trainer()
    trainer.learn()
