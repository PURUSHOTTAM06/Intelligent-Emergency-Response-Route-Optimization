import torch
import torch.optim as optim
import torch.nn as nn
import random
import numpy as np
from model import DQNBrain
from memory import ReplayMemory

class DQNAgent:
    def __init__(self, state_dim, action_dim):
        # Hardware acceleration check
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.action_dim = action_dim
        
        # Policy Net: The active network that the ambulance uses to decide moves
        self.policy_net = DQNBrain(state_dim, action_dim).to(self.device)
        # Target Net: A stable 'goal' network to prevent the AI from chasing its own tail
        self.target_net = DQNBrain(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=1e-3)
        self.memory = ReplayMemory(capacity=10000)
        self.gamma = 0.99 
        self.batch_size = 64

    def choose_action(self, state, epsilon):
        """Exploration vs Exploitation: Uses Epsilon to decide between random or smart moves"""
        if random.random() < epsilon:
            return random.randrange(self.action_dim)
        
        with torch.no_grad():
            # Convert state to tensor and push to GPU/CPU
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            return self.policy_net(state_t).argmax().item()

    def learn(self):
        """The core Deep Learning update using the Bellman Equation"""
        if len(self.memory) < self.batch_size:
            return None

        # 1. Sample a random batch of past experiences (Matrix Math starts here)
        transitions = self.memory.sample(self.batch_size)
        batch = list(zip(*transitions))

        state_batch = torch.FloatTensor(np.array(batch[0])).to(self.device)
        action_batch = torch.LongTensor(batch[1]).unsqueeze(1).to(self.device)
        reward_batch = torch.FloatTensor(batch[2]).to(self.device)
        next_state_batch = torch.FloatTensor(np.array(batch[3])).to(self.device)
        done_batch = torch.FloatTensor(batch[4]).to(self.device)

        # 2. Predict Q-values for current states
        current_q_values = self.policy_net(state_batch).gather(1, action_batch)

        # 3. Calculate 'Ideal' Q-values using the Target Network
        with torch.no_grad():
            max_next_q_values = self.target_net(next_state_batch).max(1)[0]
            # Bellman formula: Target = Reward + Gamma * Max_Future_Reward
            target_q_values = reward_batch + (self.gamma * max_next_q_values * (1 - done_batch))

        # 4. Compute Loss (MSE) - how far off was the ambulance's guess?
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)

        # 5. Backpropagation: Optimize the Neural Network weights
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping to prevent 'Exploding Gradients' common in RL
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        return loss.item()

    def update_target_network(self):
        """Syncs the stable network with the active network"""
        self.target_net.load_state_dict(self.policy_net.state_dict())