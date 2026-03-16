import torch
import torch.optim as optim
import torch.nn as nn
import numpy as np
import random
from model import JaipurNeuralEngine # Importing your Dueling DQN

class AmbulanceAgent:
    def __init__(self, state_dim, action_dim, lr=1e-4, gamma=0.99):
        self.action_dim = action_dim
        self.gamma = gamma # Discount factor: how much we value future speed
        
        # 1. Two Networks for Stability (Production Standard)
        self.policy_net = JaipurNeuralEngine(state_dim, action_dim)
        self.target_net = JaipurNeuralEngine(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        
        # 2. Epsilon-Greedy Parameters
        self.epsilon = 1.0 # Start with 100% exploration
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995

    def select_action(self, state):
        """
        Exploration vs. Exploitation Trade-off.
        """
        if random.random() < self.epsilon:
            return random.randrange(self.action_dim) # Explore: Take a random road
        
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.policy_net(state_t)
            return q_values.argmax().item() # Exploit: Take the AI's best road

    def learn(self, memory, batch_size):
        """
        The Optimization Loop.
        """
        if len(memory) < batch_size:
            return

        # 1. Sample from Experience Replay
        states, actions, rewards, next_states, dones = memory.sample(batch_size)

        # 2. Get Current Q-Values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))

        # 3. Get Target Q-Values (Double DQN Logic)
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (self.gamma * next_q * (~dones))

        # 4. Backpropagation
        loss = self.criterion(current_q.squeeze(), target_q)
        self.optimizer.zero_grad()
        loss.backward()
        
        # Clip Gradients (Production Trick: Prevents the model from 'exploding')
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # 5. Decay Exploration
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def update_target_network(self):
        """Synchronizes the target net with the policy net."""
        self.target_net.load_state_dict(self.policy_net.state_dict())