import React, { useState } from 'react';
import axios from 'axios';
import { Activity, Map as MapIcon, ShieldAlert, Navigation, History } from 'lucide-react';

function App() {
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startY, setStartY] = useState(0);

  const triggerDispatch = async () => {
    setLoading(true);
    try {
      // Connects to the Node.js Backend Bridge (Port 5000)
      const res = await axios.post('/api/dispatch', {
        x: Number(startX),
        y: Number(startY)
      });
      
      // 'path' is retrieved by Node from the Python AI Engine and saved to Atlas
      setRoute(res.data.path); 
      console.log("Logged in MongoDB with ID:", res.data.db_id);
    } catch (err) {
      console.error("Connection Error:", err);
      const msg = err?.response?.data?.error || err.message || 'Unknown error';
      alert(`System Offline: ${msg}`);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-black text-white p-6 font-sans">
      {/* Header Section */}
      <div className="flex justify-between items-center border-b border-red-900 pb-4 mb-8">
        <div className="flex items-center gap-3">
          <ShieldAlert className="text-red-600 animate-pulse" size={32} />
          <h1 className="text-2xl font-bold tracking-tighter uppercase">Emergency_AI_Dispatch_v1.0</h1>
        </div>
        <div className="text-right text-xs text-gray-500 font-mono">
          NODE_SERVER: <span className="text-green-500">CONNECTED</span> <br/>
          AI_ENGINE: <span className="text-green-500">ACTIVE</span>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Column: Grid Visualization */}
        <div className="col-span-8 bg-zinc-900 rounded-lg border border-zinc-800 p-4 h-[550px] flex flex-col relative">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-zinc-400 uppercase text-xs">
              <MapIcon size={14} /> City_Grid_Matrix (5x5)
            </div>
            <div className="text-[10px] text-zinc-600 font-mono">MAP_ID: RJ-JPR-2026</div>
          </div>
          
          <div className="flex-1 flex flex-col items-center justify-center border border-zinc-800 bg-zinc-950 rounded relative overflow-hidden">
             {route ? (
               <div className="animate-in fade-in zoom-in duration-500 text-center">
                 <div className="text-blue-400 font-mono text-lg mb-4 tracking-widest">
                   OPTIMIZED_PATH_LOCKED
                 </div>
                 <div className="flex flex-wrap justify-center gap-2 max-w-md">
                   {route.map((step, i) => (
                     <span key={i} className="px-2 py-1 bg-blue-900/30 border border-blue-500/50 text-blue-300 rounded text-xs">
                       {`(${step[0]}, ${step[1]})`}
                     </span>
                   ))}
                 </div>
               </div>
             ) : (
               <div className="text-zinc-700 font-mono animate-pulse">AWAITING_COORDINATES...</div>
             )}
             
             {/* Background Grid Pattern for Aesthetic */}
             <div className="absolute inset-0 opacity-5 pointer-events-none" 
                  style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
             </div>
          </div>
        </div>

        {/* Right Column: Controls & Telemetry */}
        <div className="col-span-4 space-y-6">
          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-lg">
            <h3 className="text-zinc-500 text-xs font-bold uppercase mb-4 flex items-center gap-2">
              <Navigation size={14} /> Dispatch Configuration
            </h3>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-[10px] text-zinc-500 mb-1">START_X</label>
                <input type="number" min="0" max="4" value={startX} onChange={(e) => setStartX(e.target.value)}
                       className="w-full bg-black border border-zinc-700 p-2 text-blue-400 font-mono rounded"/>
              </div>
              <div>
                <label className="block text-[10px] text-zinc-500 mb-1">START_Y</label>
                <input type="number" min="0" max="4" value={startY} onChange={(e) => setStartY(e.target.value)}
                       className="w-full bg-black border border-zinc-700 p-2 text-blue-400 font-mono rounded"/>
              </div>
            </div>
            
            <button 
              onClick={triggerDispatch}
              disabled={loading}
              className="w-full bg-red-600 hover:bg-red-700 py-4 rounded font-bold flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50"
            >
              <Activity size={20} /> {loading ? "COMPUTING_RL_ROUTE..." : "INITIATE EMERGENCY DISPATCH"}
            </button>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-lg">
            <h3 className="text-zinc-500 text-xs font-bold uppercase mb-4 flex items-center gap-2">
              <History size={14} /> Telemetry_Data
            </h3>
            <div className="space-y-4 font-mono">
              <div className="flex justify-between border-b border-zinc-800 pb-2">
                <span className="text-zinc-400 text-xs">ALGORITHM</span>
                <span className="text-yellow-500 text-xs">Q-LEARNING_RL</span>
              </div>
              <div className="flex justify-between border-b border-zinc-800 pb-2">
                <span className="text-zinc-400 text-xs">DESTINATION</span>
                <span className="text-green-500 text-xs">(4,4) [HOSPITAL]</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400 text-xs">DB_STORAGE</span>
                <span className="text-blue-500 text-xs">MONGO_ATLAS_CLOUD</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;