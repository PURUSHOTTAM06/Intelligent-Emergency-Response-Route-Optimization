import random
import collections
import torch

class ExperienceMemory:
    def __init__(self, capacity=10000):
        # We use a deque with a fixed max length to automatically discard old memories
        self.buffer = collections.deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """Stores a transition tuple in memory."""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        """Randomly samples a batch of experiences for the training loop."""
        transitions = random.sample(self.buffer, batch_size)
        
        # Unpack and convert to Torch Tensors for GPU/CPU acceleration
        states, actions, rewards, next_states, dones = zip(*transitions)
        
        return (
            torch.FloatTensor(states),
            torch.LongTensor(actions),
            torch.FloatTensor(rewards),
            torch.FloatTensor(next_states),
            torch.BoolTensor(dones)
        )

    def __len__(self):
        return len(self.buffer)