import networkx as nx
import numpy as np

class UrbanGraphEnv:
    def __init__(self, size=5):
        self.size = size
        self.num_nodes = size * size
        self.start_node = (0, 0)
        self.hospital_node = (size-1, size-1)
        
        self.G = nx.grid_2d_graph(size, size, create_using=nx.DiGraph())
        self.node_to_id = {node: i for i, node in enumerate(self.G.nodes())}
        self.id_to_node = {i: node for node, i in self.node_to_id.items()}
        
        for u, v in self.G.edges():
            self.G.edges[u, v].update({
                'length': 2.0, 'capacity': 100,
                'current_flow': np.random.randint(20, 80),
                'has_accident': False
            })
        self.reset()

    def get_state(self):
        pos_feat = np.array([self.node_to_id[self.current_pos] / self.num_nodes])
        traffic_feats = []
        accident_feats = []
        for i, (u, v) in enumerate(self.G.edges()):
            if i >= 10: break 
            traffic_feats.append(self.G.edges[u, v]['current_flow'] / 100)
            accident_feats.append(1.0 if self.G.edges[u, v]['has_accident'] else 0.0)
        return np.concatenate([pos_feat, traffic_feats, accident_feats]).astype(np.float32)

    def step(self, action_id):
        action_node = self.id_to_node[action_id]
        # Illegal move check
        if action_node not in self.G.neighbors(self.current_pos):
            return self.get_state(), -500, False 
        
        edge = self.G.edges[self.current_pos, action_node]
        # BPR formula for time
        t_actual = 2.0 * (1 + 0.15 * (edge['current_flow'] / edge['capacity'])**4)
        
        self.current_pos = action_node
        done = (self.current_pos == self.hospital_node)
        
        # REWARD LOGIC: Time penalty + constant step penalty + big goal reward
        reward = -t_actual - 5 + (300 if done else 0) 
        return self.get_state(), reward, done

    def reset(self):
        self.current_pos = self.start_node
        return self.get_state()