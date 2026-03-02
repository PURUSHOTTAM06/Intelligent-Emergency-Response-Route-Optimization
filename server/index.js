require('dotenv').config(); // Load secrets from .env
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const mongoose = require('mongoose');
const Dispatch = require('./db'); // Import your schema

const app = express();
app.use(cors());
app.use(express.json());

// 1. Connect to MongoDB Atlas
mongoose.connect(process.env.MONGODB_URI)
    .then(() => console.log("✅ Connected to Atlas: Emergency_System Database Isolated"))
    .catch(err => console.error("❌ MongoDB Connection Error:", err));
app.get('/', (req, res) => {
    res.send('🚀 Emergency System Orchestrator is Online and Connected to MongoDB Atlas!');
});
// 2. Updated Dispatch Route
app.post('/api/dispatch', async (req, res) => {
    const { x, y } = req.body;

    try {
        // A. Call Python AI Engine using URL from .env
        const aiResponse = await axios.get(process.env.PYTHON_AI_URL, {
            params: { start_x: x, start_y: y }
        });

        const optimalPath = aiResponse.data.optimal_path;

        // B. Save to MongoDB Atlas for history & analysis
        const newDispatch = new Dispatch({
            start_node: { x, y },
            hospital_node: { x: 4, y: 4 },
            optimal_path: optimalPath,
            travel_time_penalty: aiResponse.data.total_penalty || 0
        });
        await newDispatch.save();

        // C. Send to React Frontend
        res.json({
            message: "AI Dispatch Successful & Logged",
            path: optimalPath,
            db_id: newDispatch._id
        });

    } catch (error) {
        console.error("System Error:", error.message);
        res.status(500).json({ error: "AI Microservice or Database is offline" });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 Orchestrator running on Port ${PORT}`));