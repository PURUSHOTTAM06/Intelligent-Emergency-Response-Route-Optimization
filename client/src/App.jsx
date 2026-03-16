import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap, useMapEvents, Popup } from 'react-leaflet';
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// --- PROFESSIONAL ASSETS ---
const getIcon = (color) => new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});

const icons = {
    user: getIcon('blue'),
    hospitals: getIcon('red'),
    schools: getIcon('gold'),
    offices: getIcon('violet')
};

// --- EMERGENCY VEHICLE SPEEDS (km/h) ---
const VEHICLE_PROFILES = {
    ambulance: { name: 'Ambulance', speed: 50, icon: '🚑' },
    police: { name: 'Police', speed: 65, icon: '🚓' },
    fire: { name: 'Fire Engine', speed: 35, icon: '🚒' }
};

// --- CINEMATIC MAP ANIMATOR ---
function MapAnimate({ center, cityId }) {
    const map = useMap();
    const prevCityId = useRef();

    useEffect(() => {
        if (center && cityId !== prevCityId.current) {
            map.flyTo(center, 13, {
                animate: true,
                duration: 2.5,
                easeLinearity: 0.25
            });
            prevCityId.current = cityId;
        }
    }, [center, cityId, map]);
    return null;
}

function App() {
    const [cities, setCities] = useState([]);
    const [activeCity, setActiveCity] = useState(null);
    const [category, setCategory] = useState('hospitals');
    const [vehicle, setVehicle] = useState('ambulance'); // New Vehicle State
    const [userLocation, setUserLocation] = useState(null);
    const [route, setRoute] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [telemetry, setTelemetry] = useState(null);

    useEffect(() => {
        const fetchCities = async () => {
            try {
                const res = await axios.get('http://localhost:5000/api/cities');
                setCities(res.data);
                if (res.data.length > 0) setActiveCity(res.data[0]);
            } catch (err) { console.error("ORCHESTRATOR_OFFLINE"); }
        };
        fetchCities();
    }, []);

    const MapClickHandler = () => {
        useMapEvents({
            click(e) {
                setUserLocation(e.latlng);
                setRoute([]);
            },
        });
        return null;
    };

    const handleDispatch = async (target) => {
        if (!userLocation || !activeCity) return;
        setIsLoading(true);
        try {
            const res = await axios.post('http://localhost:5000/dispatch', {
                cityId: activeCity.id,
                user_lat: userLocation.lat,
                user_lng: userLocation.lng,
                target_lat: target.lat,
                target_lng: target.lng
            });
            setRoute(res.data.route);
            setTelemetry(res.data.telemetry);
        } catch (err) { alert("AI_ENGINE_TIMEOUT: Check Python backend."); }
        setIsLoading(false);
    };

    // Calculate Dynamic ETA based on selected vehicle
    const getETA = () => {
        if (!telemetry) return 0;
        const distanceKm = telemetry.distance_m / 1000;
        const speedKmH = VEHICLE_PROFILES[vehicle].speed;
        const hours = distanceKm / speedKmH;
        return Math.ceil(hours * 60); // Convert to minutes
    };

    return (
        <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
            {/* CLEAN PROFESSIONAL SIDEBAR */}
            <aside style={{ width: '420px', backgroundColor: 'white', zIndex: 1000, display: 'flex', flexDirection: 'column' }} className="shadow-soft">
                <header style={{ padding: '28px 24px', borderBottom: '1px solid var(--slate-100)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                        <div style={{ width: '36px', height: '36px', background: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 800, fontSize: '18px' }}>R</div>
                        <div>
                            <h1 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.3px', color: 'var(--slate-900)' }}>RouteFlow Intelligence</h1>
                            <div style={{ fontSize: '0.7rem', color: 'var(--slate-600)', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <span style={{ width: '6px', height: '6px', background: 'var(--success)', borderRadius: '50%' }}></span>
                                SYSTEM_STATUS: OPERATIONAL
                            </div>
                        </div>
                    </div>
                </header>

                <div style={{ padding: '24px', flex: 1, overflowY: 'auto' }}>
                    {/* SECTOR & CATEGORY */}
                    <section style={{ marginBottom: '24px' }}>
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <div style={{ flex: 1 }}>
                                <label style={{ fontSize: '0.70rem', fontWeight: 700, color: 'var(--slate-600)', textTransform: 'uppercase' }}>Sector</label>
                                <select 
                                    onChange={(e) => { setActiveCity(cities.find(c => c.id === e.target.value)); setRoute([]); }}
                                    style={{ width: '100%', marginTop: '6px', padding: '10px', borderRadius: '8px', border: '1px solid var(--slate-200)', backgroundColor: 'var(--slate-50)', fontSize: '0.85rem', outline: 'none' }}
                                >
                                    {cities.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                </select>
                            </div>
                            <div style={{ flex: 1 }}>
                                <label style={{ fontSize: '0.70rem', fontWeight: 700, color: 'var(--slate-600)', textTransform: 'uppercase' }}>Unit Type</label>
                                <select 
                                    value={vehicle}
                                    onChange={(e) => setVehicle(e.target.value)}
                                    style={{ width: '100%', marginTop: '6px', padding: '10px', borderRadius: '8px', border: '1px solid var(--slate-200)', backgroundColor: 'var(--slate-50)', fontSize: '0.85rem', outline: 'none' }}
                                >
                                    {Object.entries(VEHICLE_PROFILES).map(([key, data]) => (
                                        <option key={key} value={key}>{data.icon} {data.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </section>

                    <nav style={{ display: 'flex', background: 'var(--slate-100)', padding: '4px', borderRadius: '10px', marginBottom: '28px' }}>
                        {['hospitals', 'schools', 'offices'].map(type => (
                            <button 
                                key={type} onClick={() => { setCategory(type); setRoute([]); }}
                                style={{ 
                                    flex: 1, padding: '10px 0', borderRadius: '7px', fontSize: '0.75rem', cursor: 'pointer', border: 'none', transition: '0.2s',
                                    backgroundColor: category === type ? 'white' : 'transparent', color: category === type ? 'var(--primary)' : 'var(--slate-600)',
                                    fontWeight: 600, boxShadow: category === type ? '0 2px 4px rgba(0,0,0,0.05)' : 'none'
                                }}
                            >
                                {type.charAt(0).toUpperCase() + type.slice(1)}
                            </button>
                        ))}
                    </nav>

                    <div style={{ borderTop: '1px solid var(--slate-100)', paddingTop: '24px' }}>
                        <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--slate-900)', marginBottom: '16px' }}>Available Destinations</h3>
                        {!userLocation && (
                            <div style={{ padding: '20px', textAlign: 'center', backgroundColor: 'var(--slate-50)', borderRadius: '12px', border: '1px dashed var(--slate-200)' }}>
                                <p style={{ fontSize: '0.8rem', color: 'var(--slate-600)', margin: 0 }}>📍 Mark your current position on the map to begin routing.</p>
                            </div>
                        )}
                        
                        {activeCity?.targets[category].map((dest, i) => (
                            <div key={i} className="destination-card" style={{ padding: '16px', border: '1px solid var(--slate-200)', borderRadius: '12px', marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ overflow: 'hidden' }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.9rem', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{dest.name}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--slate-600)', marginTop: '2px' }}>AI Routing Available</div>
                                </div>
                                <button 
                                    disabled={!userLocation || isLoading} onClick={() => handleDispatch(dest)}
                                    className="btn-primary" 
                                    style={{ padding: '8px 16px', fontSize: '0.8rem', borderRadius: '8px', fontWeight: 600, backgroundColor: '#8b5cf6' }} // Purple Button
                                >
                                    {isLoading ? "..." : "Route"}
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                {telemetry && (
                    <footer style={{ padding: '24px', background: 'var(--slate-900)', color: 'white' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <div style={{ fontSize: '0.65rem', color: 'var(--slate-600)', fontWeight: 700, textTransform: 'uppercase' }}>Total Distance</div>
                                <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{(telemetry.distance_m / 1000).toFixed(2)} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>km</span></div>
                            </div>
                            <div style={{ width: '1px', height: '30px', backgroundColor: 'var(--slate-700)' }}></div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.65rem', color: 'var(--slate-600)', fontWeight: 700, textTransform: 'uppercase' }}>{VEHICLE_PROFILES[vehicle].icon} Est. Time ({vehicle})</div>
                                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#a78bfa' }}>{getETA()} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>min</span></div>
                            </div>
                        </div>
                    </footer>
                )}
            </aside>

            {/* MAP INTERFACE */}
            <main style={{ flex: 1, position: 'relative' }}>
                <MapContainer center={[26.91, 75.78]} zoom={13} style={{ height: '100%', width: '100%' }} zoomControl={false}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    
                    <MapAnimate center={activeCity?.center} cityId={activeCity?.id} />
                    <MapClickHandler />

                    {userLocation && <Marker position={userLocation} icon={icons.user}><Popup>Emergency Vehicle Origin</Popup></Marker>}
                    
                    {activeCity?.targets[category].map((target, idx) => (
                        <Marker key={idx} position={[target.lat, target.lng]} icon={icons[category]}>
                            <Popup>{target.name}</Popup>
                        </Marker>
                    ))}

                    {route.length > 0 && (
                        <Polyline 
                            positions={route} 
                            /* Updated to a Purple smooth curve look */
                            pathOptions={{ color: '#8b5cf6', weight: 7, lineCap: 'round', lineJoin: 'round', opacity: 0.85 }} 
                        />
                    )}
                </MapContainer>

                {/* Professional Overlay */}
                <div style={{ position: 'absolute', top: '20px', right: '20px', background: 'white', padding: '10px 18px', borderRadius: '30px', fontWeight: 700, fontSize: '11px', color: 'var(--slate-900)', zIndex: 1000, display: 'flex', alignItems: 'center', gap: '8px' }} className="shadow-soft">
                   <span style={{ color: '#8b5cf6' }}>●</span> MULTI-UNIT AI ROUTING
                </div>
            </main>
        </div>
    );
}

export default App;