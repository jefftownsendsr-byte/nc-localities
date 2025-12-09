/**
 * GeoMapper Core Logic (Resilient Architecture)
 * Handles HUD, Firebase Sync, and User Interactions.
 * Uses Dynamic Imports for Resilience.
 */

// 1. Initialize UI IMMEDIATELY (The Genius Part: Never fail to show the interface)
// DOM Elements
const hudPanel = document.createElement('div');
hudPanel.className = 'hud-panel';
hudPanel.innerHTML = `
    <div class="hud-title">GEO-MAPPER HUD v2.0</div>
    <div class="hud-grid">
        <span class="hud-label">LATITUDE</span>
        <span class="hud-value" id="hud-lat">--.----</span>
        <span class="hud-label">LONGITUDE</span>
        <span class="hud-value" id="hud-lon">--.----</span>
        <span class="hud-label">STATUS</span>
        <span class="hud-value" id="hud-status" style="color:#f1c40f"><span class="live-dot" style="background:#f1c40f"></span>CONNECTING...</span>
        <span class="hud-label">ALTITUDE</span>
        <span class="hud-value" id="hud-alt">--</span>
    </div>
`;
document.body.appendChild(hudPanel);

// Floating Action Button
const fabContainer = document.createElement('div');
fabContainer.className = 'fab-container';
fabContainer.innerHTML = `
    <button class="fab add-marker" id="btn-add-marker" data-tooltip="Log Discovery">
        <i class="fa-solid fa-plus"></i>
    </button>
    <button class="fab" id="btn-locate" data-tooltip="My Location">
        <i class="fa-solid fa-crosshairs"></i>
    </button>
`;
document.body.appendChild(fabContainer);

// Modal HTML
const modalHTML = `
<div class="modal-overlay" id="field-log-modal">
    <div class="glass-modal">
        <div class="modal-header">
            <h2>Field Discovery Log</h2>
            <p>Record your findings for the collaborative database.</p>
        </div>
        <div class="form-group">
            <label class="form-label">Location Name</label>
            <input type="text" class="form-control" id="log-name" placeholder="e.g. Copper Ridge Find">
        </div>
        <div class="form-group">
            <label class="form-label">Mineral Type</label>
            <select class="form-control" id="log-type">
                <option value="gold">Gold</option>
                <option value="silver">Silver</option>
                <option value="copper">Copper</option>
                <option value="platinum">Platinum</option>
                <option value="emerald">Emerald</option>
                <option value="ruby_sapphire">Ruby/Sapphire</option>
                <option value="garnet">Garnet</option>
                <option value="gems">Multi-Gem</option>
                <option value="uranium">Uranium</option>
                <option value="other">Other</option>
            </select>
        </div>
        <div class="form-group">
            <label class="form-label">Observations</label>
            <textarea class="form-control" id="log-desc" placeholder="Describe the find..."></textarea>
        </div>
        <div class="form-group">
            <label class="form-label">Evidence (Photo)</label>
            <div class="upload-zone" id="upload-zone">
                <div class="upload-icon">📷</div>
                <div>Click or Drag Photo Here</div>
                <input type="file" id="file-input" accept="image/*" style="display:none">
            </div>
            <div id="file-preview" style="margin-top:10px; font-size: 0.9em; color: green;"></div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" id="btn-cancel">Cancel</button>
            <button class="btn btn-primary" id="btn-save">Upload & Save</button>
        </div>
    </div>
</div>
`;
document.body.insertAdjacentHTML('beforeend', modalHTML);

// State
let isAddingMarker = false;
let currentLatLng = null;
let firebaseActive = false;
let markersCollection = null;
let storage = null;
let addDoc, serverTimestamp, ref, uploadBytes, getDownloadURL; // Placeholders

// --- Core Interaction Logic (Offline Capable) ---
// HUD Updates
if (window.map) {
    window.map.on('mousemove', (e) => {
        const latEl = document.getElementById('hud-lat');
        const lonEl = document.getElementById('hud-lon');
        if (latEl) latEl.textContent = e.latlng.lat.toFixed(4);
        if (lonEl) lonEl.textContent = e.latlng.lng.toFixed(4);
    });

    window.map.on('locationfound', (e) => {
        const radius = e.accuracy;
        L.marker(e.latlng).addTo(window.map)
            .bindPopup("You are within " + radius + " meters from this point").openPopup();
        L.circle(e.latlng, radius).addTo(window.map);
        const altEl = document.getElementById('hud-alt');
        if (altEl) altEl.textContent = e.altitude ? e.altitude.toFixed(1) + 'm' : 'N/A';
    });

    window.map.on('click', (e) => {
        if (!isAddingMarker) return;
        currentLatLng = e.latlng;
        document.getElementById('field-log-modal').classList.add('active');
        toggleAddMarkerMode(false);
    });
}

// Button Listeners
document.getElementById('btn-locate').addEventListener('click', () => {
    if (window.map) window.map.locate({ setView: true, maxZoom: 16 });
});

const btnAdd = document.getElementById('btn-add-marker');
btnAdd.addEventListener('click', () => {
    toggleAddMarkerMode(!isAddingMarker);
});

function toggleAddMarkerMode(active) {
    isAddingMarker = active;
    btnAdd.style.background = isAddingMarker ? '#e74c3c' : '#2980b9';
    btnAdd.innerHTML = isAddingMarker ? '<i class="fa-solid fa-times"></i>' : '<i class="fa-solid fa-plus"></i>';

    if (window.map) {
        if (isAddingMarker) {
            document.body.style.cursor = 'crosshair';
            window.map.getContainer().style.cursor = 'crosshair';
        } else {
            document.body.style.cursor = 'default';
            window.map.getContainer().style.cursor = '';
        }
    }
}

// Modal Logic
document.getElementById('btn-cancel').addEventListener('click', () => {
    document.getElementById('field-log-modal').classList.remove('active');
    resetForm();
});

const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
let selectedFile = null;

uploadZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        selectedFile = e.target.files[0];
        document.getElementById('file-preview').textContent = `Selected: ${selectedFile.name}`;
    }
});

function resetForm() {
    document.getElementById('log-name').value = '';
    document.getElementById('log-desc').value = '';
    document.getElementById('file-preview').textContent = '';
    selectedFile = null;
    currentLatLng = null;
}

// Helper to add marker
function addMarkerToMap(data) {
    if (!data.latitude || !data.longitude || !window.map) return;

    const color = window.colorMap && window.colorMap[data.mineral_type] ? window.colorMap[data.mineral_type] : '#e74c3c';

    const marker = L.circleMarker([data.latitude, data.longitude], {
        radius: 14,
        fillColor: color,
        color: "#fff",
        weight: 3,
        opacity: 1,
        fillOpacity: 0.9,
        dashArray: "5, 5"
    });

    let popupContent = `
        <div class="custom-popup">
            <div class="popup-title">${data.name}</div>
            <div class="popup-badge" style="background-color: ${color}">
                ${data.mineral_type.toUpperCase()} (USER FOUND)
            </div>
            <div class="popup-description">${data.description || ''}</div>
    `;

    if (data.imageUrl) {
        popupContent += `<div style="margin-top:10px;"><img src="${data.imageUrl}" style="width:100%; border-radius:8px;"></div>`;
    }

    // Add Report Button
    popupContent += `
        <div style="margin-top:10px; text-align:right;">
            <button class="btn btn-secondary" style="font-size:0.7em; padding:4px 8px;" onclick="window.generateClaimReport('${data.name}', '${data.mineral_type}', ${data.latitude}, ${data.longitude}, '${data.description || ''}')">
                <i class="fa-solid fa-file-pdf"></i> Generate Report
            </button>
        </div>
    `;
    popupContent += `</div>`;

    marker.bindPopup(popupContent);
    marker.addTo(window.map);

    if (window.mapState && window.mapState.markerCluster) {
        window.mapState.markerCluster.addLayer(marker);
    }
}


// 2. Initialize Logic (Async)
async function initLogic() {
    // A. PWA Registration (Independent of Firebase)
    if ('serviceWorker' in navigator) {
        try {
            const reg = await navigator.serviceWorker.register('./sw.js');
            console.log('Service Worker Registered!', reg.scope);
        } catch (err) {
            console.log('Service Worker Failed:', err);
        }
    }

    // B. Firebase Loading (Target of potential failure)
    try {
        const { initializeApp } = await import("https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js");
        const { getFirestore, collection, addDoc: _addDoc, onSnapshot, serverTimestamp: _st } = await import("https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore.js");
        const { getStorage, ref: _ref, uploadBytes: _ub, getDownloadURL: _gdu } = await import("https://www.gstatic.com/firebasejs/9.22.0/firebase-storage.js");

        // Assign to global vars for modal use
        addDoc = _addDoc;
        serverTimestamp = _st;
        ref = _ref;
        uploadBytes = _ub;
        getDownloadURL = _gdu;

        const app = initializeApp(window.firebaseConfig);
        const db = getFirestore(app);
        storage = getStorage(app);
        markersCollection = collection(db, "markers");
        firebaseActive = true;

        // Update Status
        const statusEl = document.getElementById('hud-status');
        if (statusEl) {
            statusEl.innerHTML = '<span class="live-dot"></span>ONLINE';
            statusEl.style.color = '#2ecc71';
            statusEl.querySelector('.live-dot').style.background = '#2ecc71';
        }

        // Start Sync
        onSnapshot(markersCollection, (snapshot) => {
            snapshot.docChanges().forEach((change) => {
                if (change.type === "added") {
                    const data = change.doc.data();
                    addMarkerToMap(data);
                }
            });
        });

    } catch (error) {
        console.warn("Firebase Init Failed (Offline?):", error);
        const statusEl = document.getElementById('hud-status');
        if (statusEl) {
            statusEl.innerHTML = '<span class="live-dot" style="background:gray"></span>OFFLINE';
            statusEl.style.color = '#bdc3c7';
        }
    }

    // C. PDF Generator
    try {
        const { jsPDF } = await import("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.es.min.js");
        window.generateClaimReport = (name, type, lat, lon, desc) => {
            const doc = new jsPDF();
            // Header
            doc.setFillColor(44, 62, 80); // Dark Blue
            doc.rect(0, 0, 210, 40, "F");

            doc.setTextColor(255, 255, 255);
            doc.setFontSize(22);
            doc.text("OFFICIAL CLAIM REPORT", 20, 25);

            doc.setFontSize(10);
            doc.text("NC GEOMAPPER ELITE", 160, 25);

            // Content
            doc.setTextColor(0, 0, 0);
            doc.setFontSize(16);
            doc.text(`Site: ${name}`, 20, 60);

            doc.setFontSize(12);
            doc.text(`Mineral Type: ${type.toUpperCase()}`, 20, 75);

            doc.setFillColor(240, 240, 240);
            doc.rect(20, 85, 170, 30, "F");
            doc.text(`GPS Coordinates:`, 25, 95);
            doc.setFont("courier", "bold");
            doc.text(`${lat.toFixed(6)}, ${lon.toFixed(6)}`, 25, 105);
            doc.setFont("helvetica", "normal");

            doc.text(`Notes:`, 20, 130);
            const splitDesc = doc.splitTextToSize(desc, 170);
            doc.text(splitDesc, 20, 140);

            // Footer
            doc.setFontSize(10);
            doc.setTextColor(150, 150, 150);
            doc.text(`Generated by GeoMapper Elite - ${new Date().toLocaleDateString()}`, 20, 280);

            doc.save(`${name.replace(/\s+/g, '_')}_Claim_Report.pdf`);
        };
    } catch (e) {
        console.warn("PDF Module Failed:", e);
    }
}

// 3. Save Logic (Dependent on Firebase)
document.getElementById('btn-save').addEventListener('click', async () => {
    const btn = document.getElementById('btn-save');

    if (!firebaseActive) {
        alert("Offline Mode: Saving not currently supported without internet.");
        return;
    }

    btn.textContent = 'Uploading...';
    btn.disabled = true;

    try {
        const name = document.getElementById('log-name').value || "Unknown Discovery";
        const type = document.getElementById('log-type').value;
        const desc = document.getElementById('log-desc').value;
        let imageUrl = null;

        if (selectedFile) {
            const storageRef = ref(storage, 'uploads/' + Date.now() + '_' + selectedFile.name);
            await uploadBytes(storageRef, selectedFile);
            imageUrl = await getDownloadURL(storageRef);
        }

        await addDoc(markersCollection, {
            name: name,
            mineral_type: type,
            description: desc,
            latitude: currentLatLng.lat,
            longitude: currentLatLng.lng,
            imageUrl: imageUrl,
            timestamp: serverTimestamp(),
            source: 'user_submission'
        });

        alert("Discovery Logged Successfully!");
        document.getElementById('field-log-modal').classList.remove('active');
        resetForm();

    } catch (error) {
        console.error("Error adding document: ", error);
        alert("Error saving: " + error.message);
    } finally {
        btn.textContent = 'Upload & Save';
        btn.disabled = false;
    }
});

// --- The Oracle: Vein Tracer ---
let oracleActive = false;
let veinLayer = L.layerGroup();

function initOracle() {
    // 1. Add Toggle to HUD or Controls
    // Using a new control for tools
    const toolControl = L.control({ position: 'topright' });
    toolControl.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'leaflet-bar');
        div.innerHTML = `
            <button class="reset-btn" id="btn-oracle" style="background:#2c3e50; color:white; border:1px solid #f1c40f;" onclick="toggleOracle()">
                <i class="fa-solid fa-eye"></i> Oracle
            </button>
        `;
        L.DomEvent.disableClickPropagation(div);
        return div;
    };
    if (window.map) toolControl.addTo(window.map);

    window.toggleOracle = () => {
        oracleActive = !oracleActive;
        const btn = document.getElementById('btn-oracle');
        if (oracleActive) {
            btn.style.background = '#f1c40f'; // Gold
            btn.style.color = '#2c3e50';
            calculateAndDrawVeins();
            alert("The Oracle: Analyzing Topography & Mineral Alignment...");
        } else {
            btn.style.background = '#2c3e50';
            btn.style.color = 'white';
            veinLayer.clearLayers();
        }
    };
}

function calculateAndDrawVeins() {
    if (!window.map || !window.mapState || !window.mapState.allMarkers) return;

    veinLayer.clearLayers();
    const markers = window.mapState.allMarkers;
    const grouped = {};

    // 1. Group by Mineral Type
    markers.forEach(m => {
        // Use the custom property we added in the build script
        // Note: m.feature.properties is from GeoJSON, but we added .mineralType to the marker object directly in the HTML script
        const type = m.mineralType || 'unknown';
        if (!grouped[type]) grouped[type] = [];
        grouped[type].push(m);
    });

    // 2. Logic: Connect neighbors within range (e.g., 25km)
    const MAX_VEIN_DISTANCE_METERS = 25000;

    Object.keys(grouped).forEach(type => {
        const group = grouped[type];
        if (group.length < 2) return;

        const color = window.colorMap[type] || '#fff';

        for (let i = 0; i < group.length; i++) {
            for (let j = i + 1; j < group.length; j++) {
                const m1 = group[i];
                const m2 = group[j];
                const latlng1 = m1.getLatLng();
                const latlng2 = m2.getLatLng();

                const dist = latlng1.distanceTo(latlng2);

                // "The Logic": If close, they are likely part of the same system
                if (dist < MAX_VEIN_DISTANCE_METERS) {
                    const line = L.polyline([latlng1, latlng2], {
                        color: color,
                        weight: 3,
                        className: 'vein-line' // CSS Animation
                    });

                    // Tooltip explaining the logic
                    line.bindTooltip(`${formatMineralType(type)} Vein Connection<br>${(dist / 1000).toFixed(1)}km Segment`, {
                        sticky: true,
                        className: 'leaflet-tooltip'
                    });

                    veinLayer.addLayer(line);
                }
            }
        }
    });

    veinLayer.addTo(window.map);
}

// Helper (Duplicated from HTML script for safety, or we assume it's global)
function formatMineralType(type) {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}


// Go!
initLogic();
// Start Oracle after map is ready (small delay to ensure markers are populated)
setTimeout(initOracle, 2000);
