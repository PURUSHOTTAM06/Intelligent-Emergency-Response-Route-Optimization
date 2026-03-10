import torch
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from model import DQNBrain
from environment import UrbanGraphEnv

app = FastAPI()

STATE_DIM, ACTION_DIM = 21, 25
MODEL_PATH = "ambulance_dqn_v1.pth"
DEVICE = torch.device("cpu")

brain = DQNBrain(STATE_DIM, ACTION_DIM).to(DEVICE)
try:
    brain.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    brain.eval()
    print("✅ [NEURAL_LINK_ESTABLISHED]")
except:
    print("❌ Model Not Found - Please Retrain")

class DispatchRequest(BaseModel):
    x: int
    y: int

@app.post("/get-optimal-route")
async def get_route(request: DispatchRequest):
    env = UrbanGraphEnv(size=5)
    env.current_pos = (max(0, min(request.x, 4)), max(0, min(request.y, 4)))
    state = env.get_state()
    
    path = [[env.current_pos[0], env.current_pos[1]]]
    visited = {env.node_to_id[env.current_pos]} # Loop prevention

    with torch.no_grad():
        for _ in range(15): # Max steps for a 5x5 grid
            state_t = torch.FloatTensor(state).unsqueeze(0).to(DEVICE)
            q_values = brain(state_t)
            
            # --- MASKING & LOOP PREVENTION ---
            mask = torch.full((1, 25), -1e9).to(DEVICE)
            neighbors = list(env.G.neighbors(env.current_pos))
            for n in neighbors:
                n_id = env.node_to_id[n]
                # Apply penalty to nodes already in the current path
                penalty = -200.0 if n_id in visited else 0.0
                mask[0, n_id] = penalty
            
            action = (q_values + mask).argmax().item()
            state, _, done = env.step(action)
            
            visited.add(action)
            path.append([action // 5, action % 5])
            if done: break

    return {"status": "SUCCESS", "optimal_path": path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)