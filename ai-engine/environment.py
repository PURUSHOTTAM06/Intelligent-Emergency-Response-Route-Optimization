import networkx as nx
import numpy as np

class EmergencyEnv:
    def __init__(self, size=5):
        self.size = size
        # Starting Point: Top-Left (0,0)
        # Goal (Hospital): Bottom-Right (4,4)
        self.start_node = (0, 0)
        self.hospital_node = (size-1, size-1)
        
        # Create a directed grid graph (roads)
        self.G = nx.grid_2d_graph(size, size, create_using=nx.DiGraph())
        
        # Initialize road physics for every edge
        for u, v in self.G.edges():
            self.G.edges[u, v].update({
                'length': 2.0,          # 2 km per block
                'free_speed': 60,       # 60 km/h
                'capacity': 100,        # Max vehicles per hour
                'current_flow': 20,     # Initial background traffic
                'has_accident': False
            })
        
        self.reset()

    def reset(self):
        """Resets the ambulance to the start and clears the map"""
        self.current_pos = self.start_node
        for u, v in self.G.edges():
            self.G.edges[u, v]['has_accident'] = False
        return self.current_pos

    def get_travel_time(self, u, v):
        """BPR Formula: Calculates minutes to cross a road"""
        edge = self.G.edges[u, v]
        # Bottleneck: Accident reduces capacity by 90%
        cap = edge['capacity'] * 0.1 if edge['has_accident'] else edge['capacity']
        
        t_free = (edge['length'] / edge['free_speed']) * 60
        # Time = FreeTime * (1 + 0.15 * (flow/capacity)^4)
        t_actual = t_free * (1 + 0.15 * (edge['current_flow'] / cap)**4)
        return t_actual

    def step(self, action_node):
        """
        Moves the ambulance to the chosen next intersection.
        Returns: (new_position, reward, is_done)
        """
        # 1. Validation: Is the move possible?
        if action_node not in self.G.neighbors(self.current_pos):
            return self.current_pos, -100, False # Big penalty for trying to teleport
        
        # 2. Calculate the 'Cost' (Travel Time)
        travel_time = self.get_travel_time(self.current_pos, action_node)
        
        # 3. Update Position
        self.current_pos = action_node
        
        # 4. Check if we reached the Hospital
        done = (self.current_pos == self.hospital_node)
        
        # 5. Calculate Reward: Negative travel time + bonus for arriving
        reward = -travel_time 
        if done:
            reward += 100 # Large incentive for success
            
        return self.current_pos, reward, done

# --- TEST THE ENVIRONMENT ---
if __name__ == "__main__":
    env = EmergencyEnv()
    print("🚑 Environment Initialized.")
    print(f"Ambulance at: {env.current_pos}")
    
    # Simulate a crash at (0,0) -> (0,1)
    env.G.edges[(0,0), (0,1)]['has_accident'] = True
    print("⚠️ Accident injected at (0,0) -> (0,1)")
    
    # Try to move there
    pos, rew, done = env.step((0,1))
    print(f"Moved to: {pos} | Reward (Time Penalty): {rew:.2f} mins")