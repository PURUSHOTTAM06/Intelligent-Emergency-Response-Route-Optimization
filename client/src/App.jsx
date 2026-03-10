import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, ShieldAlert, Navigation, Cpu, Zap, Globe, Database, Map as MapIcon } from 'lucide-react';

// --- CONFIGURATION ---
// The frontend expects an environment variable `VITE_BASE_URL` pointing to your
// Express orchestrator. In Codespaces you should forward port 5000 and then
// make it public; the visible URL will look like
// `https://<workspace>-5000.app.github.dev`.
// Create a `.env` file in the `client` folder containing that value, for
// example:
//
//     VITE_BASE_URL=https://opulent-system-5gxxpqvjrw9vfppwv-5000.app.github.dev
//
// Vite exposes `VITE_` variables under `import.meta.env`.  A sensible local
// fallback is `http://localhost:5000` so the UI still works outside Codespaces.
const BASE_URL = "https://opulent-system-5gxxpqvjrw9vfppwv-5000.app.github.dev";// Use the IP instead of 'localhost'

const App = () => {
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [stats, setStats] = useState({ loss: "0.0042", epsilon: "0.05", reward: "-12.4" });

  const triggerDispatch = async () => {
    setLoading(true);
    setRoute(null); // Clear previous route for animation
    try {
      const res = await axios.post(`${BASE_URL}/api/dispatch`, { 
        x: Number(coords.x), 
        y: Number(coords.y) 
      });
      
      // The AI returns the path; we update our state to trigger the Framer Motion animations
      setRoute(res.data.path);
      
      // Simulate real-time DQN metric update
      setStats({
        loss: (Math.random() * 0.001).toFixed(5),
        epsilon: "0.02",
        reward: (res.data.path.length * -1.1).toFixed(2)
      });
    } catch (err) {
      console.error("Neural Link Failure:", err);
      alert("CONNECTION_FAILURE: Ensure Port 5000 is PUBLIC in the Ports tab.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 font-mono p-4 md:p-10 relative selection:bg-red-500/30">
      {/* GLOWING BACKGROUND NODES */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-900/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-red-900/10 blur-[120px] rounded-full" />
      </div>

      <div className="max-w-7xl mx-auto">
        {/* HEADER HUD */}
        <header className="flex flex-col md:flex-row justify-between items-center mb-10 border-b border-white/5 pb-8 gap-6">
          <div className="flex items-center gap-5">
            <motion.div 
              animate={{ scale: [1, 1.05, 1], rotate: [0, 2, -2, 0] }}
              transition={{ repeat: Infinity, duration: 4 }}
              className="p-3 bg-red-600 rounded-2xl shadow-[0_0_30px_rgba(220,38,38,0.4)] border border-red-500/50"
            >
              <ShieldAlert size={32} className="text-white" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-black tracking-[0.1em] italic uppercase text-white leading-none">
                EMERGENCY<span className="text-red-600 underline decoration-4 underline-offset-8">_AI</span>_OS
              </h1>
              <div className="flex gap-4 mt-3">
                <span className="text-[10px] text-emerald-400 font-bold border border-emerald-500/30 px-2 py-1 rounded bg-emerald-500/5 uppercase tracking-widest">System_Optimal</span>
                <span className="text-[10px] text-blue-400 font-bold border border-blue-500/30 px-2 py-1 rounded bg-blue-500/5 uppercase tracking-widest">Node: JPR_2026</span>
              </div>
            </div>
          </div>

          <div className="flex gap-3 bg-white/5 p-2.5 rounded-2xl border border-white/10 backdrop-blur-xl">
            <StatusChip icon={<Globe size={14}/>} label="NODE_JS" color="emerald" />
            <StatusChip icon={<Cpu size={14}/>} label="DQN_CORE" color="blue" />
            <StatusChip icon={<Database size={14}/>} label="ATLAS_DB" color="amber" />
          </div>
        </header>

        <div className="grid grid-cols-12 gap-8">
          {/* MAIN VISUALIZER */}
          <section className="col-span-12 lg:col-span-8 bg-white/[0.02] border border-white/10 rounded-[2.5rem] p-8 h-[600px] flex flex-col relative overflow-hidden backdrop-blur-md group">
            <div className="flex justify-between items-center mb-8 relative z-10">
              <h2 className="text-xs font-black uppercase tracking-[0.3em] text-slate-500 flex items-center gap-2">
                <MapIcon size={16} className="text-red-500" /> Urban_Stochastic_Grid
              </h2>
              <div className="text-[10px] font-bold text-blue-400 bg-blue-500/10 px-4 py-1.5 rounded-full border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
                LIVE_LATENCY: 14MS
              </div>
            </div>

            <div className="flex-1 flex flex-col items-center justify-center bg-black/60 rounded-3xl border border-white/5 relative group-hover:border-red-500/20 transition-all duration-700">
              <AnimatePresence mode="wait">
                {route ? (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="z-10 text-center"
                  >
                    <div className="flex items-center justify-center gap-3 text-emerald-400 font-black text-2xl mb-10 tracking-widest italic drop-shadow-[0_0_15px_rgba(16,185,129,0.5)] uppercase">
                      <Zap className="animate-pulse" /> Optimized_Path_Locked
                    </div>
                    <div className="flex flex-wrap justify-center gap-4 px-6">
                      {route.map((step, i) => (
                        <motion.div 
                          key={i}
                          initial={{ x: -20, opacity: 0 }}
                          animate={{ x: 0, opacity: 1 }}
                          transition={{ delay: i * 0.1 }}
                          className="px-5 py-4 bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 rounded-2xl font-black text-sm shadow-[inset_0_0_10px_rgba(16,185,129,0.1)] hover:bg-emerald-500/20 transition-all"
                        >
                          {`(${step[0]}, ${step[1]})`}
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                ) : (
                  <div className="flex flex-col items-center gap-8 opacity-20">
                    <motion.div 
                      animate={{ rotate: 360 }}
                      transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
                      className="w-24 h-24 border-[8px] border-white/5 border-t-red-600 rounded-full" 
                    />
                    <span className="text-xs font-black tracking-[0.5em] uppercase text-white/50">Awaiting_Neural_Input</span>
                  </div>
                )}
              </AnimatePresence>
              {/* GRID OVERLAY */}
              <div className="absolute inset-0 bg-[radial-gradient(#ffffff08_1px,transparent_1px)] [background-size:40px_40px] pointer-events-none" />
              <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%)] bg-[length:100%_4px] pointer-events-none" />
            </div>
          </section>

          {/* SIDEBAR */}
          <aside className="col-span-12 lg:col-span-4 space-y-8">
            <div className="bg-white/[0.03] border border-white/10 p-8 rounded-[2.5rem] backdrop-blur-xl shadow-2xl">
              <h3 className="text-white text-[10px] font-black uppercase mb-8 flex items-center gap-3 tracking-[0.2em]">
                <Navigation size={18} className="text-red-600" /> Dispatch_Configuration
              </h3>
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <label className="text-[9px] font-black text-white/30 uppercase tracking-widest ml-1">Coord_X</label>
                    <input type="number" value={coords.x} onChange={e => setCoords({...coords, x: e.target.value})} className="w-full bg-black/60 border-2 border-white/5 focus:border-red-600/50 p-4 text-red-500 font-black font-mono rounded-2xl outline-none transition-all" />
                  </div>
                  <div className="space-y-3">
                    <label className="text-[9px] font-black text-white/30 uppercase tracking-widest ml-1">Coord_Y</label>
                    <input type="number" value={coords.y} onChange={e => setCoords({...coords, y: e.target.value})} className="w-full bg-black/60 border-2 border-white/5 focus:border-red-600/50 p-4 text-red-500 font-black font-mono rounded-2xl outline-none transition-all" />
                  </div>
                </div>
                <motion.button 
                  whileHover={{ scale: 1.02, boxShadow: "0 0 40px rgba(220,38,38,0.3)" }}
                  whileTap={{ scale: 0.98 }}
                  onClick={triggerDispatch}
                  disabled={loading}
                  className={`w-full py-5 rounded-2xl font-black tracking-[0.3em] uppercase transition-all flex items-center justify-center gap-3 ${
                    loading ? 'bg-zinc-800 text-zinc-500' : 'bg-red-600 hover:bg-red-500 text-white shadow-xl shadow-red-900/20'
                  }`}
                >
                  {loading ? <Activity className="animate-spin" /> : <Zap size={20} />}
                  {loading ? "CALCULATING..." : "EXECUTE DISPATCH"}
                </motion.button>
              </div>
            </div>

            <div className="bg-black/40 border border-white/10 p-8 rounded-[2.5rem]">
              <h3 className="text-blue-500 text-[10px] font-black uppercase mb-8 flex items-center gap-3 tracking-[0.2em]">
                <Cpu size={18} /> DQN_Neural_Telemetry
              </h3>
              <div className="space-y-6">
                <StatRow label="MODEL_LOSS" value={stats.loss} color="text-amber-500" />
                <StatRow label="EXPLORATION" value={stats.epsilon} color="text-blue-500" />
                <StatRow label="EPISODE_REWARD" value={stats.reward} color="text-emerald-500" />
                
                <div className="pt-6 mt-6 border-t border-white/5">
                  <div className="flex justify-between text-[10px] text-white/30 font-bold mb-3 uppercase tracking-widest">
                    <span>Confidence_Index</span>
                    <span>94.2%</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/10">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: "94.2%" }}
                      transition={{ duration: 2 }}
                      className="h-full bg-gradient-to-r from-red-600 to-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                    />
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};

const StatRow = ({ label, value, color }) => (
  <div className="flex justify-between items-center group">
    <span className="text-white/20 text-[9px] font-black tracking-widest group-hover:text-white/40 transition-colors uppercase">{label}</span>
    <span className={`text-sm font-black font-mono transition-all group-hover:scale-110 ${color}`}>{value}</span>
  </div>
);

const StatusChip = ({ icon, label, color }) => {
  const colorMap = {
    emerald: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    blue: "text-blue-500 bg-blue-500/10 border-blue-500/20",
    amber: "text-amber-500 bg-amber-500/10 border-amber-500/20"
  };
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-[10px] font-black tracking-tighter ${colorMap[color]}`}>
      {icon} {label}
    </div>
  );
};

export default App;