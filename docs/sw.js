const CACHE_NAME = 'geomapper-elite-v2';
const ASSETS_TO_CACHE = [
    './mineral_map.html',
    './config.js',
    './styles/geomapper.css',
    './js/geomapper.js',
    './manifest.json',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css',
    'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js',
    'https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js',
    'https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore.js',
    'https://www.gstatic.com/firebasejs/9.22.0/firebase-storage.js',
    'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.es.min.js'
];

// Install Event - Cache Core Assets
self.addEventListener('install', (event) => {
    self.skipWaiting(); // Force new SW to enter 'activate' state immediately
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] Caching Assets');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// Activate Event - Cleanup Old Caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        Promise.all([
            clients.claim(), // Force new SW to control all clients immediately
            caches.keys().then((keyList) => {
                return Promise.all(keyList.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                }));
            })
        ])
    );
});

// Fetch Event - Serve from Cache or Network
self.addEventListener('fetch', (event) => {
    // Ignora requests not http/https (like chrome-extension)
    if (!event.request.url.startsWith('http')) return;

    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request).then((networkResponse) => {
                // Optional: Cache new requests dynamically? 
                // For now, keep it simple to avoid caching bad data
                return networkResponse;
            });
        })
    );
});
