import torch
import torch.optim as optim
import torch.nn as nn
import numpy as np
import random

# Ensure your model.py has the generic 'RouteNeuralEngine' name
from model import RouteNeuralEngine 

class AmbulanceAgent:
    def __init__(self, state_dim, action_dim, lr=1e-4, gamma=0.99):
        self.action_dim = action_dim
        self.gamma = gamma 
        
        # 1. Double DQN Architecture
        self.policy_net = RouteNeuralEngine(state_dim, action_dim)
        self.target_net = RouteNeuralEngine(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        
        # 2. Epsilon-Greedy (Exploration vs. Exploitation)
        self.epsilon = 1.0 
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995

    def select_action(self, state):
        """
        Picks the best road based on the current 6-feature state vector.
        """
        if random.random() < self.epsilon:
            return random.randrange(self.action_dim)
        
        with torch.no_grad():
            # state is [length, lanes, type, centrality, sin_time, cos_time]
            state_t = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.policy_net(state_t)
            return q_values.argmax().item()

    def learn(self, memory, batch_size):
        """
        Standard DQN Optimization with Double DQN Target Calculation
        """
        if len(memory) < batch_size:
            return

        # 1. Sample Replay Memory
        states, actions, rewards, next_states, dones = memory.sample(batch_size)

        # 2. Predict Q-values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))

        # 3. Calculate Target Q-values (The Bellman Equation Logic)
        with torch.no_grad():
            # Double DQN: Use target_net for the next state evaluation
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (self.gamma * next_q * (1 - dones.float()))

        # 4. Backprop
        loss = self.criterion(current_q.squeeze(), target_q)
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient Clipping: Prevents the AI from 'forgetting' everything during a traffic spike
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # 5. Decay Exploration
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def update_target_network(self):
        """Hard sync of weights every N episodes."""
        self.target_net.load_state_dict(self.policy_net.state_dict())