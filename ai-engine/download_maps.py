import osmnx as ox
import os

# --- CONFIGURATION ---
CITIES = {
    "jaipur": "Jaipur, Rajasthan, India",
    "delhi": "New Delhi, Delhi, India",
    "allahabad": "Prayagraj, Uttar Pradesh, India",
    "bangalore": "Bengaluru, Karnataka, India"
}

def download_urban_graphs():
    print("🌍 MAP_SCOUT: Initializing Urban Graph Downloader...")
    
    for city_id, query in CITIES.items():
        filename = f"{city_id}_map.graphml"
        
        if os.path.exists(filename):
            print(f"✅ SKIP: {filename} already exists.")
            continue
            
        try:
            print(f"📡 FETCHING: Downloading street network for {query}...")
            
            # Use the most stable version of the function call
            # We download by place name directly
            G = ox.graph_from_place(query, network_type='drive', retain_all=True)
            
            # Project to UTM for accurate geometry calculations
            G_proj = ox.project_graph(G)
            
            # 2. Clean the graph (Consolidate complex intersections)
            # This makes the A* search much faster
            G_final = ox.consolidate_intersections(G_proj, rebuild_graph=True, tolerance=15)
            
            # 3. Save as GraphML
            ox.save_graphml(G_final, filepath=filename)
            print(f"💾 SAVED: {filename} (Successfully indexed intersections)")
            
        except Exception as e:
            print(f"🚨 FAILED: Could not download {city_id}. Error: {e}")

if __name__ == "__main__":
    ox.settings.use_cache = True
    ox.settings.log_console = False # Set to False to keep terminal clean
    
    download_urban_graphs()
    print("\n🏁 ALL MAPS SYNCED: You can now run main.py or train_main.py")