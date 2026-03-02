const mongoose = require('mongoose');

// This schema tracks every emergency dispatch for history and analysis
const DispatchSchema = new mongoose.Schema({
    start_node: { x: Number, y: Number },
    hospital_node: { x: Number, y: Number },
    optimal_path: Array,
    travel_time_penalty: Number,
    timestamp: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Dispatch', DispatchSchema);