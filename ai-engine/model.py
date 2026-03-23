import torch
import torch.nn as nn
import torch.nn.functional as F

class RouteNeuralEngine(nn.Module):
    def __init__(self, state_dim, action_dim):
        """
        Dueling Deep Q-Network for Spatiotemporal Routing.
        :param state_dim: 6 Features (Length, Lanes, Type, Centrality, Sin_Time, Cos_Time)
        :param action_dim: Max road exits at an intersection
        """
        super(RouteNeuralEngine, self).__init__()
        
        # 1. SHARED FEATURE EXTRACTION
        # Learns the underlying logic of urban infrastructure
        self.feature_layer = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )
        
        # 2. VALUE STREAM (V)
        # Estimates the 'Value' of the current state regardless of action
        self.value_stream = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        # 3. ADVANTAGE STREAM (A)
        # Estimates the relative benefit of each specific road choice
        self.advantage_stream = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )
        
        # Apply Xavier Initialization
        self.apply(self.init_weights)

    def init_weights(self, m):
        if isinstance(m, nn.Linear):
            torch.nn.init.xavier_uniform_(m.weight)
            m.bias.data.fill_(0.01)

    def forward(self, state):
        """
        Combines Value and Advantage to produce final Q-values.
        Equation: $$Q(s, a) = V(s) + \left(A(s, a) - \frac{1}{|A|} \sum_{a'} A(s, a')\right)$$
        """
        features = self.feature_layer(state)
        
        value = self.value_stream(features)
        advantage = self.advantage_stream(features)
        
        # Combining streams using the mean-centering advantage logic
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        
        return q_values