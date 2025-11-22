import os
import numpy as np
import torch
import torch.optim as optim
from collections import deque
from random import shuffle
import sys
import logging
import time
import queue

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


class ReplayBuffer:
    """
    Fixed-size buffer to store training examples.
    """
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def push(self, examples):
        """Add a list of examples to the buffer."""
        for ex in examples:
            self.buffer.append(ex)

    def sample(self, batch_size):
        """Sample a batch of examples."""
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]

    def __len__(self):
        return len(self.buffer)

class Trainer:
    """
    Self-play training loop for SkyTowers.
    
    Generates training data through self-play games and trains the neural network.
    """
    
    def __init__(self, callback_queue: queue.Queue = None, train_duration_minutes: float = None):
        """
        Initialize trainer.
        
        Args:
            callback_queue: Thread-safe queue for pushing visualization updates
            train_duration_minutes: Optional training duration in minutes (None = use num_iterations)
        """
        self.args = Args()
        self.game = SkyTowersGame()
        self.model = SkyNet()
        self.callback_queue = callback_queue
        self.running = True  # Flag to control training loop
        self.train_duration_minutes = train_duration_minutes
        self.start_time = None
        
        # Move model to appropriate device
        self.device = 'mps' if self.args.cuda else 'cpu'
        self.model = self.model.to(self.device)
        logger.info(f"Model moved to device: {self.device}")
        
        # Load previous checkpoint if exists
        checkpoint_path = os.path.join(self.args.checkpoint_dir, 'best.pth.tar')
        if os.path.exists(checkpoint_path):
            self.load_checkpoint(checkpoint_path)
            logger.info("Continuing training from previous checkpoint")
        else:
            logger.info("Starting training from scratch")
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.args.lr)
        self.mcts = MCTS(self.game, self.model, self.args)
        
        # Replay Buffer
        self.replay_buffer = ReplayBuffer(self.args.buffer_size)
        
        # Learning metrics
        self.loss_history = []
        self.win_history = []  # 1 for P1 win, -1 for P2 win
        self.episode_lengths = []
        self.elo_rating = 1500  # Starting ELO
        
        # Create checkpoint directory
        if not os.path.exists(self.args.checkpoint_dir):
            os.makedirs(self.args.checkpoint_dir)
            logger.info(f"Created checkpoint directory: {self.args.checkpoint_dir}")

    def stop(self):
        """Signal the training loop to stop."""
        self.running = False

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
        
        while True:
            step += 1
            # Use high temperature for exploration in early moves
            temp = 1 if step < 10 else 0
            
            # Check for game end
            game_ended = game.getGameEnded()
            if game_ended != 0:
                final_value = game_ended
                
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
            
            # Push update to queue if available (non-blocking)
            if self.callback_queue:
                try:
                    update_data = {
                        "type": "game_update",
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
                    }
                    self.callback_queue.put_nowait(update_data)
                except queue.Full:
                    pass # Drop frame if queue is full

    def learn(self):
        """
        Main training loop: execute episodes and train model.
        """
        self.start_time = time.time()
        
        if self.train_duration_minutes:
            logger.info(f"Starting training for {self.train_duration_minutes} minutes")
            max_iterations = 10000  # Large number, will stop based on time
        else:
            logger.info(f"Starting training for {self.args.num_iterations} iterations")
            max_iterations = self.args.num_iterations
        
        for iteration in range(1, max_iterations + 1):
            # Check time limit
            if self.train_duration_minutes:
                elapsed_minutes = (time.time() - self.start_time) / 60
                if elapsed_minutes >= self.train_duration_minutes:
                    logger.info(f"Training duration reached ({self.train_duration_minutes} minutes)")
                    break
            
            if not self.running:
                logger.info("Training stopped by user request")
                break
            
            logger.info(f"=== Iteration {iteration}/{self.args.num_iterations} ===")
            
            # 1. Self-Play
            iteration_examples = []
            for _ in range(self.args.num_episodes):
                if not self.running: break
                iteration_examples += self.execute_episode()
            
            # 2. Save to Replay Buffer
            self.replay_buffer.push(iteration_examples)
            logger.info(f"Replay Buffer size: {len(self.replay_buffer)}")
            
            # 3. Train
            if len(self.replay_buffer) > self.args.batch_size:
                self.train()
            
            # 4. Save Checkpoint
            checkpoint_path = os.path.join(self.args.checkpoint_dir, f'checkpoint_{iteration}.pth.tar')
            self.save_checkpoint(checkpoint_path)
            
            # Save best model (latest for now)
            best_path = os.path.join(self.args.checkpoint_dir, 'best.pth.tar')
            self.save_checkpoint(best_path)
        
        logger.info("Training completed!")

    def save_checkpoint(self, filepath):
        """Save model and optimizer state."""
        state = {
            'state_dict': self.model.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'elo_rating': self.elo_rating,
            'loss_history': self.loss_history,
            'win_history': self.win_history
        }
        torch.save(state, filepath)

    def load_checkpoint(self, filepath):
        """Load model and optimizer state."""
        if os.path.exists(filepath):
            checkpoint = torch.load(filepath, map_location=self.device)
            self.model.load_state_dict(checkpoint['state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.elo_rating = checkpoint.get('elo_rating', 1500)
            self.loss_history = checkpoint.get('loss_history', [])
            self.win_history = checkpoint.get('win_history', [])
            logger.info(f"Loaded checkpoint from {filepath}")
        else:
            logger.warning(f"No checkpoint found at {filepath}")

    def train(self):
        """
        Train the neural network on examples from replay buffer.
        """
        self.model.train()
        
        for epoch in range(self.args.epochs):
            total_loss = 0
            num_batches = 0
            
            # Train on random batches
            # We'll do (buffer_size / batch_size) steps per epoch roughly, 
            # or just a fixed number of steps based on new data size
            num_steps = len(self.replay_buffer) // self.args.batch_size
            
            for _ in range(num_steps):
                batch = self.replay_buffer.sample(self.args.batch_size)
                boards, pis, vs = list(zip(*batch))
                
                # Convert to tensors
                boards = torch.FloatTensor(np.array(boards).astype(np.float32))
                target_pis = torch.FloatTensor(np.array(pis))
                target_vs = torch.FloatTensor(np.array(vs).astype(np.float32))
                
                # Move to device
                boards = boards.to(self.device)
                target_pis = target_pis.to(self.device)
                target_vs = target_vs.to(self.device)
                
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
            
            avg_loss = total_loss / num_batches if num_batches > 0 else 0
            
            # Track loss for last epoch
            if epoch == self.args.epochs - 1:
                self.loss_history.append(avg_loss)
        
        self.model.eval()
        
        # Send learning metrics to frontend
        if self.callback_queue and len(self.win_history) > 0:
            recent_wins = self.win_history[-20:] if len(self.win_history) >= 20 else self.win_history
            p1_win_rate = sum(1 for w in recent_wins if w == 1) / len(recent_wins)
            avg_episode_length = sum(self.episode_lengths[-20:]) / min(20, len(self.episode_lengths))
            
            # Update ELO based on recent performance
            if p1_win_rate > 0.55:
                self.elo_rating += 10
            elif p1_win_rate < 0.45:
                self.elo_rating -= 10
            
            try:
                self.callback_queue.put_nowait({
                    "type": "metrics",
                    "total_episodes": len(self.win_history),
                    "p1_win_rate": round(p1_win_rate * 100, 1),
                    "avg_loss": round(avg_loss, 4),
                    "avg_episode_length": round(avg_episode_length, 1),
                    "elo_rating": round(self.elo_rating),
                    "recent_losses": [round(l, 4) for l in self.loss_history[-10:]]
                })
            except queue.Full:
                pass

if __name__ == "__main__":
    trainer = Trainer()
    trainer.learn()
