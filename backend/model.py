import torch
import torch.nn as nn
import torch.nn.functional as F

class SkyNet(nn.Module):
    def __init__(self, board_size=5, num_channels=3, action_size=128): # 8 moves * 8 builds = 64. Let's reserve more just in case or use a simpler encoding.
        # Actually, let's refine action space.
        # 8 directions for move, 8 directions for build. 
        # 0-7: Move N, NE, E, SE, S, SW, W, NW
        # 0-7: Build N, ...
        # Total actions = 64.
        super(SkyNet, self).__init__()
        self.board_size = board_size
        self.action_size = 64 
        
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

    def forward(self, x):
        # x: (batch, 3, 5, 5)
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))
        
        # Policy
        p = F.relu(self.p_bn(self.p_conv(x)))
        p = p.view(-1, 2 * self.board_size * self.board_size)
        p = self.p_fc(p)
        p = F.log_softmax(p, dim=1)
        
        # Value
        v = F.relu(self.v_bn(self.v_conv(x)))
        v = v.view(-1, self.board_size * self.board_size)
        v = F.relu(self.v_fc1(v))
        v = torch.tanh(self.v_fc2(v))
        
        return p, v
