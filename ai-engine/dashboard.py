import streamlit as st
import requests
import networkx as nx
import matplotlib.pyplot as plt

# Page Config
st.set_page_config(page_title="Emergency AI Router", layout="wide")

st.title("🚑 Intelligent Emergency Response System")
st.markdown("""
    This system uses a **Reinforcement Learning (Q-Learning)** agent to find the fastest route for an ambulance 
    by predicting traffic delays using the **BPR (Bureau of Public Roads)** function.
""")

st.sidebar.header("Simulation Settings")

# 1. Setup Input Sliders
start_x = st.sidebar.slider("Ambulance Start X", 0, 4, 0)
start_y = st.sidebar.slider("Ambulance Start Y", 0, 4, 0)

# Dashboard Layout
if st.button("🚀 Find Optimal Emergency Route"):
    # 2. Call your FastAPI Backend
    # Ensure uvicorn is running on port 8000
    try:
        response = requests.get(f"http://127.0.0.1:8000/get-best-route?start_x={start_x}&start_y={start_y}")
        
        if response.status_code == 200:
            raw_path = response.json()["optimal_path"]
            
            # --- FIX: Convert list of lists to list of tuples ---
            path = [tuple(node) for node in raw_path]
            
            st.success(f"Optimal Path Calculated: {' ➔ '.join(map(str, path))}")
            
            # 3. Visualization
            fig, ax = plt.subplots(figsize=(10, 10))
            
            # Create the grid graph
            G = nx.grid_2d_graph(5, 5)
            pos = {(x, y): (x, y) for x, y in G.nodes()}
            
            # Draw base city grid
            nx.draw(G, pos, ax=ax, node_color="#f0f0f0", node_size=400, 
                    with_labels=True, font_size=8, edge_color="#cccccc")
            
            # Highlight Start and Hospital
            nx.draw_networkx_nodes(G, pos, nodelist=[path[0]], node_color="#3498db", node_size=700, label="Ambulance")
            nx.draw_networkx_nodes(G, pos, nodelist=[(4,4)], node_color="#2ecc71", node_size=700, label="Hospital")
            
            # Highlight the AI's Calculated Path
            path_edges = list(zip(path, path[1:]))
            nx.draw_networkx_nodes(G, pos, nodelist=path, node_color="#ff4b4b", node_size=500)
            nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color="#ff4b4b", width=6)
            
            plt.legend(scatterpoints=1)
            st.pyplot(fig)
            
        else:
            st.error("API returned an error. Check backend logs.")
            
    except Exception as e:
        st.error(f"Backend unreachable! Run 'uvicorn main:app --reload' in the terminal. Error: {e}")

# Footer info for Interview
st.sidebar.markdown("---")
st.sidebar.info("""
**Core Knowledge Applied:**
- Graph Theory (NetworkX)
- Traffic Engineering (BPR Function)
- Reinforcement Learning (Bellman Equation)
- Backend API (FastAPI)
""")