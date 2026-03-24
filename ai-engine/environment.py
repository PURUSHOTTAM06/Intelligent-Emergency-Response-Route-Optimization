import os
import pickle
import osmnx as ox
import networkx as nx
import numpy as np
import datetime
import math

class MultiCityTrafficEnv:
    def __init__(self, city_id, graph_path):
        self.city_id = city_id
        print(f"📡 INITIALIZING_ENV: Loading {city_id.upper()} Sector Map...")
        
        # --- THE GEOSPATIAL BRIDGE (Hybrid Loader) ---
        if graph_path.endswith('.pkl'):
            with open(graph_path, 'rb') as f:
                raw_G = pickle.load(f)
        else:
            raw_G = ox.load_graphml(graph_path)
            
        # Lat/Lng for Frontend, Projected for AI Math
        self.G = ox.project_graph(raw_G, to_crs="EPSG:4326")
        self.G_proj = raw_G 
        
        self.nodes = list(self.G_proj.nodes())
        self.edges = list(self.G_proj.edges(data=True, keys=True))
        
        # --- PERSISTENT TOPOLOGY CACHE ---
        cache_dir = "topology_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        cache_file = os.path.join(cache_dir, f"{city_id}_centrality.pkl")
        
        if os.path.exists(cache_file):
            print(f"🧠 CACHE_FOUND: Loading {city_id} Bottleneck Data...")
            with open(cache_file, 'rb') as f:
                self.centrality = pickle.load(f)
        else:
            print(f"🧠 ANALYZING_TOPOLOGY: Calculating {city_id} (First time only)...")
            self.centrality = nx.betweenness_centrality(
                nx.Graph(self.G_proj), 
                k=min(len(self.nodes), 50), 
                weight='length',
                normalized=True
            )
            with open(cache_file, 'wb') as f:
                pickle.dump(self.centrality, f)
        
        self.current_time = datetime.datetime.now()
        self.state_dim = 6 
        
    def _get_temporal_features(self, target_hour=None):
        if target_hour is not None:
            hour = float(target_hour)
        else:
            hour = self.current_time.hour + self.current_time.minute / 60.0
            
        h_sin = math.sin(2 * math.pi * hour / 24)
        h_cos = math.cos(2 * math.pi * hour / 24)
        return h_sin, h_cos

    def _map_highway_type(self, h_type):
        mapping = {
            'motorway': 1.0, 'trunk': 0.8, 'primary': 0.6, 
            'secondary': 0.4, 'tertiary': 0.2, 'residential': 0.1
        }
        if isinstance(h_type, list): h_type = h_type[0]
        return mapping.get(h_type, 0.1)

    def get_feature_matrix(self, target_hour=None):
        h_sin, h_cos = self._get_temporal_features(target_hour)
        feature_dict = {}

        for u, v, k, data in self.edges:
            length = data.get('length', 0) / 1000.0 
            lanes_raw = data.get('lanes', 1)
            if isinstance(lanes_raw, list): lanes_raw = lanes_raw[0]
            lanes = int(lanes_raw) if str(lanes_raw).isdigit() else 1
            
            h_type_val = self._map_highway_type(data.get('highway', 'residential'))
            node_centrality = self.centrality.get(u, 0)
            
            feature_vector = np.array([
                length, 
                min(lanes / 5.0, 1.0), 
                h_type_val,
                node_centrality,
                h_sin,
                h_cos
            ])
            feature_dict[(u, v, k)] = feature_vector
            
        return feature_dict

    def simulate_traffic_step(self, target_hour=None):
        h_sin, _ = self._get_temporal_features(target_hour)
        base_congestion = max(1.1, (abs(h_sin) * 3.0) + np.random.normal(0, 0.1))

        for u, v, k, data in self.edges:
            lanes_raw = data.get('lanes', 1)
            if isinstance(lanes_raw, list): lanes_raw = lanes_raw[0]
            lanes = int(lanes_raw) if str(lanes_raw).isdigit() else 1
            centrality_impact = self.centrality.get(u, 0) * 15
            data['ai_weight'] = (data['length'] * base_congestion * (1 + centrality_impact)) / lanes

        return self.G_proj