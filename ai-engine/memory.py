import random
from collections import deque

class ReplayMemory:
    def __init__(self, capacity=10000):
        # Circular buffer for memory efficiency
        self.memory = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        # Sampling prevents the agent from over-learning a single trip
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)