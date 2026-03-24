import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap, useMapEvents } from 'react-leaflet';
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// --- ASSETS ---
const getIcon = (color) => new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [22, 35], iconAnchor: [11, 35]
});

const icons = { 
    user: getIcon('blue'), 
    hospitals: getIcon('red'), 
    schools: getIcon('gold'), 
    offices: getIcon('violet'), 
    police: getIcon('gray') 
};

const VEHICLE_PROFILES = {
    als_ambulance: { name: 'ALS Ambulance', baseSpeed: 55, icon: '🚑' },
    police_rapid: { name: 'Police Interceptor', baseSpeed: 70, icon: '🚓' }
};

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// --- MAP UTILITIES ---
function MapEventsHandler({ onMapClick, activeCity, route }) {
    const map = useMap();
    const lastCityId = useRef(activeCity?.id);

    // Fly to city when changed
    useEffect(() => {
        if (activeCity && activeCity.id !== lastCityId.current) {
            map.flyTo(activeCity.center, 12, { animate: true, duration: 1.8 });
            lastCityId.current = activeCity.id;
        }
        map.invalidateSize();
    }, [activeCity, map]);

    // Auto-zoom to route when it appears
    useEffect(() => {
        if (route && route.length > 0) {
            const bounds = L.polyline(route).getBounds();
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [route, map]);

    useMapEvents({ click(e) { onMapClick(e.latlng); } });
    return null;
}

function App() {
    const [targetHour, setTargetHour] = useState(parseInt(localStorage.getItem('saved_hour')) || 12);
    const [uiHour, setUiHour] = useState(targetHour); 
    const [userLocation, setUserLocation] = useState(JSON.parse(localStorage.getItem('user_loc')) || null);
    const [cities, setCities] = useState([]);
    const [activeCity, setActiveCity] = useState(null);
    const [category, setCategory] = useState('hospitals');
    const [selectedVehicle, setSelectedVehicle] = useState('als_ambulance');
    const [currentTarget, setCurrentTarget] = useState(null); 
    const [route, setRoute] = useState([]);
    const [telemetry, setTelemetry] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isGreenCorridor, setIsGreenCorridor] = useState(false);
    const [isPoliceSync, setIsPoliceSync] = useState(false);
    const [isForecast, setIsForecast] = useState(false);

    const theme = useMemo(() => {
        const h = uiHour;
        if (h >= 5 && h < 10) return { color: '#f59e0b', label: 'MORNING PEAK' };
        if (h >= 16 && h < 20) return { color: '#ea580c', label: 'EVENING RUSH' };
        return { color: '#2563eb', label: 'OPTIMAL FLOW' };
    }, [uiHour]);

    useEffect(() => {
        axios.get(`${API_BASE_URL}/api/cities?hour=${targetHour}`).then(res => {
            setCities(res.data);
            const savedId = localStorage.getItem('active_city_id') || 'jaipur';
            setActiveCity(res.data.find(c => c.id === savedId) || res.data[0]);
        }).catch(err => console.error("Server Offline", err));
    }, [targetHour]);

    const sortedNodes = useMemo(() => {
        if (!activeCity?.targets?.[category]) return [];
        let list = [...activeCity.targets[category]];
        if (category === 'hospitals' && userLocation) {
            const speed = isGreenCorridor ? 75 : VEHICLE_PROFILES[selectedVehicle].baseSpeed;
            return list.sort((a, b) => {
                const distA = L.latLng(userLocation).distanceTo([a.lat, a.lng]) / 1000;
                const distB = L.latLng(userLocation).distanceTo([b.lat, b.lng]) / 1000;
                const scoreA = (distA / speed * 60) + (a.waitTime || 0);
                const scoreB = (distB / speed * 60) + (b.waitTime || 0);
                return scoreA - scoreB;
            });
        }
        return list;
    }, [activeCity, category, userLocation, selectedVehicle, isGreenCorridor]);

    const triggerDispatch = useCallback(async (node, hour, corridor, sync, forecast) => {
        if (!userLocation || !activeCity) return;
        setIsLoading(true);
        try {
            const res = await axios.post(`${API_BASE_URL}/dispatch`, {
                cityId: activeCity.id, user_lat: userLocation.lat, user_lng: userLocation.lng,
                target_lat: node.lat, target_lng: node.lng, target_hour: hour,
                isGreenCorridor: corridor, isPoliceSync: sync, isForecast: forecast
            });

            if (res.data.route) {
                // FIXED: Map to [lat, lng] array format for Leaflet
                const formattedPath = res.data.route.map(p => [p.lat, p.lng]);
                const stitchedRoute = [
                    [userLocation.lat, userLocation.lng],
                    ...formattedPath,
                    [node.lat, node.lng]
                ];
                setRoute(stitchedRoute);
                setTelemetry(res.data.telemetry);
                setCurrentTarget(node);
            }
        } catch (e) { console.error("Mission Sync Error", e); }
        setIsLoading(false);
    }, [activeCity, userLocation]);

    useEffect(() => {
        if (currentTarget) triggerDispatch(currentTarget, targetHour, isGreenCorridor, isPoliceSync, isForecast);
    }, [targetHour, isGreenCorridor, isPoliceSync, isForecast]);

    const handleCityChange = (id) => {
        const city = cities.find(c => c.id === id);
        setActiveCity(city);
        localStorage.setItem('active_city_id', id);
        setRoute([]); setTelemetry(null); setCurrentTarget(null);
    };

    const handleMapClick = (latlng) => {
        setUserLocation(latlng);
        localStorage.setItem('user_loc', JSON.stringify(latlng));
        setRoute([]); setTelemetry(null); setCurrentTarget(null);
    };

    if (!activeCity) return <div className="loading-screen">INITIALIZING SECTORS...</div>;

    return (
        <div className="main-layout">
            <aside className="sidebar">
                <header className="sidebar-header">
                    <div className="logo-box" style={{ background: theme.color }}>R</div>
                    <div className="title-stack">
                        <h1 className="main-title">RouteFlow Command</h1>
                        <span className="status-tag">SYSTEM_{isLoading ? 'SYNC' : 'READY'}</span>
                    </div>
                </header>

                <div className="sidebar-scrollable">
                    <div className="input-grid">
                        <div className="input-group">
                            <label>Sector</label>
                            <select value={activeCity.id} onChange={(e) => handleCityChange(e.target.value)}>
                                {cities.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                            </select>
                        </div>
                        <div className="input-group">
                            <label>Unit</label>
                            <select value={selectedVehicle} onChange={(e) => setSelectedVehicle(e.target.value)}>
                                {Object.entries(VEHICLE_PROFILES).map(([k,v]) => <option key={k} value={k}>{v.icon} {v.name}</option>)}
                            </select>
                        </div>
                    </div>

                    <div className="mode-selector-grid">
                        <button className={`mode-btn ${isGreenCorridor ? 'active-corridor' : ''}`} onClick={() => setIsGreenCorridor(!isGreenCorridor)}>CORRIDOR</button>
                        <button className={`mode-btn ${isPoliceSync ? 'active-police' : ''}`} onClick={() => setIsPoliceSync(!isPoliceSync)}>POLICE</button>
                        <button className={`mode-btn ${isForecast ? 'active-forecast' : ''}`} onClick={() => setIsForecast(!isForecast)}>FORECAST</button>
                    </div>

                    <div className="time-slider-card">
                        <div className="slider-header" style={{ color: theme.color }}>
                            <span>{theme.label}</span>
                            <span className="time-display">{uiHour}:00</span>
                        </div>
                        <input type="range" min="0" max="23" value={uiHour} className="custom-range" 
                               onChange={(e) => setUiHour(parseInt(e.target.value))} 
                               onMouseUp={() => { setTargetHour(uiHour); localStorage.setItem('saved_hour', uiHour); }}
                               style={{ '--accent': theme.color }} />
                    </div>

                    <nav className="category-nav">
                        {['hospitals', 'schools', 'offices'].map(type => (
                            <button key={type} onClick={() => setCategory(type)} className={category === type ? 'active' : ''}>{type.toUpperCase()}</button>
                        ))}
                    </nav>

                    <div className="nodes-container">
                        {sortedNodes.map((dest) => {
                            const isLocked = currentTarget?.name === dest.name;
                            return (
                                <div key={dest.name} className={`node-card ${isLocked ? 'active-mission' : ''}`}>
                                    <div className="node-info">
                                        <h3 className="node-name">{dest.name}</h3>
                                        <p className="node-meta">
                                            {category === 'hospitals' ? (
                                                <><span className="wait-tag">⏱️ {dest.waitTime}m wait</span> | <span className="bed-tag">🛏️ {dest.beds} beds</span></>
                                            ) : 'Ready'}
                                        </p>
                                    </div>
                                    <button 
                                        className={`dispatch-btn ${isLocked ? 'locked' : 'route'}`} 
                                        onClick={() => triggerDispatch(dest, targetHour, isGreenCorridor, isPoliceSync, isForecast)}
                                        style={!isLocked ? { background: theme.color } : {}}
                                    >
                                        {isLocked ? 'LOCKED' : 'ROUTE'}
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <footer className={`telemetry-box ${telemetry && currentTarget ? 'pop-in' : 'pop-out'}`}>
                    <div className="tele-row">
                        <div className="tele-item"><label className="label-tiny">SPATIAL</label><span className="val">{(telemetry?.distance_m/1000 || 0).toFixed(2)} <small>km</small></span></div>
                        <div className="tele-item text-right"><label className="label-tiny">VELOCITY</label><span className="val" style={{ color: '#10b981' }}>{isGreenCorridor ? '75' : '55'} <small>km/h</small></span></div>
                    </div>
                    <div className="triage-total">
                        <label className="label-tiny">ESTIMATED RESCUE TIME</label>
                        <span className="total-val">{telemetry?.total_rescue_time_min || 0} <small>MIN</small></span>
                    </div>
                </footer>
            </aside>

            <main className="map-area">
                <MapContainer center={[26.91, 75.78]} zoom={12} style={{ height: '100%' }} zoomControl={false}>
                    <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" attribution='&copy; CARTO' />
                    <MapEventsHandler onMapClick={handleMapClick} activeCity={activeCity} route={route} />
                    
                    {userLocation && <Marker position={userLocation} icon={icons.user} />}
                    {activeCity.targets[category].map((t) => (<Marker key={t.name} position={[t.lat, t.lng]} icon={icons[category]} />))}
                    
                    {isPoliceSync && telemetry?.escort && (
                        <>
                            <Marker position={[telemetry.escort.lat, telemetry.escort.lng]} icon={icons.police} />
                            <Polyline 
                                positions={[[telemetry.escort.lat, telemetry.escort.lng], [telemetry.escort.meet_lat, telemetry.escort.meet_lng]]} 
                                pathOptions={{ color: '#1e293b', weight: 2, dashArray: '5, 10', opacity: 0.6 }} 
                            />
                        </>
                    )}

                    {route && route.length > 1 && route.every(coord => coord[0] && coord[1]) && (
    <Polyline 
        key={`path-${currentTarget?.name}-${Date.now()}`} // Force fresh render
        positions={route} 
        pathOptions={{ 
            color: isGreenCorridor ? '#10b981' : theme.color, 
            weight: 8, 
            opacity: 0.8,
            className: isGreenCorridor ? 'neon-pulse' : '' 
        }} 
    />
)}
                </MapContainer>
            </main>
        </div>
    );
}

export default App;