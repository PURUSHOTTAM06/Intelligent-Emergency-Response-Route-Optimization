import networkx as nx
import numpy as np

class UrbanGraphEnv:
    def __init__(self, size=5):
        self.size = size
        self.num_nodes = size * size
        self.start_node = (0, 0)
        self.hospital_node = (size-1, size-1)
        
        # Mapping 2D coords (0,0) to Flat IDs (0) for the Neural Network
        self.node_to_id = {node: i for i, node in enumerate(nx.grid_2d_graph(size, size).nodes())}
        self.id_to_node = {i: node for node, i in self.node_to_id.items()}
        
        # Directed Graph for realistic city routing
        self.G = nx.grid_2d_graph(size, size, create_using=nx.DiGraph())
        
        # Initialize industry-standard road physics
        for u, v in self.G.edges():
            self.G.edges[u, v].update({
                'length': 2.0, 
                'free_speed': 60,
                'capacity': 100,
                'current_flow': np.random.randint(20, 80),
                'has_accident': False
            })
        self.reset()

    def get_state(self):
        """
        Generates a 21-dimensional Feature Vector for the DQN:
        [1: Normalized Position] + [10: Local Traffic] + [10: Local Accidents]
        """
        # 1. Normalized Current Position
        pos_feat = np.array([self.node_to_id[self.current_pos] / self.num_nodes])
        
        # 2. Traffic & Accident data (Sampling first 10 edges for tensor consistency)
        traffic_feats = []
        accident_feats = []
        for i, (u, v) in enumerate(self.G.edges()):
            if i >= 10: break # Keep vector size fixed at 21
            traffic_feats.append(self.G.edges[u, v]['current_flow'] / 100)
            accident_feats.append(1.0 if self.G.edges[u, v]['has_accident'] else 0.0)
            
        state = np.concatenate([pos_feat, traffic_feats, accident_feats])
        return state.astype(np.float32)

    def get_travel_time(self, u, v):
        """BPR (Bureau of Public Roads) Traffic Physics"""
        edge = self.G.edges[u, v]
        cap = edge['capacity'] * 0.1 if edge['has_accident'] else edge['capacity']
        t_free = (edge['length'] / edge['free_speed']) * 60
        # Exponential congestion penalty
        t_actual = t_free * (1 + 0.15 * (edge['current_flow'] / cap)**4)
        return t_actual

    def step(self, action_id):
        """Accepts a Node ID (0-24) from the DQN and moves the ambulance"""
        action_node = self.id_to_node[action_id]
        
        if action_node not in self.G.neighbors(self.current_pos):
            # Penalty for invalid pathfinding move
            return self.get_state(), -100, False 
        
        time_penalty = self.get_travel_time(self.current_pos, action_node)
        self.current_pos = action_node
        
        done = (self.current_pos == self.hospital_node)
        reward = -time_penalty + (100 if done else 0)
        
        return self.get_state(), reward, done

    def reset(self):
        self.current_node_id = 0
        self.current_pos = self.start_node
        # Randomize traffic on reset to prevent the AI from 'overfitting'
        for u, v in self.G.edges():
            self.G.edges[u, v]['current_flow'] = np.random.randint(20, 90)
            self.G.edges[u, v]['has_accident'] = (np.random.random() > 0.9)
        return self.get_state()