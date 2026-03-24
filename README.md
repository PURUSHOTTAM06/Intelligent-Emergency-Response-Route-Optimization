# 🚑 RouteFlow AI: Intelligent Emergency Response Engine

**RouteFlow AI** is a specialized geospatial navigation engine designed to solve the "Golden Hour" problem in emergency medical services. By bridging **Civil Infrastructure** with **Deep Reinforcement Learning**, the system optimizes ambulance routing in real-time, accounting for urban bottlenecks, temporal traffic curves, and hospital clinical loads.

![RouteFlow Demo](https://your-image-link-here.com/demo.gif)

## 🧠 Core Engineering Features

### 1. Neural Routing Engine (Dueling DQN)
Unlike standard GPS (A* or Dijkstra) which only calculates the shortest distance, RouteFlow uses a **Dueling Deep Q-Network (DQN)** to evaluate the "Value" of every road in a city.
* **Architecture:** Separates the estimation of **State Value** (how congested a city sector is) from **Action Advantage** (the benefit of taking a specific road segment).
* **State Vector:** A 6-feature input including Road Centrality, Lane Count, Highway Type, and trigonometric Temporal Encoding (Sin/Cos of time).
* **Double DQN:** Implemented to prevent Q-value overestimation, ensuring the AI doesn't "hallucinate" a fast route during peak traffic.



### 2. Geospatial Graph Environment
The "World" is built using **OSMnx** and **NetworkX**, transforming raw OpenStreetMap data into a mathematical topology.
* **Friction Mapping:** Every road segment (edge) is assigned a dynamic "Neural Friction" score.
* **Multi-Sector Support:** Trained and tested across diverse city layouts, including **Jaipur, Delhi, and Prayagraj**.
* **Binary Fast-Boot:** Utilizes `.pkl` snapshots for high-speed graph loading, bypassing slow XML parsing.

### 3. Tactical Dispatch Modules
* **Green Corridor Sync:** Simulates traffic clearance on primary arteries, adjusting the AI's weight parameters to prioritize high-velocity flow.
* **Police Escort Coordination:** A specialized module that identifies the nearest interceptor unit and calculates a tactical **Intercept Point** for high-speed coordination.
* **Clinical Pulse Integration:** The orchestrator runs a queuing theory model to predict hospital ER wait times, ensuring the patient is sent to the *fastest* available bed, not just the *closest* building.

---

## 🏗️ 3-Tier System Architecture

The project is built as a distributed microservices relay:
1.  **AI Engine (FastAPI/PyTorch):** Performs real-time neural inference and graph pathfinding.
2.  **Orchestrator (Node.js/Express):** Handles the "handshake" between geospatial data and clinical hospital metrics.
3.  **Command Dashboard (React/Leaflet):** A high-performance UI for dispatchers featuring real-time telemetry and spatiotemporal sliders.



---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **AI & Math** | Python, PyTorch, NumPy, Scipy |
| **Geospatial** | OSMnx, NetworkX, GeoPandas |
| **Backend** | Node.js, Express, FastAPI, Uvicorn |
| **Frontend** | React.js, Leaflet.js, Framer Motion |

---

## 🛰️ Neural Value Visualization

The project includes a specialized `dashboard.py` to visualize what the AI "sees." In this visualization:
* **Green Edges:** High-value, optimal paths identified by the Neural Engine.
* **Red Edges:** High-friction bottlenecks to be avoided during the current temporal state.

---

## 🚀 Getting Started (Local Run)

### Prerequisites
* Python 3.10+
* Node.js 18+

### 1. Setup AI Engine
```bash
cd ai-engine
pip install -r requirements.txt
python main.py
