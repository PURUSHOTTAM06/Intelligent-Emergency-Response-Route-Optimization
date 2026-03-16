const mongoose = require('mongoose');

const DispatchSchema = new mongoose.Schema({
    start_node: { lat: Number, lng: Number },
    hospital_node: { lat: Number, lng: Number },
    optimal_path: Array,
    travel_time_penalty: Number,
    timestamp: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Dispatch', DispatchSchema);