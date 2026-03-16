import torch
import osmnx as ox
import matplotlib.pyplot as plt
import numpy as np
from environment import JaipurTrafficEnv
from model import JaipurNeuralEngine

def visualize_ai_intelligence(model_path, graph_path):
    # 1. Setup Environment and Brain
    env = JaipurTrafficEnv(graph_path)
    brain = JaipurNeuralEngine(state_dim=6, action_dim=8)
    brain.load_state_dict(torch.load(model_path))
    brain.eval()

    # 2. Extract Features for every edge in the city
    features = env.get_feature_matrix()
    edge_values = []

    print("🛰️  SCANNING_SECTOR: Analyzing Neural Value Map of Jaipur...")
    
    with torch.no_grad():
        for edge_id, feat_vector in features.items():
            state_t = torch.FloatTensor(feat_vector).unsqueeze(0)
            # The 'Value' stream tells us how 'good' the AI thinks this road is
            # We take the mean of the Q-values as a general 'Quality' score
            q_values = brain(state_t)
            score = torch.mean(q_values).item()
            edge_values.append(score)

    # 3. Normalize scores for coloring (0 to 1)
    norm_values = (edge_values - np.min(edge_values)) / (np.max(edge_values) - np.min(edge_values))

    # 4. Color Mapping: Red (Bad/Slow) -> Green (Good/Fast)
    colors = plt.cm.RdYlGn(norm_values)

    # 5. Plot the result
    print("🎨 RENDERING: Generating Spatiotemporal Intelligence Map...")
    fig, ax = ox.plot_graph(
        env.G_proj, 
        edge_color=colors, 
        edge_linewidth=2, 
        node_size=0, 
        bgcolor='#0a0a0a', # Professional Dark Mode
        show=False, 
        close=False
    )
    
    plt.title("AI_DISPATCH_OS: NEURAL VALUE MAP (JAIPUR)", color='white', fontsize=15)
    plt.show()

if __name__ == "__main__":
    if os.path.exists("ambulance_brain.pth"):
        visualize_ai_intelligence("ambulance_brain.pth", "jaipur_map.graphml")
    else:
        print("🚨 ERROR: No trained model found. Run train_main.py first!")