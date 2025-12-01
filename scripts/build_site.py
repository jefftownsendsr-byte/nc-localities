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
import shutil
from pathlib import Path


def copy_data(output_dir: Path, site_dir: Path):
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    geojson_src = output_dir / "nc_localities.geojson"
    csv_src = output_dir / "nc_localities.csv"

    if not geojson_src.exists():
        print(f"Warning: {geojson_src} not found. No data copied.")
    else:
        shutil.copy2(geojson_src, data_dir / "nc_localities.geojson")
        print(f"Copied {geojson_src} -> {data_dir / 'nc_localities.geojson'}")

    if not csv_src.exists():
        print(f"Warning: {csv_src} not found. No CSV copied.")
    else:
        shutil.copy2(csv_src, data_dir / "nc_localities.csv")
        print(f"Copied {csv_src} -> {data_dir / 'nc_localities.csv'}")


def create_map(site_dir: Path, geojson_path: Path | None):
    # Try folium
    try:
        import folium
    except Exception:
        folium = None

    map_html = site_dir / "map.html"
    if folium is None or geojson_path is None or not geojson_path.exists():
        print(
            "Folium not available or no geojson present; writing responsive Leaflet placeholder map.html"
        )
        with open(map_html, "w", encoding="utf8") as f:
            f.write(
                "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>NC Localities Map</title>\n<link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\"/ crossorigin=\"\"/>\n<style>html,body,#map{height:100%;margin:0;padding:0}#map{height:100vh}</style>\n</head>\n<body>\n<div id=\"map\"></div>\n<script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>\n<script>\nconst map = L.map('map').setView([35.5,-79.0], 7);\nL.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);\nfetch('data/nc_localities.geojson').then(r=>{if(!r.ok){document.body.innerHTML='<h1>No geojson found</h1><p>Put data/nc_localities.geojson into site/data/</p>';throw new Error('no geojson');}return r.json()}).then(gj=>{const layer = L.geoJSON(gj,{onEachFeature:(f,ly)=>{const p = f.properties||{};const name = p.final_name || p.NAME || p.name || '';ly.bindPopup('<b>'+name+'</b><br>'+ (p.place?('Place: '+p.place+'<br>'): '') + (p.population?('Population: '+p.population+'<br>'): ''))}}).addTo(map);map.fitBounds(layer.getBounds());}).catch(e=>console.warn(e));\n</script>\n</body>\n</html>"
            )
        return

    # Build a simple folium map with markers
    import geopandas as gpd

    gdf = gpd.read_file(str(geojson_path))
    if gdf.empty:
        print("GeoJSON present but empty; writing placeholder map.html")
        with open(map_html, "w", encoding="utf8") as f:
            f.write(
                "<!doctype html>\n<html><body>\n<h1>NC Localities Map</h1>\n<p>No features found in GeoJSON.</p>\n</body></html>"
            )
        return

    # Create a center from the median coordinate or fallback to NC
    lats = gdf.geometry.y
    lngs = gdf.geometry.x
    center = [
        float(lats.median()) if not lats.isnull().all() else 35.5,
        float(lngs.median()) if not lngs.isnull().all() else -79.0,
    ]

    m = folium.Map(location=center, zoom_start=7, tiles="OpenStreetMap")
    for _, row in gdf.iterrows():
        if row.geometry is None:
            continue
        lat = float(row.geometry.y)
        lon = float(row.geometry.x)
        popup = folium.Popup(
            html=f"<b>{row.get('final_name', row.get('NAME', row.get('name', '')))}</b>"
        )
        folium.CircleMarker(
            location=(lat, lon), radius=3, color="blue", fill=True, popup=popup
        ).add_to(m)

    m.save(str(map_html))
    print(f"Written interactive map: {map_html}")


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
