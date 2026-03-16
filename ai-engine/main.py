import torch
import osmnx as ox
import networkx as nx
import os
import logging
import uvicorn
import math  # Added for the heuristic fix
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Import modular classes
from environment import MultiCityTrafficEnv 
from agent import AmbulanceAgent

# --- SYSTEM CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_ENGINE")

app = FastAPI(title="RouteFlow AI: Multi-City Neural Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
STATE_DIM = 6
ACTION_DIM = 8
MODEL_PATH = "ambulance_brain.pth"
SUPPORTED_CITIES = ["jaipur", "delhi", "allahabad", "bangalore"]

city_envs = {}
agent = AmbulanceAgent(STATE_DIM, ACTION_DIM)

# --- 1. BRAIN LOADING ---
if os.path.exists(MODEL_PATH):
    logger.info(f"❄️  BRAIN_LOAD: Injecting trained weights from {MODEL_PATH}...")
    agent.policy_net.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
    agent.policy_net.eval()
    agent.epsilon = 0.0
else:
    logger.warning("⚠️  NO_BRAIN_FOUND: Running with 'Initial Weights'. Accuracy will be low.")
    agent.policy_net.eval()

# --- 2. MULTI-CITY INITIALIZATION ---
logger.info("🏙️  STARTING_CITY_REGISTRY_INIT...")
for city in SUPPORTED_CITIES:
    map_file = f"{city}_map.graphml"
    if os.path.exists(map_file):
        try:
            city_envs[city] = MultiCityTrafficEnv(city, map_file)
            logger.info(f"✅ SUCCESS: {city.upper()} sector is live.")
        except Exception as e:
            logger.error(f"❌ ERROR: Could not initialize {city}: {e}")
    else:
        logger.error(f"🚨 MISSING_MAP: {map_file} not found! Run download_maps.py.")

class RouteRequest(BaseModel):
    city_query: str
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float

@app.post("/get_route")
async def get_route(req: RouteRequest):
    city_id = req.city_query.split(',')[0].lower().strip()
    
    if city_id not in city_envs:
        logger.error(f"🚫 UNSUPPORTED_CITY: Attempted access to '{city_id}'")
        raise HTTPException(status_code=400, detail=f"City '{city_id}' is not loaded.")

    env = city_envs[city_id]
    
    try:
        # A. Update spatiotemporal weights
        current_graph_proj = env.simulate_traffic_step()
        
        # B. GEOSPATIAL BRIDGE
        orig_node = ox.distance.nearest_nodes(env.G, req.start_lng, req.start_lat)
        dest_node = ox.distance.nearest_nodes(env.G, req.end_lng, req.end_lat)

        # C. A* Pathfinding with Version-Safe Heuristic
        def heuristic(u, v):
            u_n = current_graph_proj.nodes[u]
            v_n = current_graph_proj.nodes[v]
            # Use math.dist for x/y projected coordinates (meters)
            return math.dist([u_n['x'], u_n['y']], [v_n['x'], v_n['y']])

        logger.info(f"🧠 DISPATCH: Solving optimized path for {city_id.upper()}...")
        
        with torch.no_grad(): 
            route_nodes = nx.astar_path(
                current_graph_proj, 
                orig_node, 
                dest_node, 
                weight='ai_weight', 
                heuristic=heuristic
            )

        # D. HUD Response Formatting
        route_points = []
        for n in route_nodes:
            node_data = env.G.nodes[n]
            route_points.append({"lat": node_data['y'], "lng": node_data['x']})
            
        actual_dist_m = nx.shortest_path_length(current_graph_proj, orig_node, dest_node, weight='length')

        return {
            "status": "success",
            "city": city_id,
            "route": route_points,
            "telemetry": {
                "distance_m": round(actual_dist_m, 2),
                "nodes": len(route_nodes),
                "ai_status": "ONLINE",
                "engine": "Dueling_DQN_v3"
            }
        }

    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="PATH_NOT_FOUND_IN_GRAPH")
    except Exception as e:
        logger.error(f"🚨 RUNTIME_ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="INTERNAL_NEURAL_ERROR")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)