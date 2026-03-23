import torch
import osmnx as ox
import networkx as nx
import os
import logging
import uvicorn
import numpy as np
import random
import math
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from environment import MultiCityTrafficEnv 
from agent import AmbulanceAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_ENGINE")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load Neural Brain
STATE_DIM, ACTION_DIM = 6, 8
agent = AmbulanceAgent(STATE_DIM, ACTION_DIM)
if os.path.exists("ambulance_brain.pth"):
    agent.policy_net.load_state_dict(torch.load("ambulance_brain.pth", map_location=torch.device('cpu')))
    agent.policy_net.eval()

# --- HIGH-SPEED SECTOR INIT ---
city_list = ["jaipur", "delhi", "allahabad", "bangalore"]
city_synonyms = {"prayagraj": "allahabad", "bengaluru": "bangalore", "new delhi": "delhi"}
city_envs = {}

for city in city_list:
    map_path = f"{city}_map.graphml"
    if os.path.exists(map_path):
        try:
            logger.info(f"🦾 TURBO_INIT: {city}...")
            G = ox.load_graphml(map_path)
            scc = max(nx.strongly_connected_components(G), key=len) if G.is_directed() else max(nx.connected_components(G), key=len)
            env = MultiCityTrafficEnv(city, map_path)
            env.G = ox.project_graph(G.subgraph(scc).copy(), to_crs="EPSG:4326")
            city_envs[city] = env
            logger.info(f"✅ {city.upper()} Sector Ready.")
        except Exception as e: logger.error(f"Fail {city}: {e}")

class RouteRequest(BaseModel):
    city_query: str
    start_lat: float; start_lng: float; end_lat: float; end_lng: float
    target_hour: int; target_hospital_wait_time: int = 0
    is_green_corridor: bool = False
    is_police_sync: bool = False
    is_forecast: bool = False

@app.post("/get_route")
async def get_route(req: RouteRequest):
    raw_query = req.city_query.lower()
    target_id = next((cid for cid in city_list if cid in raw_query), None)
    if not target_id: target_id = next((cid for syn, cid in city_synonyms.items() if syn in raw_query), None)
    
    env = city_envs.get(target_id)
    if not env: raise HTTPException(status_code=400, detail="CITY_NOT_LOADED")

    try:
        # 1. TEMPORAL DYNAMICS
        h = req.target_hour + (0.42 if req.is_forecast else 0)
        rush_intensity = math.exp(-(h-9)**2/6) + math.exp(-(h-18)**2/6)
        
        # 2. NEURAL INFERENCE (Vectorized for Speed)
        feat_dict = env.get_feature_matrix(h)
        edge_keys = list(feat_dict.keys())
        feat_array = np.array([feat_dict[k] for k in edge_keys], dtype=np.float32)
        features_tensor = torch.from_numpy(feat_array)
        
        with torch.no_grad():
            q_values = agent.policy_net(features_tensor)
            friction_map = dict(zip(edge_keys, (1.0 / (torch.abs(q_values.mean(dim=1)) + 0.01)).numpy()))

        # 3. AGGRESSIVE LARGE-CITY REROUTING
        priority_roads = ['primary', 'trunk', 'motorway', 'motorway_link', 'trunk_link', 'primary_link']

        for u, v, k, data in env.G.edges(keys=True, data=True):
            road_type = data.get('highway', 'residential')
            if isinstance(road_type, list): road_type = road_type[0]
            
            ai_friction = friction_map.get((u, v, k), 1.0)
            length = data.get('length', 100)
            
            if req.is_green_corridor:
                traffic_mult = 0.2 if road_type in priority_roads else 0.8
            else:
                penalty_weight = 120.0 if target_id in ['delhi', 'bangalore'] else 60.0
                traffic_mult = 1.0 + (rush_intensity * penalty_weight if road_type in priority_roads else rush_intensity * 8.0)
            
            data['ml_cost'] = length * traffic_mult * ai_friction

        # 4. ASTAR PATHFINDING
        orig = ox.distance.nearest_nodes(env.G, req.start_lng, req.start_lat)
        dest = ox.distance.nearest_nodes(env.G, req.end_lng, req.end_lat)
        route_nodes = nx.astar_path(env.G, orig, dest, weight='ml_cost')

        # 5. POLICE INTERCEPTOR SYNC (Restored Fast Version)
        escort_data = None
        if req.is_police_sync:
            mid_node = route_nodes[len(route_nodes)//2]
            random.seed(sum(route_nodes[:3]))
            fleet_nodes = random.sample(list(env.G.nodes()), 10)
            b_lat, b_lng = env.G.nodes[mid_node]['y'], env.G.nodes[mid_node]['x']
            dist_list = [((env.G.nodes[fn]['y']-b_lat)**2 + (env.G.nodes[fn]['x']-b_lng)**2) for fn in fleet_nodes]
            best_unit = fleet_nodes[dist_list.index(min(dist_list))]
            escort_data = {
                "lat": env.G.nodes[best_unit]['y'], "lng": env.G.nodes[best_unit]['x'], 
                "meet_lat": b_lat, "meet_lng": b_lng
            }

        # 6. TELEMETRY
        actual_dist = sum(env.G.get_edge_data(u, v)[0].get('length', 100) for u, v in zip(route_nodes[:-1], route_nodes[1:]))
        avg_speed = 75 if req.is_green_corridor else max(5, 50 - (rush_intensity * 40))
        
        return {
            "status": "success", 
            "route": [{"lat": env.G.nodes[n]['y'], "lng": env.G.nodes[n]['x']} for n in route_nodes],
            "telemetry": {
                "distance_m": round(actual_dist, 2),
                "travel_time_min": round((actual_dist/1000)/avg_speed*60, 1),
                "total_rescue_time_min": round((actual_dist/1000)/avg_speed*60 + req.target_hospital_wait_time, 1),
                "intensity": round(rush_intensity, 3),
                "escort": escort_data
            }
        }
    except Exception as e:
        logger.error(f"FAIL: {e}")
        raise HTTPException(status_code=500, detail="PATHFINDING_ERROR")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)