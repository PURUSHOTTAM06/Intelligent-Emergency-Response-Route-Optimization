require('dotenv').config();
const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors({ origin: '*', methods: ['GET', 'POST'] }));
app.use(express.json());

const PORT = 5000;
const AI_URL = process.env.AI_URL || "http://localhost:8000";

const getClinicalPulse = (hosp, hour) => {
    let arrivalRate = 0.15; 
    if ((hour >= 8 && hour <= 11) || (hour >= 17 && hour <= 21)) arrivalRate = 0.38;
    if (hour >= 23 || hour <= 3) arrivalRate = 0.28;
    const rho = Math.min(0.99, arrivalRate / (hosp.serviceCapacity || 0.45)); 
    const waitMinutes = Math.floor(rho / ((hosp.serviceCapacity || 0.45) - arrivalRate));
    const availableBeds = Math.max(0, Math.floor((hosp.totalBeds || 50) * (1 - rho)));
    return { 
        waitTime: waitMinutes + 5, 
        beds: availableBeds, 
        load: rho > 0.85 ? 'CRITICAL' : (rho > 0.6 ? 'HIGH' : 'OPTIMAL') 
    };
};

const CITY_REGISTRY = {
    "jaipur": {
        id: "jaipur", name: "Jaipur", query: "Jaipur, Rajasthan, India", center: [26.9124, 75.7873],
        targets: {
            hospitals: [
                { name: "SMS Medical Center", lat: 26.8917, lng: 75.8153, totalBeds: 120, serviceCapacity: 0.45 },
                { name: "Fortis International", lat: 26.8488, lng: 75.8038, totalBeds: 60, serviceCapacity: 0.65 },
                { name: "Santokba Durlabhji", lat: 26.8982, lng: 75.8065, totalBeds: 45, serviceCapacity: 0.40 },
                { name: "Apex Hospital", lat: 26.8439, lng: 75.8236, totalBeds: 40, serviceCapacity: 0.50 },
                { name: "Eternal Multispecialty", lat: 26.8245, lng: 75.8122, totalBeds: 55, serviceCapacity: 0.55 }
            ],
            schools: [
                { name: "MGD Girls School", lat: 26.9105, lng: 75.8122 },
                { name: "St. Xavier's", lat: 26.9168, lng: 75.7981 },
                { name: "Maharaja Sawai Man Singh", lat: 26.8975, lng: 75.8090 }
            ],
            offices: [
                { name: "World Trade Park", lat: 26.8524, lng: 75.8051 },
                { name: "Genpact Park", lat: 26.8242, lng: 75.8135 },
                { name: "Infosys Campus", lat: 26.8280, lng: 75.8010 }
            ]
        }
    },
    "delhi": {
        id: "delhi", name: "Delhi", query: "New Delhi, Delhi, India", center: [28.6139, 77.2090],
        targets: {
            hospitals: [
                { name: "AIIMS Delhi", lat: 28.5672, lng: 77.2100, totalBeds: 300, serviceCapacity: 0.50 },
                { name: "Safdarjung Hospital", lat: 28.5665, lng: 77.2075, totalBeds: 250, serviceCapacity: 0.42 },
                { name: "Max Super Specialty", lat: 28.5283, lng: 77.2115, totalBeds: 100, serviceCapacity: 0.70 }
            ],
            schools: [{ name: "DPS RK Puram", lat: 28.5639, lng: 77.1725 }],
            offices: [{ name: "Cyber City", lat: 28.4950, lng: 77.0878 }]
        }
    },
    "allahabad": {
        id: "allahabad", name: "Allahabad", query: "Prayagraj, Uttar Pradesh, India", center: [25.4358, 81.8463],
        targets: {
            hospitals: [
                { name: "Nazareth Hospital", lat: 25.4412, lng: 81.8520, totalBeds: 60, serviceCapacity: 0.40 },
                { name: "SRN Hospital", lat: 25.4325, lng: 81.8339, totalBeds: 100, serviceCapacity: 0.35 }
            ],
            schools: [{ name: "Boys High School", lat: 25.4542, lng: 81.8335 }],
            offices: [{ name: "Prayagraj High Court", lat: 25.4580, lng: 81.8250 }]
        }
    },
    "bangalore": {
        id: "bangalore", name: "Bangalore", query: "Bengaluru, Karnataka, India", center: [12.9716, 77.5946],
        targets: {
            hospitals: [
                { name: "Manipal Hospital", lat: 12.9593, lng: 77.6444, totalBeds: 200, serviceCapacity: 0.60 },
                { name: "St. John's Medical", lat: 12.9344, lng: 77.6120, totalBeds: 180, serviceCapacity: 0.45 }
            ],
            schools: [{ name: "Bishop Cotton", lat: 12.9678, lng: 77.5985 }],
            offices: [{ name: "Manyata Tech Park", lat: 13.0451, lng: 77.6266 }]
        }
    }
};

app.get('/api/cities', (req, res) => {
    const hour = parseInt(req.query.hour) || new Date().getHours();
    const snapshot = Object.values(CITY_REGISTRY).map(city => {
        const dynamicCity = JSON.parse(JSON.stringify(city));
        dynamicCity.targets.hospitals = city.targets.hospitals.map(h => ({ ...h, ...getClinicalPulse(h, hour) }));
        return dynamicCity;
    });
    res.json(snapshot);
});
// ... existing clinical pulse and registry same ...

app.post('/dispatch', async (req, res) => {
    const { cityId, user_lat, user_lng, target_lat, target_lng, target_hour, isGreenCorridor, isPoliceSync, isForecast } = req.body;
    const city = CITY_REGISTRY[cityId?.toLowerCase()];
    if (!city) return res.status(400).json({ error: "SECTOR_NOT_FOUND" });

    const allNodes = Object.values(city.targets).flat();
    const targetNode = allNodes.find(t => Math.abs(t.lat - parseFloat(target_lat)) < 0.005);
    const triage = targetNode ? getClinicalPulse(targetNode, target_hour) : { waitTime: 0 };

    try {
        const aiResponse = await axios.post(`${AI_URL}/get_route`, {
            city_query: city.id,
            start_lat: parseFloat(user_lat), start_lng: parseFloat(user_lng),
            end_lat: parseFloat(target_lat), end_lng: parseFloat(target_lng),
            target_hour: parseInt(target_hour),
            target_hospital_wait_time: triage.waitTime,
            is_green_corridor: isGreenCorridor,
            is_police_sync: isPoliceSync,
            is_forecast: isForecast // PHASE 4 RELAY
        });

        res.json({
            status: "success",
            route: aiResponse.data.route,
            telemetry: aiResponse.data.telemetry
        });
    } catch (err) {
        console.error("AI engine request failed", err?.response?.data || err.message || err);
        res.status(503).json({ error: "AI Engine Offline", details: err?.response?.data || err?.message || "unknown" });
    }
});

app.listen(PORT, () => console.log(`🚀 ORCHESTRATOR ONLINE | PORT ${PORT}`));