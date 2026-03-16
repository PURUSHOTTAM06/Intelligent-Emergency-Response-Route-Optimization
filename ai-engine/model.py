import torch
import torch.nn as nn
import torch.nn.functional as F

class JaipurNeuralEngine(nn.Module):
    def __init__(self, state_dim, action_dim):
        """
        Production-Grade Dueling Deep Q-Network.
        :param state_dim: Number of features per road (Length, Lanes, Time, etc.)
        :param action_dim: Number of possible next turns (Maximum branching factor)
        """
        super(JaipurNeuralEngine, self).__init__()
        
        # 1. Shared Feature Extraction Layer
        # This layer "learns" the general patterns of Jaipur's traffic
        self.feature_layer = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )
        
        # 2. The Value Stream (V)
        # Estimates the inherent "goodness" of being at a specific intersection
        self.value_stream = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        # 3. The Advantage Stream (A)
        # Estimates the relative benefit of taking each specific exit/road
        self.advantage_stream = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )

    def forward(self, state):
        """
        The Forward Pass: Combines Value and Advantage to get Q-Values.
        Formula: Q(s,a) = V(s) + (A(s,a) - Mean(A(s,a)))
        """
        features = self.feature_layer(state)
        
        value = self.value_stream(features)
        advantage = self.advantage_stream(features)
        
        # Aggregating Streams (Centered for stability)
        # This ensures the advantage is relative to the mean
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        
        return q_values

# --- PRODUCTION FEATURE: WEIGHT INITIALIZATION ---
def init_weights(m):
    """Xavier initialization is best for deep networks to prevent vanishing gradients."""
    if isinstance(m, nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight)
        m.bias.data.fill_(0.01)