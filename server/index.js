require('dotenv').config();
const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();

app.use(cors({ origin: '*', methods: ['GET', 'POST'] }));
app.use(express.json());

const PORT = 5000;
const AI_URL = "http://localhost:8000";

/**
 * CITY REGISTRY 4.0 - PRODUCTION DATASET
 * Includes Jaipur, Delhi, Allahabad, and Bangalore.
 */
const CITY_REGISTRY = {
    "jaipur": {
        id: "jaipur",
        name: "Jaipur",
        center: [26.9124, 75.7873],
        query: "Jaipur, Rajasthan, India",
        targets: {
            hospitals: [
                { name: "SMS Medical Center", lat: 26.8917, lng: 75.8153 },
                { name: "Fortis International", lat: 26.8488, lng: 75.8038 },
                { name: "Santokba Durlabhji", lat: 26.8982, lng: 75.8065 }
            ],
            schools: [
                { name: "MGD Girls School", lat: 26.9105, lng: 75.8122 },
                { name: "St. Xavier's Senior Sec", lat: 26.9168, lng: 75.7981 }
            ],
            offices: [
                { name: "World Trade Park (WTP)", lat: 26.8524, lng: 75.8051 },
                { name: "Genpact IT Park", lat: 26.8242, lng: 75.8135 }
            ]
        }
    },
    "delhi": {
        id: "delhi",
        name: "Delhi",
        center: [28.6139, 77.2090],
        query: "New Delhi, Delhi, India",
        targets: {
            hospitals: [
                { name: "AIIMS Delhi", lat: 28.5672, lng: 77.2100 },
                { name: "Safdarjung Hospital", lat: 28.5665, lng: 77.2075 }
            ],
            schools: [
                { name: "Delhi Public School (RK Puram)", lat: 28.5639, lng: 77.1725 },
                { name: "Modern School Barakhamba", lat: 28.6315, lng: 77.2345 }
            ],
            offices: [
                { name: "Cyber City (Gurugram)", lat: 28.4950, lng: 77.0878 },
                { name: "Connaught Place Hub", lat: 28.6304, lng: 77.2177 }
            ]
        }
    },
    "allahabad": {
        id: "allahabad",
        name: "Allahabad",
        center: [25.4358, 81.8463],
        query: "Prayagraj, Uttar Pradesh, India",
        targets: {
            hospitals: [
                { name: "Nazareth Hospital", lat: 25.4412, lng: 81.8520 },
                { name: "SRN Hospital", lat: 25.4325, lng: 81.8339 }
            ],
            schools: [
                { name: "Boys' High School (BHS)", lat: 25.4542, lng: 81.8335 },
                { name: "St. Joseph's College", lat: 25.4515, lng: 81.8350 }
            ],
            offices: [
                { name: "Civil Lines Business District", lat: 25.4485, lng: 81.8322 },
                { name: "High Court Complex", lat: 25.4580, lng: 81.8250 }
            ]
        }
    },
    "bangalore": {
        id: "bangalore",
        name: "Bangalore",
        center: [12.9716, 77.5946],
        query: "Bengaluru, Karnataka, India",
        targets: {
            hospitals: [
                { name: "Manipal Hospital Old Airport Rd", lat: 12.9593, lng: 77.6444 },
                { name: "St. John's Medical College", lat: 12.9344, lng: 77.6120 }
            ],
            schools: [
                { name: "Bishop Cotton Boys", lat: 12.9678, lng: 77.5985 },
                { name: "The Valley School", lat: 12.8625, lng: 77.5180 }
            ],
            offices: [
                { name: "Manyata Tech Park", lat: 13.0451, lng: 77.6266 },
                { name: "Bagmane World Tech Park", lat: 12.9805, lng: 77.6936 }
            ]
        }
    }
};

app.get('/api/cities', (req, res) => {
    const list = Object.values(CITY_REGISTRY);
    console.log(`📡 HUD_SYNC: Synchronizing ${list.length} sectors.`);
    res.json(list);
});

app.post('/dispatch', async (req, res) => {
    const { cityId, user_lat, user_lng, target_lat, target_lng } = req.body;
    
    const city = CITY_REGISTRY[cityId?.toLowerCase()];
    if (!city) return res.status(400).json({ error: "INVALID_SECTOR" });

    if (!target_lat || !target_lng) {
        return res.status(400).json({ error: "NO_TARGET_COORDINATES" });
    }

    try {
        console.log(`🧠 AI_INVOCATION: Requesting path optimization for ${city.name}...`);
        
        // Added a 15-second timeout to handle large graph calculations in Python
        const aiResponse = await axios.post(`${AI_URL}/get_route`, {
            city_query: city.query,
            start_lat: parseFloat(user_lat),
            start_lng: parseFloat(user_lng),
            end_lat: parseFloat(target_lat),
            end_lng: parseFloat(target_lng)
        }, { timeout: 15000 });

        res.json({
            status: "success",
            city: city.name,
            route: aiResponse.data.route,
            telemetry: aiResponse.data.telemetry
        });

    } catch (err) {
        const errorMsg = err.response?.data || err.message;
        console.error("❌ AI_ENGINE_LINK_FAILURE:", errorMsg);
        res.status(503).json({ 
            status: "error", 
            message: "Neural Engine Timeout. Ensure Python backend is running on port 8000." 
        });
    }
});

app.listen(PORT, () => {
    console.log(`\n-----------------------------------------`);
    console.log(`🚀 ORCHESTRATOR ONLINE | http://localhost:${PORT}`);
    console.log(`🏙️  REGISTRY: ${Object.keys(CITY_REGISTRY).join(', ').toUpperCase()}`);
    console.log(`-----------------------------------------\n`);
});