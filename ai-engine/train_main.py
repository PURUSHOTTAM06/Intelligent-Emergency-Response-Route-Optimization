import torch
import random
import logging
import os
import osmnx as ox
import networkx as nx

# --- IMPORT MODULES ---
from environment import MultiCityTrafficEnv
from agent import AmbulanceAgent
from memory import ExperienceMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TRAINING_CORE")

# --- CONFIGURATION ---
CITIES = ["jaipur", "delhi", "allahabad", "bangalore"]
STATE_DIM = 6
ACTION_DIM = 8
BATCH_SIZE = 64
EPISODES = 1200  # Increased for multi-city generalization

# --- MULTI-SECTOR INITIALIZATION ---
city_envs = {}
logger.info("Initializing Global Neural Training...")

for city in CITIES:
    map_path = f"{city}_map.graphml"
    if os.path.exists(map_path):
        logger.info(f"🦾 Loading Sector: {city}...")
        try:
            # We must apply the connectivity fix here too, 
            # otherwise the AI will step into a dead-end and crash the loop.
            G = ox.load_graphml(map_path)
            scc = max(nx.strongly_connected_components(G), key=len) if G.is_directed() else max(nx.connected_components(G), key=len)
            clean_G = G.subgraph(scc).copy()
            
            env = MultiCityTrafficEnv(city, map_path)
            env.G = ox.project_graph(clean_G, to_crs="EPSG:4326")
            city_envs[city] = env
            logger.info(f"✅ {city.upper()} loaded into training matrix.")
        except Exception as e:
            logger.error(f"❌ Failed to load {city}: {e}")

if not city_envs:
    raise ValueError("CRITICAL: No maps found. Please ensure .graphml files exist.")

# --- AI AGENT SETUP ---
agent = AmbulanceAgent(STATE_DIM, ACTION_DIM)
memory = ExperienceMemory(capacity=50000) # Increased memory for multi-city experiences

print(f"\n🚀 CROSS-SECTOR TRAINING STARTED: {len(city_envs)} CITIES LIVE...")

for episode in range(EPISODES):
    # 1. Teleport AI to a random city for this episode
    target_city = random.choice(list(city_envs.keys()))
    env = city_envs[target_city]
    
    # 2. Simulate random hour traffic and get features
    # Assuming your env.simulate_traffic_step() assigns random traffic weights
    current_graph = env.simulate_traffic_step()
    features = env.get_feature_matrix()
    
    # 3. Drop the agent on a random road
    current_edge = random.choice(list(features.keys()))
    state = features[current_edge]
    
    total_reward = 0
    
    for step in range(120): # Max steps per dispatch
        # Agent chooses a path
        action = agent.select_action(state)
        
        # Find neighbors (connected roads)
        neighbors = list(current_graph.out_edges(current_edge[1], keys=True))
        
        if not neighbors: # Dead end trap
            reward = -20 # Heavy penalty for hitting dead ends
            done = True
            next_state = state 
        else:
            # Action maps to one of the neighboring edges
            next_edge = neighbors[action % len(neighbors)]
            next_state = features[next_edge]
            
            # REWARD FUNCTION: 
            # Penalize heavily for high ai_weight (traffic/time)
            raw_weight = current_graph[next_edge[0]][next_edge[1]][next_edge[2]].get('ai_weight', 10.0)
            reward = -raw_weight
            done = False
            current_edge = next_edge

        # Store experience in the global memory bank
        memory.push(state, action, reward, next_state, done)
        
        # Learn from past experiences
        agent.learn(memory, BATCH_SIZE)
        
        state = next_state
        total_reward += reward
        if done: break

    # Periodic Target Network Sync & Logging
    if episode % 20 == 0:
        agent.update_target_network()
        print(f"📊 EP: {episode:4d} | CITY: {target_city.upper():10s} | REWARD: {total_reward:7.2f} | EPSILON: {agent.epsilon:.3f}")

# --- SAVE THE GLOBAL BRAIN ---
torch.save(agent.policy_net.state_dict(), "ambulance_brain.pth")
print("\n✅ GLOBAL TRAINING COMPLETE: Multi-Sector Brain saved as 'ambulance_brain.pth'")