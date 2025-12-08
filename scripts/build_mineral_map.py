#!/usr/bin/env python
"""
Build mineral localities map: create a focused map showing only gem, mineral, and precious metal sites in NC

Usage:
    python scripts/build_mineral_map.py --output-dir ./output --site-dir ./site
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_mineral_map(data_csv: Path, site_dir: Path):
    """Build an interactive map from the mineral localities CSV."""
    try:
        import pandas as pd
        import json
    except ImportError as e:
        logger.error(f"Required library not available: {e}")
        return

    if not data_csv.exists():
        logger.error(f"Mineral localities CSV not found: {data_csv}")
        return

    # Read the CSV
    df = pd.read_csv(data_csv)
    logger.info(f"Loaded {len(df)} mineral localities from CSV")

    # Create GeoJSON features
    features = []
    for _, row in df.iterrows():
        feature = {
            "type": "Feature",
            "properties": {
                "name": row["name"],
                "mineral_type": row["mineral_type"],
                "description": row["description"],
            },
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["longitude"]), float(row["latitude"])],
            },
        }
        features.append(feature)

    geojson_data = {"type": "FeatureCollection", "features": features}

    # Create the HTML map with embedded GeoJSON
    map_html = site_dir / "mineral_map.html"
    geojson_str = json.dumps(geojson_data)

    # Color coding by mineral type
    color_map = {
        "gold": "#FFD700",
        "silver": "#C0C0C0",
        "copper": "#B87333",
        "platinum": "#E5E4E2",
        "emerald": "#50C878",
        "ruby_sapphire": "#E0115F",
        "garnet": "#B22222",
        "gems": "#9370DB",
        "hiddenite": "#98FF98",
        "uranium": "#4B5320",
        "other": "#808080",
    }

    html_content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NC Mineral & Gem Localities Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
<link rel="stylesheet" href="styles/geomapper.css" />
<style>
html,body,#map{{height:100%;margin:0;padding:0;font-family:Arial,sans-serif}}
#map{{height:100vh}}

/* Control Panels */
.control-panel {{
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    max-width: 280px;
}}

.search-panel {{
    margin-bottom: 10px;
}}

.search-box {{
    width: 100%;
    padding: 8px 12px;
    border: 2px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    box-sizing: border-box;
}}

.search-box:focus {{
    outline: none;
    border-color: #4CAF50;
}}

.filter-panel {{
    max-height: 400px;
    overflow-y: auto;
}}

.filter-header {{
    font-weight: bold;
    margin-bottom: 10px;
    font-size: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.filter-buttons {{
    display: flex;
    gap: 5px;
    margin-bottom: 10px;
}}

.filter-btn {{
    padding: 4px 8px;
    font-size: 11px;
    border: 1px solid #ddd;
    background: #f5f5f5;
    border-radius: 3px;
    cursor: pointer;
}}

.filter-btn:hover {{
    background: #e0e0e0;
}}

.filter-item {{
    margin: 8px 0;
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: background 0.2s;
}}

.filter-item:hover {{
    background: #f5f5f5;
}}

.filter-checkbox {{
    margin-right: 8px;
    cursor: pointer;
}}

.filter-color {{
    display: inline-block;
    width: 18px;
    height: 18px;
    margin-right: 8px;
    border: 2px solid #000;
    border-radius: 50%;
    vertical-align: middle;
}}

.filter-label {{
    flex: 1;
    font-size: 14px;
}}

/* Enhanced Legend */
.legend {{
    background: white;
    padding: 12px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    line-height: 24px;
    font-family: Arial, sans-serif;
    font-size: 14px;
}}

.legend-title {{
    margin: 0 0 10px 0;
    font-size: 16px;
    font-weight: bold;
}}

.legend-item {{
    margin: 6px 0;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: background 0.2s;
}}

.legend-item:hover {{
    background: #f5f5f5;
}}

.legend-item.inactive {{
    opacity: 0.4;
}}

.legend-color {{
    display: inline-block;
    width: 18px;
    height: 18px;
    margin-right: 8px;
    border: 2px solid #000;
    border-radius: 50%;
    vertical-align: middle;
}}

/* Enhanced Popups */
.custom-popup {{
    font-family: Arial, sans-serif;
}}

.popup-title {{
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 8px;
    color: #333;
}}

.popup-badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    color: white;
    margin-bottom: 8px;
}}

.popup-description {{
    font-size: 13px;
    line-height: 1.4;
    color: #666;
    max-width: 250px;
}}

/* Tooltips */
.leaflet-tooltip {{
    background: rgba(0,0,0,0.8);
    border: none;
    color: white;
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 4px;
}}

/* Reset Button */
.reset-btn {{
    background: white;
    padding: 8px 12px;
    border-radius: 4px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    cursor: pointer;
    font-size: 13px;
    border: 2px solid #ddd;
    font-weight: bold;
}}

.reset-btn:hover {{
    background: #f5f5f5;
}}

/* Mobile Responsive */
@media (max-width: 768px) {{
    .control-panel {{
        max-width: 90%;
        font-size: 12px;
    }}
    .legend {{
        font-size: 12px;
    }}
}}

/* Marker Clusters */
.marker-cluster-small {{
    background-color: rgba(181, 226, 140, 0.6);
}}
.marker-cluster-small div {{
    background-color: rgba(110, 204, 57, 0.6);
}}
.marker-cluster-medium {{
    background-color: rgba(241, 211, 87, 0.6);
}}
.marker-cluster-medium div {{
    background-color: rgba(240, 194, 12, 0.6);
}}
.marker-cluster-large {{
    background-color: rgba(253, 156, 115, 0.6);
}}
.marker-cluster-large div {{
    background-color: rgba(241, 128, 23, 0.6);
}}
</style>
</head>
<body>
<div id="map"></div>

<!-- Firebase Config -->
<script src="config.js"></script>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const data = {geojson_str};
// Expose colorMap to window for external JS
window.colorMap = {json.dumps(color_map)};
const colorMap = window.colorMap;

// State management
// Expose to window for external JS
window.mapState = {{
    activeFilters: new Set(Object.keys(colorMap)),
    allMarkers: [],
    markerCluster: null
}};
const mapState = window.mapState;

// Initialize map
// Expose map to window for external JS
window.map = L.map('map').setView([35.5,-80.5], 7);
const map = window.map;

L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{
    maxZoom:19,
    attribution:'&copy; OpenStreetMap contributors'
}}).addTo(map);

// Create marker cluster group
mapState.markerCluster = L.markerClusterGroup({{
    maxClusterRadius: 50,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true
}});

// Helper function to get badge color
function getBadgeColor(mineralType) {{
    const color = colorMap[mineralType] || '#9370DB';
    // Darken the color for better text contrast
    return color;
}}

// Helper function to format mineral type
function formatMineralType(type) {{
    return type.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
}}

// Create markers
if (data && data.features && data.features.length > 0) {{
    data.features.forEach(feature => {{
        const props = feature.properties || {{}};
        const coords = feature.geometry.coordinates;
        const latlng = [coords[1], coords[0]];
        const mineralType = props.mineral_type || 'gems';
        const color = colorMap[mineralType] || '#9370DB';
        
        // Create marker
        const marker = L.circleMarker(latlng, {{
            radius: 12,
            fillColor: color,
            color: "#000",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }});
        
        // Enhanced popup
        const popupContent = `
            <div class="custom-popup">
                <div class="popup-title">${{props.name || 'Unknown'}}</div>
                <div class="popup-badge" style="background-color: ${{getBadgeColor(mineralType)}}">
                    ${{formatMineralType(mineralType)}}
                </div>
                <div class="popup-description">${{props.description || 'No description available'}}</div>
            </div>
        `;
        marker.bindPopup(popupContent);
        
        // Hover tooltip
        marker.bindTooltip(props.name || 'Unknown', {{
            permanent: false,
            direction: 'top',
            offset: [0, -10]
        }});
        
        // Store mineral type for filtering
        marker.mineralType = mineralType;
        marker.searchName = (props.name || '').toLowerCase();
        
        mapState.allMarkers.push(marker);
    }});
    
    // Add all markers to cluster initially
    updateMarkers();
    map.fitBounds(mapState.markerCluster.getBounds(), {{maxZoom: 8}});
}}

// Update markers based on filters
function updateMarkers() {{
    mapState.markerCluster.clearLayers();
    const filteredMarkers = mapState.allMarkers.filter(m => 
        mapState.activeFilters.has(m.mineralType)
    );
    mapState.markerCluster.addLayers(filteredMarkers);
    if (!map.hasLayer(mapState.markerCluster)) {{
        map.addLayer(mapState.markerCluster);
    }}
}}

// Filter functions
function toggleFilter(mineralType) {{
    if (mapState.activeFilters.has(mineralType)) {{
        mapState.activeFilters.delete(mineralType);
    }} else {{
        mapState.activeFilters.add(mineralType);
    }}
    updateMarkers();
    updateLegendUI();
    updateFilterUI();
}}

function selectAllFilters() {{
    mapState.activeFilters = new Set(Object.keys(colorMap));
    updateMarkers();
    updateLegendUI();
    updateFilterUI();
}}

function deselectAllFilters() {{
    mapState.activeFilters.clear();
    updateMarkers();
    updateLegendUI();
    updateFilterUI();
}}

function updateFilterUI() {{
    Object.keys(colorMap).forEach(type => {{
        const checkbox = document.getElementById('filter-' + type);
        if (checkbox) {{
            checkbox.checked = mapState.activeFilters.has(type);
        }}
    }});
}}

function updateLegendUI() {{
    Object.keys(colorMap).forEach(type => {{
        const item = document.getElementById('legend-' + type);
        if (item) {{
            if (mapState.activeFilters.has(type)) {{
                item.classList.remove('inactive');
            }} else {{
                item.classList.add('inactive');
            }}
        }}
    }});
}}

// Search function
function searchLocalities(query) {{
    query = query.toLowerCase().trim();
    if (!query) {{
        // Reset to show all filtered markers
        updateMarkers();
        return;
    }}
    
    // Find matching markers
    const matches = mapState.allMarkers.filter(m => 
        m.searchName.includes(query) && mapState.activeFilters.has(m.mineralType)
    );
    
    if (matches.length > 0) {{
        // Clear and show only matches
        mapState.markerCluster.clearLayers();
        mapState.markerCluster.addLayers(matches);
        
        // Zoom to results
        if (matches.length === 1) {{
            map.setView(matches[0].getLatLng(), 12);
            matches[0].openPopup();
        }} else {{
            const group = L.featureGroup(matches);
            map.fitBounds(group.getBounds(), {{maxZoom: 10}});
        }}
    }}
}}

// Add search control
const searchControl = L.control({{position: 'topleft'}});
searchControl.onAdd = function(map) {{
    const div = L.DomUtil.create('div', 'control-panel search-panel');
    div.innerHTML = `
        <input type="text" 
               class="search-box" 
               id="searchBox" 
               placeholder="Search localities..."
               autocomplete="off">
    `;
    
    L.DomEvent.disableClickPropagation(div);
    
    return div;
}};
searchControl.addTo(map);

// Add search event listener
setTimeout(() => {{
    const searchBox = document.getElementById('searchBox');
    if (searchBox) {{
        let searchTimeout;
        searchBox.addEventListener('input', (e) => {{
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {{
                searchLocalities(e.target.value);
            }}, 300);
        }});
        
        searchBox.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') {{
                searchLocalities(e.target.value);
            }}
        }});
    }}
}}, 100);

// Add filter control
const filterControl = L.control({{position: 'topleft'}});
filterControl.onAdd = function(map) {{
    const div = L.DomUtil.create('div', 'control-panel filter-panel');
    
    let html = '<div class="filter-header">Filter by Type</div>';
    html += '<div class="filter-buttons">';
    html += '<button class="filter-btn" onclick="selectAllFilters()">All</button>';
    html += '<button class="filter-btn" onclick="deselectAllFilters()">None</button>';
    html += '</div>';
    
    const types = [
        ['gold', 'Gold'],
        ['silver', 'Silver'],
        ['copper', 'Copper'],
        ['platinum', 'Platinum'],
        ['emerald', 'Emerald'],
        ['ruby_sapphire', 'Ruby/Sapphire'],
        ['garnet', 'Garnet'],
        ['gems', 'Multi-Gem'],
        ['hiddenite', 'Hiddenite'],
        ['uranium', 'Uranium'],
        ['other', 'Other']
    ];
    
    types.forEach(([key, label]) => {{
        const color = colorMap[key] || '#9370DB';
        html += `
            <div class="filter-item" onclick="toggleFilter('${{key}}')">
                <input type="checkbox" 
                       class="filter-checkbox" 
                       id="filter-${{key}}" 
                       checked 
                       onclick="event.stopPropagation(); toggleFilter('${{key}}')">
                <span class="filter-color" style="background-color:${{color}}"></span>
                <span class="filter-label">${{label}}</span>
            </div>
        `;
    }});
    
    div.innerHTML = html;
    L.DomEvent.disableClickPropagation(div);
    
    return div;
}};
filterControl.addTo(map);

// Add interactive legend
const legend = L.control({{position: 'bottomright'}});
legend.onAdd = function(map) {{
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = '<h4 class="legend-title">Mineral Types</h4>';
    
    const types = [
        ['gold', 'Gold'],
        ['silver', 'Silver'],
        ['copper', 'Copper'],
        ['platinum', 'Platinum'],
        ['emerald', 'Emerald'],
        ['ruby_sapphire', 'Ruby/Sapphire'],
        ['garnet', 'Garnet'],
        ['gems', 'Multi-Gem'],
        ['hiddenite', 'Hiddenite'],
        ['uranium', 'Uranium'],
        ['other', 'Other']
    ];
    
    types.forEach(([key, label]) => {{
        const color = colorMap[key] || '#9370DB';
        div.innerHTML += `
            <div class="legend-item" id="legend-${{key}}" onclick="toggleFilter('${{key}}')">
                <span class="legend-color" style="background-color:${{color}}"></span>
                ${{label}}
            </div>
        `;
    }});
    
    L.DomEvent.disableClickPropagation(div);
    
    return div;
}};
legend.addTo(map);

// Add reset view button
const resetControl = L.control({{position: 'topright'}});
resetControl.onAdd = function(map) {{
    const div = L.DomUtil.create('div', 'leaflet-bar');
    div.innerHTML = '<button class="reset-btn" onclick="resetView()">Reset View</button>';
    L.DomEvent.disableClickPropagation(div);
    return div;
}};
resetControl.addTo(map);

function resetView() {{
    document.getElementById('searchBox').value = '';
    selectAllFilters();
    if (mapState.markerCluster.getBounds().isValid()) {{
        map.fitBounds(mapState.markerCluster.getBounds(), {{maxZoom: 8}});
    }}
}}
</script>

<!-- GeoMapper Logic (Must be after map init) -->
<script type="module" src="js/geomapper.js"></script>

</body>
</html>"""

    try:
        with open(map_html, "w", encoding="utf8") as f:
            f.write(html_content)
        logger.info(f"Created mineral localities map: {map_html}")
    except Exception as e:
        logger.error(f"Failed to write mineral map: {e}")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-csv",
        default="./data/mineral_localities.csv",
        help="Path to mineral localities CSV",
    )
    parser.add_argument(
        "--site-dir", default="./site", help="Path to site/ folder to modify"
    )
    args = parser.parse_args(argv)

    data_csv = Path(args.data_csv).resolve()
    site_dir = Path(args.site_dir).resolve()
    site_dir.mkdir(parents=True, exist_ok=True)

    build_mineral_map(data_csv, site_dir)


if __name__ == "__main__":
    main()
