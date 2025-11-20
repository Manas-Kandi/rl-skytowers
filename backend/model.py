import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

class SkyNet(nn.Module):
    """
    Neural network for SkyTowers game.
    
    Architecture:
    - Shared convolutional trunk for feature extraction
    - Policy head: outputs probability distribution over actions
    - Value head: outputs game value estimate
    
    Action space: 64 (8 move directions × 8 build directions)
    """
    
    def __init__(self, board_size: int = 5, num_channels: int = 4, action_size: int = 64):
        """
        Initialize the SkyNet model.
        
        Args:
            board_size: Size of the game board (default 5x5)
            num_channels: Number of input channels (default 4: p1, p2, board, player_id)
            action_size: Number of possible actions (default 64)
        """
        super(SkyNet, self).__init__()
        self.board_size = board_size
        self.action_size = action_size 
        
        # Common trunk
        self.conv1 = nn.Conv2d(num_channels, 64, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        self.conv2 = nn.Conv2d(64, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 64, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        
        # Policy Head
        self.p_conv = nn.Conv2d(64, 2, 1) # 1x1 conv
        self.p_bn = nn.BatchNorm2d(2)
        self.p_fc = nn.Linear(2 * board_size * board_size, self.action_size)
        
        # Value Head
        self.v_conv = nn.Conv2d(64, 1, 1)
        self.v_bn = nn.BatchNorm2d(1)
        self.v_fc1 = nn.Linear(board_size * board_size, 64)
        self.v_fc2 = nn.Linear(64, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, num_channels, board_size, board_size)
            
        Returns:
            Tuple of (policy_logits, value_estimate)
            - policy_logits: Shape (batch_size, action_size), log probabilities
            - value_estimate: Shape (batch_size, 1), value in [-1, 1]
        """
        # Shared trunk: extract features
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))
        
        # Policy head: output action probabilities
        p = F.relu(self.p_bn(self.p_conv(x)))
        p = p.view(p.size(0), -1)  # Flatten
        p = self.p_fc(p)
        p = F.log_softmax(p, dim=1)
        
        # Value head: output game value estimate
        v = F.relu(self.v_bn(self.v_conv(x)))
        v = v.view(v.size(0), -1)  # Flatten
        v = F.relu(self.v_fc1(v))
        v = torch.tanh(self.v_fc2(v))
        
        return p, v
