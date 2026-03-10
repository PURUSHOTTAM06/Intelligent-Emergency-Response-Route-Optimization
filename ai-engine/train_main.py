import torch
import numpy as np
from environment import UrbanGraphEnv
from agent import DQNAgent

def train_ambulance_ai():
    env = UrbanGraphEnv(size=5)
    agent = DQNAgent(state_dim=21, action_dim=25)
    
    episodes = 800
    max_steps = 50
    epsilon = 1.0
    epsilon_decay = 0.996 # Slower decay for better exploration
    
    print("🚀 [INITIATING_DEEP_Q_TRAINING]...")

    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        for _ in range(max_steps):
            action = agent.choose_action(state, epsilon)
            next_state, reward, done = env.step(action)
            agent.memory.push(state, action, reward, next_state, done)
            agent.learn()
            state, total_reward = next_state, total_reward + reward
            if done: break

        epsilon = max(0.05, epsilon * epsilon_decay)
        if episode % 10 == 0:
            agent.update_target_network()
            print(f"EP_{episode:03d} | RWD: {total_reward:.1f} | EPS: {epsilon:.2f}")

    torch.save(agent.policy_net.state_dict(), "ambulance_dqn_v1.pth")
    print("\n✅ [TRAINING_COMPLETE]")

if __name__ == "__main__":
    train_ambulance_ai()