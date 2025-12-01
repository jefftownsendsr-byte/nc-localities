"""
Build North Carolina localities dataset: fetch OSM places via Overpass & Census TIGER places
Export GeoJSON, CSV, Shapefile, and an interactive map (folium)

Usage:
    python scripts/build_nc_localities.py --output-dir ./output --year 2025

"""

import argparse
import os
import json
import tempfile
from pathlib import Path

requests = None
try:
    import geopandas as gpd
except Exception:
    gpd = None
try:
    import pandas as pd
except Exception:
    pd = None
try:
    from shapely.geometry import Point
except Exception:
    Point = None

# Constants
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CENSUS_BASE = "https://www2.census.gov/geo/tiger/"

# User agent to avoid being blocked
HEADERS = {"User-Agent": "nc-localities/1.0 (+https://example.com)"}


def fetch_state_polygon(state_name="North Carolina"):
    # Import requests lazily to allow running sample mode without requests installed
    global requests
    if requests is None:
        import requests as _requests

        requests = _requests
    params = {
        "q": state_name,
        "format": "jsonv2",
        "polygon_geojson": 1,
    }
    resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    items = resp.json()
    if not items:
        raise RuntimeError(f"State polygon for {state_name} not found via Nominatim")
    for itm in items:
        if itm.get("osm_type") in ("relation", "way") and "geojson" in itm:
            return itm
    return items[0]


def polygon_to_overpass_poly(poly_geojson):
    coords = poly_geojson["coordinates"][0]
    return " ".join(f"{lat} {lon}" for lon, lat in coords)


def fetch_osm_places(polygon_str):
    # Import requests lazily to allow running sample mode without requests installed
    global requests
    if requests is None:
        import requests as _requests

        requests = _requests
    node_query = f'(node["place"]({polygon_str});way["place"]({polygon_str});relation["place"]({polygon_str}););out center tags;'
    payload = f"[out:json][timeout:300];{node_query}"

    resp = requests.post(OVERPASS_URL, data=payload, headers=HEADERS, timeout=600)
    resp.raise_for_status()
    data = resp.json()

    elements = data.get("elements", [])
    rows = []
    for el in elements:
        el_type = el.get("type")
        tags = el.get("tags", {})
        name = tags.get("name")
        place = tags.get("place")
        population = tags.get("population")
        if el_type == "node":
            geom = Point(el.get("lon"), el.get("lat"))
        else:
            center = el.get("center")
            if center:
                geom = Point(center.get("lon"), center.get("lat"))
            else:
                continue
        rows.append(
            {
                "osm_id": el.get("id"),
                "osm_type": el_type,
                "name": name,
                "place": place,
                "population": population,
                "tags": tags,
                "geometry": geom,
            }
        )

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    return gdf


def fetch_census_places(state_fips="37", year=2025):
    global requests
    if requests is None:
        import requests as _requests

        requests = _requests
    base = f"{CENSUS_BASE}TIGER{year}/PLACE/"
    filename = f"tl_{year}_{state_fips}_place.zip"
    url = base + filename
    resp = requests.get(url, headers=HEADERS, stream=True, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to download census TIGER {year} place shapefile from {url}"
        )
    tmpdir = tempfile.mkdtemp()
    zpath = os.path.join(tmpdir, filename)
    with open(zpath, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            fh.write(chunk)
    gdf = gpd.read_file("zip://" + zpath)
    return gdf


def merge_and_export(osm_gdf, census_gdf, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    census_gdf = census_gdf.to_crs("EPSG:4326")
    census_gdf = census_gdf[["GEOID", "NAME", "geometry"]].rename(
        columns={"NAME": "place_name", "GEOID": "geoid"}
    )
    osm_gdf = osm_gdf.to_crs("EPSG:4326")
    osm_gdf["name_norm"] = osm_gdf["name"].str.strip()
    joined = gpd.sjoin(osm_gdf, census_gdf, how="left", predicate="within")
    joined["final_name"] = joined["name_norm"].fillna(joined["place_name"])
    out_geo = joined[
        ["osm_id", "osm_type", "final_name", "place", "population", "geoid", "geometry"]
    ]
    out_geo["x_round"] = out_geo.geometry.x.round(6)
    out_geo["y_round"] = out_geo.geometry.y.round(6)
    out_geo["dup_key"] = (
        out_geo["x_round"].astype(str)
        + ","
        + out_geo["y_round"].astype(str)
        + ","
        + out_geo["final_name"].fillna("")
    )
    out_geo = out_geo.sort_values(by=["population"], ascending=False)
    out_geo = out_geo.drop_duplicates(subset=["dup_key"])
    out_geo = out_geo.drop(columns=["x_round", "y_round", "dup_key"])
    geojson_path = output_dir / "nc_localities.geojson"
    csv_path = output_dir / "nc_localities.csv"
    shp_dir = output_dir / "nc_localities_shp"
    html_path = output_dir / "nc_localities_map.html"
    out_geo.to_file(geojson_path, driver="GeoJSON")
    out_geo.drop(columns="geometry").to_csv(csv_path, index=False)
    shp_dir.mkdir(parents=True, exist_ok=True)
    out_geo.to_file(str(shp_dir / "nc_localities.shp"))
    try:
        import folium
    except Exception:
        print("folium not installed; skipping HTML map")
        return
    center = [35.5, -79.0]
    import folium

    m = folium.Map(location=center, zoom_start=7, tiles="OpenStreetMap")
    for _, row in out_geo.iterrows():
        coords = (row.geometry.y, row.geometry.x)
        popup = folium.Popup(
            html=f"<b>{row.final_name}</b><br>Place: {row.place}<br>Population: {row.population}<br>OSM ID: {row.osm_id}"
        )
        folium.CircleMarker(
            coords, radius=3, color="blue", fill=True, popup=popup
        ).add_to(m)
    m.save(html_path)
    site_dir = Path(__file__).resolve().parents[1] / "site"
    if site_dir.exists():
        data_dir = site_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        geojson_out = data_dir / "nc_localities.geojson"
        csv_out = data_dir / "nc_localities.csv"
        html_out = site_dir / "map.html"
        import shutil

        out_geo.to_file(geojson_out, driver="GeoJSON")
        out_geo.drop(columns="geometry").to_csv(csv_out, index=False)
        try:
            shutil.copyfile(str(html_path), str(html_out))
        except Exception as e:
            print(f"Warning: failed to copy map.html to site path: {e}")

    def parse_args(argv=None):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--output-dir", default="./output", help="Directory for exports"
        )
        parser.add_argument("--state", default="North Carolina")
        parser.add_argument("--state-fips", default="37")
        parser.add_argument(
            "--year", default=2025, type=int, help="Census TIGER year (e.g., 2025)"
        )
        parser.add_argument(
            "--non-interactive",
            action="store_true",
            help="Run fully non-interactively (default: false)",
        )
        parser.add_argument(
            "--pack-output",
            action="store_true",
            help="Zip output into a single archive after export",
        )
        parser.add_argument(
            "--use-sample",
            action="store_true",
            help="Use a small sample dataset instead of fetching from OSM/Census for quick testing",
        )
        args = parser.parse_args(argv)
        return args

    def get_osm_and_census(args, outdir: Path):
        """Return (osm_gdf, census_gdf), handling sample mode and downloads."""
        osm_gdf = None
        census_gdf = None
        if args.use_sample:
            print("Using sample data for quick local testing...")
            # If geopandas is available, construct a GeoDataFrame; otherwise write minimal output files directly.
            try:
                from shapely.geometry import Point as ShapelyPoint
                import geopandas as gpd_mod

                rows = [
                    {
                        "osm_id": 1,
                        "osm_type": "node",
                        "name": "Sample Place",
                        "place": "city",
                        "population": "1000",
                        "tags": {},
                        "geometry": ShapelyPoint(-79.0, 35.5),
                    }
                ]
                osm_gdf = gpd_mod.GeoDataFrame(
                    rows, geometry="geometry", crs="EPSG:4326"
                )
                census_gdf = gpd_mod.GeoDataFrame(
                    columns=["GEOID", "NAME", "geometry"],
                    geometry="geometry",
                    crs="EPSG:4326",
                )
            except Exception:
                # Fall back to writing simple GeoJSON and CSV files to output for the build_site step
                out_geojson_path = outdir / "nc_localities.geojson"
                out_csv_path = outdir / "nc_localities.csv"
                gj = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "osm_id": 1,
                                "final_name": "Sample Place",
                                "place": "city",
                                "population": "1000",
                            },
                            "geometry": {"type": "Point", "coordinates": [-79.0, 35.5]},
                        }
                    ],
                }
                outdir.mkdir(parents=True, exist_ok=True)
                with open(out_geojson_path, "w", encoding="utf8") as fh:
                    json.dump(gj, fh)
                with open(out_csv_path, "w", encoding="utf8") as fh:
                    fh.write(
                        "osm_id,final_name,place,geoid,x,y\n1,Sample Place,city,,,-79.0,35.5\n"
                    )
                print(
                    "Wrote sample geojson & csv to output folder (no geopandas required)"
                )
                # Create minimal in-memory placeholders so merge_and_export can proceed if needed
                osm_gdf = None
                census_gdf = None
        else:
            print("Fetching state polygon from Nominatim...")
            state = fetch_state_polygon(args.state)
            poly_geojson = state["geojson"]
            poly_str = polygon_to_overpass_poly(poly_geojson)
            print(
                "Querying Overpass for place nodes/ways/relations in the state polygon..."
            )
            osm_gdf = fetch_osm_places(poly_str)

        # If not sample mode, try fetching census
        if not args.use_sample:
            print(
                "Downloading Census TIGER place shapefile (attempting the requested year, falling back if needed)..."
            )
            census_gdf = None
            for y in range(args.year, 2019, -1):
                try:
                    census_gdf = fetch_census_places(state_fips=args.state_fips, year=y)
                    print(
                        f"Census TIGER places loaded (year {y}): {len(census_gdf)} features"
                    )
                    break
                except Exception as e:
                    print(f"Failed to fetch Census TIGER places for {y}: {e}")
                    census_gdf = None
        else:
            census_gdf = None

        if census_gdf is None:
            print(
                "No Census TIGER place shapefile could be fetched. Continuing with OSM points only."
            )
            if gpd is not None:
                census_gdf = gpd.GeoDataFrame(
                    columns=["GEOID", "NAME", "geometry"],
                    geometry="geometry",
                    crs="EPSG:4326",
                )
            else:
                census_gdf = None

        return osm_gdf, census_gdf


def main(argv=None):
    # Entry point wrapper: parse args and run the pipeline
    args = parse_args(argv)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    osm_gdf, census_gdf = get_osm_and_census(args, outdir)
    # After this point, osm_gdf and census_gdf are set (or sample mode created outputs)
    if osm_gdf is not None:
        try:
            print(f"Fetched {len(osm_gdf)} OSM place elements")
        except Exception:
            print("Fetched OSM place elements (count unavailable)")
    if not args.use_sample:
        print(
            "Downloading Census TIGER place shapefile (attempting the requested year, falling back if needed)..."
        )
        census_gdf = None
        for y in range(args.year, 2019, -1):
            try:
                census_gdf = fetch_census_places(state_fips=args.state_fips, year=y)
                print(
                    f"Census TIGER places loaded (year {y}): {len(census_gdf)} features"
                )
                break
            except Exception as e:
                print(f"Failed to fetch Census TIGER places for {y}: {e}")
                census_gdf = None
    else:
        # In sample mode, we skip fetching Census TIGER data
        census_gdf = None

    if census_gdf is None:
        print(
            "No Census TIGER place shapefile could be fetched. Continuing with OSM points only."
        )
        if gpd is not None:
            census_gdf = gpd.GeoDataFrame(
                columns=["GEOID", "NAME", "geometry"],
                geometry="geometry",
                crs="EPSG:4326",
            )
        else:
            census_gdf = None
    if osm_gdf is not None:
        merge_and_export(osm_gdf, census_gdf, outdir)
    else:
        print("Sample mode created pre-built outputs; skipping merge/export step.")
    if args.pack_output:
        try:
            import zipfile

            zip_path = outdir.parent / f"nc_localities_output_{args.year}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(outdir):
                    for f in files:
                        file_path = Path(root) / f
                        zf.write(
                            file_path, arcname=str(file_path.relative_to(outdir.parent))
                        )
            print(f"Packaged output to {zip_path}")
        except Exception as e:
            print(f"Warning: failed to package output: {e}")


if __name__ == "__main__":
    main()
