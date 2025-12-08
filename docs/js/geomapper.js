/**
 * GeoMapper Core Logic
 * Handles HUD, Firebase Sync, and User Interactions.
 */

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
import { getFirestore, collection, addDoc, onSnapshot, serverTimestamp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore.js";
import { getStorage, ref, uploadBytes, getDownloadURL } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-storage.js";

// Initialize Firebase
// process.env keys would be better, but for this simpler setup using window.config
const app = initializeApp(window.firebaseConfig);
const db = getFirestore(app);
const storage = getStorage(app);
const markersCollection = collection(db, "markers");

// State
let isAddingMarker = false;
let tempMarker = null;
let currentLatLng = null;

// DOM Elements
const hudPanel = document.createElement('div');
hudPanel.className = 'hud-panel';
hudPanel.innerHTML = `
    <div class="hud-title">GEO-MAPPER HUD v1.0</div>
    <div class="hud-grid">
        <span class="hud-label">LATITUDE</span>
        <span class="hud-value" id="hud-lat">--.----</span>
        <span class="hud-label">LONGITUDE</span>
        <span class="hud-value" id="hud-lon">--.----</span>
        <span class="hud-label">STATUS</span>
        <span class="hud-value" style="color:#2ecc71"><span class="live-dot"></span>ONLINE</span>
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


// --- Interaction Logic ---

// HUD Updates
map.on('mousemove', (e) => {
    document.getElementById('hud-lat').textContent = e.latlng.lat.toFixed(4);
    document.getElementById('hud-lon').textContent = e.latlng.lng.toFixed(4);
});

// User Location
document.getElementById('btn-locate').addEventListener('click', () => {
    map.locate({ setView: true, maxZoom: 16 });
});

map.on('locationfound', (e) => {
    const radius = e.accuracy;
    L.marker(e.latlng).addTo(map)
        .bindPopup("You are within " + radius + " meters from this point").openPopup();
    L.circle(e.latlng, radius).addTo(map);
    document.getElementById('hud-alt').textContent = e.altitude ? e.altitude.toFixed(1) + 'm' : 'N/A';
});

// Add Marker Mode
const btnAdd = document.getElementById('btn-add-marker');
btnAdd.addEventListener('click', () => {
    isAddingMarker = !isAddingMarker;
    btnAdd.style.background = isAddingMarker ? '#e74c3c' : '#2980b9'; // Toggle Color
    btnAdd.innerHTML = isAddingMarker ? '<i class="fa-solid fa-times"></i>' : '<i class="fa-solid fa-plus"></i>';

    if (isAddingMarker) {
        document.body.style.cursor = 'crosshair';
        map.getContainer().style.cursor = 'crosshair';
    } else {
        document.body.style.cursor = 'default';
        map.getContainer().style.cursor = '';
    }
});

map.on('click', (e) => {
    if (!isAddingMarker) return;

    currentLatLng = e.latlng;

    // Open Modal
    document.getElementById('field-log-modal').classList.add('active');

    // Reset cursor
    isAddingMarker = false;
    btnAdd.style.background = '#2980b9';
    btnAdd.innerHTML = '<i class="fa-solid fa-plus"></i>';
    document.body.style.cursor = 'default';
    map.getContainer().style.cursor = '';
});

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

document.getElementById('btn-save').addEventListener('click', async () => {
    const btn = document.getElementById('btn-save');
    btn.textContent = 'Uploading...';
    btn.disabled = true;

    try {
        const name = document.getElementById('log-name').value || "Unknown Discovery";
        const type = document.getElementById('log-type').value;
        const desc = document.getElementById('log-desc').value;

        let imageUrl = null;

        // Upload photo if exists
        if (selectedFile) {
            const storageRef = ref(storage, 'uploads/' + Date.now() + '_' + selectedFile.name);
            await uploadBytes(storageRef, selectedFile);
            imageUrl = await getDownloadURL(storageRef);
        }

        // Save to Firestore
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

function resetForm() {
    document.getElementById('log-name').value = '';
    document.getElementById('log-desc').value = '';
    document.getElementById('file-preview').textContent = '';
    selectedFile = null;
    currentLatLng = null;
}

// --- Real-time Sync --- (The Magic part)
onSnapshot(markersCollection, (snapshot) => {
    snapshot.docChanges().forEach((change) => {
        if (change.type === "added") {
            const data = change.doc.data();
            addMarkerToMap(data);
        }
    });
});

function addMarkerToMap(data) {
    if (!data.latitude || !data.longitude) return;

    const color = window.colorMap && window.colorMap[data.mineral_type] ? window.colorMap[data.mineral_type] : '#e74c3c';

    const marker = L.circleMarker([data.latitude, data.longitude], {
        radius: 14, // Slightly bigger than standard
        fillColor: color,
        color: "#fff",
        weight: 3, // Thicker border
        opacity: 1,
        fillOpacity: 0.9,
        dashArray: "5, 5" // Dashed line to indicate "Unverified/User"
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

    popupContent += `</div>`;

    marker.bindPopup(popupContent);
    marker.addTo(map); // Add directly to map (or cluster if you exposed it)

    // Ideally add to the cluster group if exposed, but adding to map works for now
    if (window.mapState && window.mapState.markerCluster) {
        window.mapState.markerCluster.addLayer(marker);
    }
}
