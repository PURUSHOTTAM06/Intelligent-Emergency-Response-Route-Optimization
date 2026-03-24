import torch
import osmnx as ox
import networkx as nx
import os
import logging
import uvicorn
import numpy as np
import random
import math
import asyncio
import pickle
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from environment import MultiCityTrafficEnv 
from agent import AmbulanceAgent

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_ENGINE")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- GLOBAL PATHS & MODELS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIM, ACTION_DIM = 6, 8
agent = AmbulanceAgent(STATE_DIM, ACTION_DIM)

if os.environ.get("RENDER"):
    city_list = ["jaipur"] 
else:
    city_list = ["jaipur", "allahabad"]

city_envs = {}
app_ready = False 

# --- ASYNC BACKGROUND BOOTSTRAP ---
async def load_sectors():
    global app_ready
    brain_path = os.path.join(BASE_DIR, "ambulance_brain.pth")
    if os.path.exists(brain_path):
        try:
            agent.policy_net.load_state_dict(torch.load(brain_path, map_location=torch.device('cpu')))
            agent.policy_net.eval()
            logger.info("🧠 Neural Brain Synced.")
        except Exception as e:
            logger.error(f"❌ Brain Load Failed: {e}")

    logger.info("🦾 BOOTING SECTORS (Fast Boot Active)...")
    for cid in city_list:
        path_pkl = os.path.join(BASE_DIR, f"{cid}_map.pkl")
        path_graphml = os.path.join(BASE_DIR, f"{cid}_map.graphml")
        target_path = path_pkl if os.path.exists(path_pkl) else path_graphml
        
        if os.path.exists(target_path):
            try:
                # The Env class now handles .pkl correctly
                env = MultiCityTrafficEnv(cid, target_path)
                city_envs[cid] = env
                logger.info(f"✅ {cid.upper()} Sector Ready.")
            except Exception as e:
                logger.error(f"❌ Failed to boot {cid}: {e}")
        else:
            logger.warning(f"⚠️ No map file found for {cid}")
    
    app_ready = True
    logger.info("🚀 SYSTEM FULLY INITIALIZED.")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(load_sectors())

@app.api_route("/", methods=["GET", "HEAD"])
async def health_check():
    return {
        "status": "online" if app_ready else "loading", 
        "loaded_sectors": list(city_envs.keys()),
        "engine": "Async_EagerLoad_V2_Fast"
    }

class RouteRequest(BaseModel):
    city_query: str
    start_lat: float; start_lng: float; end_lat: float; end_lng: float
    target_hour: int; target_hospital_wait_time: int = 0
    is_green_corridor: bool = False
    is_police_sync: bool = False
    is_forecast: bool = False

@app.post("/get_route")
async def get_route(req: RouteRequest):
    if not app_ready:
        raise HTTPException(status_code=503, detail="SYSTEM_BOOTING_PLEASE_WAIT")

    raw_query = req.city_query.lower()
    target_id = next((cid for cid in city_list if cid in raw_query), None)
    
    if not target_id or target_id not in city_envs:
        raise HTTPException(status_code=400, detail="CITY_NOT_LOADED")

    env = city_envs[target_id]

    try:
        h = req.target_hour + (0.42 if req.is_forecast else 0)
        rush_intensity = math.exp(-(h-9)**2/6) + math.exp(-(h-18)**2/6)
        
        feat_dict = env.get_feature_matrix(h)
        edge_keys = list(feat_dict.keys())
        feat_array = np.array([feat_dict[k] for k in edge_keys], dtype=np.float32)
        features_tensor = torch.from_numpy(feat_array)
        
        with torch.no_grad():
            q_values = agent.policy_net(features_tensor)
            friction_map = dict(zip(edge_keys, (1.0 / (torch.abs(q_values.mean(dim=1)) + 0.01)).numpy()))

        priority_roads = ['primary', 'trunk', 'motorway', 'motorway_link', 'trunk_link', 'primary_link']
        for u, v, k, data in env.G.edges(keys=True, data=True):
            road_type = data.get('highway', 'residential')
            if isinstance(road_type, list): road_type = road_type[0]
            ai_friction = friction_map.get((u, v, k), 1.0)
            length = data.get('length', 100)
            
            if req.is_green_corridor:
                traffic_mult = 0.2 if road_type in priority_roads else 0.8
            else:
                penalty_weight = 60.0 
                traffic_mult = 1.0 + (rush_intensity * penalty_weight if road_type in priority_roads else rush_intensity * 8.0)
            
            data['ml_cost'] = length * traffic_mult * ai_friction

        orig = ox.distance.nearest_nodes(env.G, req.start_lng, req.start_lat)
        dest = ox.distance.nearest_nodes(env.G, req.end_lng, req.end_lat)
        route_nodes = nx.astar_path(env.G, orig, dest, weight='ml_cost')

        escort_data = None
        if req.is_police_sync:
            mid_node = route_nodes[len(route_nodes)//2]
            random.seed(sum(route_nodes[:3]))
            fleet_nodes = random.sample(list(env.G.nodes()), 10)
            b_lat, b_lng = env.G.nodes[mid_node]['y'], env.G.nodes[mid_node]['x']
            dist_list = [((env.G.nodes[fn]['y']-b_lat)**2 + (env.G.nodes[fn]['x']-b_lng)**2) for fn in fleet_nodes]
            best_unit = fleet_nodes[dist_list.index(min(dist_list))]
            escort_data = {"lat": env.G.nodes[best_unit]['y'], "lng": env.G.nodes[best_unit]['x'], "meet_lat": b_lat, "meet_lng": b_lng}

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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)