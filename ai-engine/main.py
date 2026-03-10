import torch
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from model import DQNBrain
from environment import UrbanGraphEnv

app = FastAPI(title="Emergency_AI_DQN_Inference_Engine")

# --- HYPERPARAMETERS & CONFIG ---
STATE_DIM = 21  # [Current_Pos(1) + Traffic(10) + Incidents(10)]
ACTION_DIM = 10 
MODEL_PATH = "ambulance_dqn_v1.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- LOAD NEURAL BRAIN ---
# We initialize the architecture and load the trained weights
brain = DQNBrain(STATE_DIM, ACTION_DIM).to(DEVICE)
try:
    brain.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    brain.eval() # Set to evaluation mode (disables dropout/batchnorm)
    print(f"✅ AI Brain Loaded Successfully from {MODEL_PATH}")
except FileNotFoundError:
    print(f"❌ ERROR: {MODEL_PATH} not found. Run train_main.py first!")

class DispatchRequest(BaseModel):
    x: int
    y: int

@app.get("/")
def health_check():
    return {
        "status": "ONLINE",
        "engine": "DEEP_Q_NETWORK_V1",
        "device": str(DEVICE)
    }

@app.post("/get-optimal-route")
async def get_route(request: DispatchRequest):
    env = UrbanGraphEnv(num_nodes=10)
    state = env.reset() # In production, this state would pull from real-time traffic data
    
    path = []
    current_node = 0  # Assuming dispatch starts at node 0
    hospital_node = 9 # Destination node
    max_steps = 15    # Safety cutoff
    
    # Inference Loop: Neural Network predicts each step
    with torch.no_grad():
        for _ in range(max_steps):
            # Convert state to tensor for the Brain
            state_t = torch.FloatTensor(state).unsqueeze(0).to(DEVICE)
            
            # Brain predicts Q-values; we take the argmax (best action)
            action = brain(state_t).argmax().item()
            
            # Map action back to grid coordinates for your React UI
            # (Example mapping: Node ID converted to X,Y)
            path.append([action // 2, action % 2])
            
            if action == hospital_node:
                break
            
            # Move environment forward to the next state
            state, _, done = env.step(action)
            if done: break

    return {
        "status": "SUCCESS",
        "optimal_path": path,
        "telemetry": {
            "model_version": "1.0.0-DQN",
            "compute_device": str(DEVICE)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)