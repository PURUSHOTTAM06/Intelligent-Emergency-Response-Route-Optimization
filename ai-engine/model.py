import torch
import torch.nn as nn
import torch.nn.functional as F

class DQNBrain(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(DQNBrain, self).__init__()
        # Layer 1: Processes the raw feature vector
        self.fc1 = nn.Linear(state_dim, 128)
        # Layer 2: Learns complex non-linear traffic patterns
        self.fc2 = nn.Linear(128, 64)
        # Layer 3: Outputs the Q-value for each possible direction
        self.fc3 = nn.Linear(64, action_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)