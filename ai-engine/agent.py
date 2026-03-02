import numpy as np
import random
import pickle
from environment import EmergencyEnv

class QLearningAgent:
    def __init__(self, env, learning_rate=0.1, discount_factor=0.9, epsilon=1.0):
        self.env = env
        self.lr = learning_rate
        self.gamma = discount_factor # Importance of future rewards
        self.epsilon = epsilon       # Exploration rate (start by being random)
        self.epsilon_decay = 0.995   # Get smarter over time
        
        # Initialize Q-Table with zeros
        # State: (x, y) coordinates | Actions: Up, Down, Left, Right
        self.q_table = {}

    def get_q_value(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state):
        """Epsilon-Greedy: Sometimes explore, sometimes use the Cheat Sheet"""
        neighbors = list(self.env.G.neighbors(state))
        
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(neighbors) # Explore randomly
        else:
            # Look at the Q-table and pick the best road
            q_values = [self.get_q_value(state, a) for a in neighbors]
            max_q = max(q_values)
            # Handle multiple roads with the same best score
            best_actions = [a for i, a in enumerate(neighbors) if q_values[i] == max_q]
            return random.choice(best_actions)

    def learn(self, state, action, reward, next_state):
        """Update the Cheat Sheet using the Q-Learning Formula"""
        old_value = self.get_q_value(state, action)
        
        # What is the best we can do from the next intersection?
        next_neighbors = list(self.env.G.neighbors(next_state))
        next_max = max([self.get_q_value(next_state, a) for a in next_neighbors]) if next_neighbors else 0
        
        # The core Q-Learning Formula (Bellman Equation)
        new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
        self.q_table[(state, action)] = new_value

# --- TRAINING LOOP ---
if __name__ == "__main__":
    env = EmergencyEnv()
    agent = QLearningAgent(env)
    
    print("🚀 Training the Ambulance AI...")
    for episode in range(500): # Run the simulation 500 times
        state = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            agent.learn(state, action, reward, next_state)
            state = next_state
            total_reward += reward
        
        # Decay epsilon: Explore less as we learn more
        agent.epsilon *= agent.epsilon_decay
        
        if (episode + 1) % 100 == 0:
            print(f"Episode {episode + 1}: Total Penalty: {total_reward:.2f}")

    print("✅ Training Complete!")
    # Save the Q-table to a file
    with open("ambulance_brain.pkl", "wb") as f:
        pickle.dump(agent.q_table, f)
    print("💾 AI Brain saved as ambulance_brain.pkl")