#!/usr/bin/env python
"""
Build site: copy generated GeoJSON and CSV into site/data and create a map.html

This script expects the pipeline to have created output/nc_localities.geojson and output/nc_localities.csv.
If folium is installed, it will create an interactive map (like the pipeline's map). Otherwise it will copy a simple placeholder map template.

Usage:
    python scripts/build_site.py --output-dir ./output --site-dir ./site

"""
from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def copy_data(output_dir: Path, site_dir: Path):
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    geojson_src = output_dir / "nc_localities.geojson"
    csv_src = output_dir / "nc_localities.csv"

    if not geojson_src.exists():
        logger.warning(f"{geojson_src} not found. No data copied.")
    else:
        try:
            shutil.copy2(geojson_src, data_dir / "nc_localities.geojson")
            logger.info(f"Copied {geojson_src} -> {data_dir / 'nc_localities.geojson'}")
        except Exception as e:
            logger.error(f"Failed to copy {geojson_src}: {e}")

    if not csv_src.exists():
        logger.warning(f"{csv_src} not found. No CSV copied.")
    else:
        try:
            shutil.copy2(csv_src, data_dir / "nc_localities.csv")
            logger.info(f"Copied {csv_src} -> {data_dir / 'nc_localities.csv'}")
        except Exception as e:
            logger.error(f"Failed to copy {csv_src}: {e}")


def create_map(site_dir: Path, geojson_path: Path | None):
    # Try folium
    try:
        import folium
    except ImportError:
        folium = None

    map_html = site_dir / "map.html"
    if folium is None or geojson_path is None or not geojson_path.exists():
        logger.info(
            "Folium not available or no geojson present; writing responsive Leaflet placeholder map.html"
        )
        
        geojson_content = "{}"
        if geojson_path and geojson_path.exists():
            try:
                with open(geojson_path, "r", encoding="utf8") as f:
                    geojson_content = f.read()
            except Exception as e:
                logger.error(f"Failed to read geojson for embedding: {e}")

        try:
            with open(map_html, "w", encoding="utf8") as f:
                f.write(
                    f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NC Localities Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<style>html,body,#map{{height:100%;margin:0;padding:0}}#map{{height:100vh}}</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const data = {geojson_content};
const map = L.map('map').setView([35.5,-79.0], 7);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}}).addTo(map);

if (data && data.features && data.features.length > 0) {{
    const layer = L.geoJSON(data, {{
        pointToLayer: (feature, latlng) => {{
            return L.circleMarker(latlng, {{
                radius: 8,
                fillColor: "#ff7800",
                color: "#000",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }});
        }},
        onEachFeature: (f, ly) => {{
            const p = f.properties || {{}};
            const name = p.final_name || p.NAME || p.name || '';
            ly.bindPopup('<b>' + name + '</b><br>' + 
                (p.place ? ('Place: ' + p.place + '<br>') : '') + 
                (p.population ? ('Population: ' + p.population + '<br>') : ''));
        }}
    }}).addTo(map);
    map.fitBounds(layer.getBounds(), {{maxZoom: 12}});
}} else {{
    console.warn("No features in embedded data");
}}
</script>
</body>
</html>"""
                )
        except Exception as e:
            logger.error(f"Failed to write placeholder map: {e}")
        return

    # Build a simple folium map with markers
    try:
        import geopandas as gpd
        gdf = gpd.read_file(str(geojson_path))
    except Exception as e:
        logger.error(f"Failed to read GeoJSON with geopandas: {e}")
        return

    if gdf.empty:
        logger.warning("GeoJSON present but empty; writing placeholder map.html")
        try:
            with open(map_html, "w", encoding="utf8") as f:
                f.write(
                    "<!doctype html>\n<html><body>\n<h1>NC Localities Map</h1>\n<p>No features found in GeoJSON.</p>\n</body></html>"
                )
        except Exception as e:
            logger.error(f"Failed to write empty placeholder map: {e}")
        return

    # Create a center from the median coordinate or fallback to NC
    lats = gdf.geometry.y
    lngs = gdf.geometry.x
    center = [
        float(lats.median()) if not lats.isnull().all() else 35.5,
        float(lngs.median()) if not lngs.isnull().all() else -79.0,
    ]

    try:
        m = folium.Map(location=center, zoom_start=7, tiles="OpenStreetMap")
        for _, row in gdf.iterrows():
            if row.geometry is None:
                continue
            lat = float(row.geometry.y)
            lon = float(row.geometry.x)
            popup_content = f"<b>{row.get('final_name', row.get('NAME', row.get('name', '')))}</b>"
            popup = folium.Popup(html=popup_content)
            folium.CircleMarker(
                location=(lat, lon), radius=3, color="blue", fill=True, popup=popup
            ).add_to(m)

        m.save(str(map_html))
        logger.info(f"Written interactive map: {map_html}")
    except Exception as e:
        logger.error(f"Failed to create/save folium map: {e}")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Directory where pipeline exports are stored",
    )
    parser.add_argument(
        "--site-dir", default="./site", help="Path to site/ folder to modify"
    )
    parser.add_argument(
        "--year",
        default=None,
        help="Optional year argument (ignored) to stay compatible with older scripts",
    )
    args = parser.parse_args(argv)

    outdir = Path(args.output_dir).resolve()
    sdir = Path(args.site_dir).resolve()

    copy_data(outdir, sdir)
    geojson_path = outdir / "nc_localities.geojson"
    if geojson_path.exists():
        create_map(sdir, geojson_path)


if __name__ == "__main__":
    main()
