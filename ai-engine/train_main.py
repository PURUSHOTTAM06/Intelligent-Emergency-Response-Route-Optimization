from environment import JaipurTrafficEnv
from agent import AmbulanceAgent
from memory import ExperienceMemory
import torch
import random
# --- CONFIGURATION ---
MAP_PATH = "jaipur_map.graphml"
STATE_DIM = 6 # Features we defined in Step 1
ACTION_DIM = 8 # Max branching factor (typical for intersections)
BATCH_SIZE = 64
EPISODES = 500

# --- INITIALIZATION ---
env = JaipurTrafficEnv(MAP_PATH)
agent = AmbulanceAgent(STATE_DIM, ACTION_DIM)
memory = ExperienceMemory(capacity=20000)

print("🚀 TRAINING_STARTED: Simulated Jaipur Emergency Dispatch...")

for episode in range(EPISODES):
    # 1. Reset Env and get Initial State
    # Note: For our graph, a state is the feature vector of the current road
    current_graph = env.simulate_traffic_step()
    features = env.get_feature_matrix()
    
    # Let's pick a random start edge for training
    current_edge = random.choice(list(features.keys()))
    state = features[current_edge]
    
    total_reward = 0
    
    for step in range(100): # Max steps per dispatch
        # 2. Agent chooses a road
        action = agent.select_action(state)
        
        # 3. Step Environment (Find neighbors and move)
        # In a real graph, we'd find actual connected edges. 
        # For training, we simulate the 'next' state based on graph connectivity.
        neighbors = list(current_graph.out_edges(current_edge[1], keys=True))
        
        if not neighbors: # Dead end
            reward = -10
            done = True
            next_state = state # Stay in place
        else:
            # Action maps to one of the neighboring edges
            next_edge = neighbors[action % len(neighbors)]
            next_state = features[next_edge]
            
            # REWARD: Negative of the AI Weight (Time/Congestion)
            # We want to MINIMIZE time, so we MAXIMIZE negative time
            reward = -current_graph[next_edge[0]][next_edge[1]][next_edge[2]]['ai_weight']
            done = False
            current_edge = next_edge

        # 4. Store and Learn
        memory.push(state, action, reward, next_state, done)
        agent.learn(memory, BATCH_SIZE)
        
        state = next_state
        total_reward += reward
        if done: break

    # 5. Periodic Target Network Sync
    if episode % 10 == 0:
        agent.update_target_network()
        print(f"📊 EPISODE {episode} | AVG_REWARD: {total_reward:.2f} | EPSILON: {agent.epsilon:.2f}")

# 6. Save the Brain
torch.save(agent.policy_net.state_dict(), "ambulance_brain.pth")
print("✅ TRAINING_COMPLETE: model saved as ambulance_brain.pth")