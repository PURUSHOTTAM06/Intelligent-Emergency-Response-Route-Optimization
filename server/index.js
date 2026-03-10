require('dotenv').config();
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const mongoose = require('mongoose');
const Dispatch = require('./db');

const app = express();

// --- CRITICAL FIX 1: LOOSEN CORS FOR CODESPACES ---
// This allows your browser (port 5173) to talk to this server (port 5000)
app.use(cors({
    origin: '*', 
    methods: ['GET', 'POST'],
    allowedHeaders: ['Content-Type']
}));

app.use(express.json());

// --- DATABASE CONNECTION ---
mongoose.connect(process.env.MONGODB_URI)
    .then(() => console.log("✅ Database Link Established: Atlas_Cloud_Sync_Active"))
    .catch(err => console.error("❌ DB Connection Error:", err));

// --- DIAGNOSTICS ENDPOINT ---
app.get('/', (req, res) => {
    res.json({ 
        status: "ONLINE", 
        service: "Emergency_Orchestrator_v1",
        database: mongoose.connection.readyState === 1 ? "CONNECTED" : "DISCONNECTED"
    });
});

// --- MAIN NEURAL DISPATCH ROUTE ---
app.post('/api/dispatch', async (req, res) => {
    const { x, y } = req.body;
    console.log(`📡 Dispatch Request Received: Initializing AI Route from (${x}, ${y})`);

    try {
        // --- CRITICAL FIX 2: ALIGN WITH DQN FASTAPI ---
        // Your Python engine now uses POST /get-optimal-route
        // Use the Public Port 8000 URL from your .env
        const aiResponse = await axios.post(`${process.env.PYTHON_AI_URL}/get-optimal-route`, {
            x: Number(x),
            y: Number(y)
        });

        const optimalPath = aiResponse.data.optimal_path;

        // --- DATABASE PERSISTENCE ---
        const newDispatch = new Dispatch({
            start_node: { x: Number(x), y: Number(y) },
            hospital_node: { x: 4, y: 4 }, // Fixed destination for our JPR grid
            optimal_path: optimalPath,
            status: "OPTIMIZED_BY_DQN"
        });
        
        await newDispatch.save();
        console.log(`💾 Telemetry Logged to Atlas: ID ${newDispatch._id}`);

        // Send results back to React HUD
        res.json({
            status: "SUCCESS",
            path: optimalPath,
            db_id: newDispatch._id,
            meta: aiResponse.data.telemetry
        });

    } catch (error) {
        console.error("🚨 Neural Link Error:", error.response?.data || error.message);
        res.status(500).json({ 
            error: "NEURAL_LINK_FAILURE",
            details: "Ensure Python engine is running on Port 8000 and set to PUBLIC."
        });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`🚀 Orchestrator active on Port ${PORT}`);
    console.log(`🔗 Target AI Engine: ${process.env.PYTHON_AI_URL}`);
});