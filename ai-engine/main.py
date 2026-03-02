from fastapi import FastAPI
import pickle
import networkx as nx

app = FastAPI()

# Load the trained AI Brain
with open("ambulance_brain.pkl", "rb") as f:
    q_table = pickle.load(f)

@app.get("/")
def home():
    return {"message": "Emergency Response Routing API is Online"}

@app.get("/get-best-route")
def get_route(start_x: int, start_y: int):
    # This simulates the AI making decisions for the frontend
    current_state = (start_x, start_y)
    hospital = (4, 4)
    path = [current_state]
    
    # Use the Q-table to find the path
    while current_state != hospital and len(path) < 25:
        # In a real app, we'd look up neighbors. For now, let's find the best move
        possible_actions = [k[1] for k in q_table.keys() if k[0] == current_state]
        if not possible_actions:
            break
            
        best_move = max(possible_actions, key=lambda a: q_table.get((current_state, a), -float('inf')))
        current_state = best_move
        path.append(current_state)
    
    return {"optimal_path": path}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
