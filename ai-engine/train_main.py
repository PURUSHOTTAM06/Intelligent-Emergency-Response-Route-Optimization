import torch
import numpy as np
from environment import UrbanGraphEnv
from agent import DQNAgent

def train_ambulance_ai():
    # 1. Initialize Environment and Agent
    # State Dim: pos(1) + traffic(10) + incidents(10) = 21
    env = UrbanGraphEnv(num_nodes=10)
    agent = DQNAgent(state_dim=21, action_dim=10)
    
    # 2. Hyperparameters for the Learning Phase
    episodes = 1000
    epsilon = 1.0          # Starting exploration rate (100% random)
    epsilon_decay = 0.995  # Rate at which the AI stops guessing and starts 'thinking'
    min_epsilon = 0.05     # Minimum exploration to keep the AI adaptable
    target_update = 10     # Sync stable network every 10 episodes
    
    print("🚀 [INITIATING_DEEP_Q_TRAINING]...")
    print(f"📡 Device detected: {agent.device}")

    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            # Choose Action (Explore vs Exploit)
            action = agent.choose_action(state, epsilon)
            
            # Execute move in Stochastic Environment
            next_state, reward, done = env.step(action)
            
            # Store experience in Replay Memory
            agent.memory.push(state, action, reward, next_state, done)
            
            # Perform Neural Weight Update (The 'Heavy' AI part)
            loss = agent.learn()
            
            state = next_state
            total_reward += reward

        # Decay Epsilon: Get smarter every episode
        if epsilon > min_epsilon:
            epsilon *= epsilon_decay

        # Periodically sync Target Network for training stability
        if episode % target_update == 0:
            agent.update_target_network()

        # Console Progress Update
        if episode % 50 == 0:
            avg_loss = loss if loss else 0
            print(f"EPISODE_{episode:04d} | REWARD: {total_reward:.2f} | EPSILON: {epsilon:.2f} | LOSS: {avg_loss:.4f}")

    # 3. Save the Neural Weights for Deployment
    torch.save(agent.policy_net.state_dict(), "ambulance_dqn_v1.pth")
    print("\n✅ [TRAINING_COMPLETE]")
    print("💾 Model Weights Saved: 'ambulance_dqn_v1.pth'")

if __name__ == "__main__":
    train_ambulance_ai()