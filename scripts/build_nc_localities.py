"""
Build North Carolina localities dataset: fetch OSM places via Overpass & Census TIGER places
Export GeoJSON, CSV, Shapefile, and an interactive map (folium)

Usage:
    python scripts/build_nc_localities.py --output-dir ./output --year 2025

"""

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

# Third-party imports
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    requests = None

try:
    import geopandas as gpd
except ImportError:
    gpd = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from shapely.geometry import Point
except ImportError:
    Point = None

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm is not installed
    def tqdm(iterable, **kwargs):
        return iterable


# Constants
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CENSUS_BASE = "https://www2.census.gov/geo/tiger/"

# User agent to avoid being blocked
HEADERS = {"User-Agent": "nc-localities/1.0 (+https://example.com)"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_requests_session():
    """Create a requests session with retry logic."""
    if requests is None:
        return None
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session


def load_mineral_localities_from_csv(csv_path: Path):
    """Load mineral locality data from CSV file."""
    logger.info(f"Loading mineral localities from {csv_path}")
    
    if not csv_path.exists():
        logger.error(f"Mineral localities CSV not found: {csv_path}")
        return None
    
    try:
        if pd is None:
            logger.error("pandas is required to read CSV files")
            return None
        if gpd is None or Point is None:
            logger.error("geopandas and shapely are required for spatial data")
            return None
            
        # Read CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} mineral localities from CSV")
        
        # Create Point geometries from lat/lon
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        
        # Rename columns to match expected format
        gdf['final_name'] = gdf['name']
        gdf['place'] = gdf['mineral_type']
        gdf['population'] = ''  # Not applicable for mineral sites
        gdf['osm_id'] = range(1, len(gdf) + 1)  # Generate IDs
        gdf['osm_type'] = 'mineral_site'
        gdf['geoid'] = ''
        
        return gdf
        
    except Exception as e:
        logger.error(f"Failed to load mineral localities from CSV: {e}")
        return None


def fetch_state_polygon(state_name="North Carolina"):
    session = get_requests_session()
    if session is None:
        raise ImportError("requests library is required for fetching data")

    params = {
        "q": state_name,
        "format": "jsonv2",
        "polygon_geojson": 1,
    }
    logger.info(f"Fetching state polygon for {state_name} from Nominatim...")
    try:
        resp = session.get(NOMINATIM_URL, params=params, timeout=60)
        resp.raise_for_status()
        items = resp.json()
    except requests.RequestException as e:
        logger.error(f"Network error fetching state polygon: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error fetching state polygon: {e}")
        raise

    if not items:
        raise RuntimeError(f"State polygon for {state_name} not found via Nominatim")
    
    for itm in items:
        if itm.get("osm_type") in ("relation", "way") and "geojson" in itm:
            return itm
    return items[0]


def polygon_to_overpass_poly(poly_geojson):
    coords = poly_geojson["coordinates"][0]
    return " ".join(f"{lat} {lon}" for lon, lat in coords)


def fetch_osm_places(polygon_str=None):
    session = get_requests_session()
    if session is None:
        raise ImportError("requests library is required for fetching data")

    # Use bounding box for North Carolina instead of complex polygon
    # NC bounding box: approximately 33.8°N to 36.6°N, -84.3°W to -75.4°W
    bbox = "33.8,-84.3,36.6,-75.4"  # south,west,north,east
    
    node_query = f'(node["place"]({bbox});way["place"]({bbox});relation["place"]({bbox}););out center tags;'
    payload = f"[out:json][timeout:300];{node_query}"

    logger.info("Querying Overpass API for places in NC bounding box...")
    try:
        resp = session.post(OVERPASS_URL, data=payload, timeout=600)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"Network error fetching OSM places: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error fetching OSM places: {e}")
        raise

    elements = data.get("elements", [])
    logger.info(f"Received {len(elements)} elements from Overpass.")
    
    rows = []
    for el in tqdm(elements, desc="Processing OSM elements"):
        el_type = el.get("type")
        tags = el.get("tags", {})
        name = tags.get("name")
        place = tags.get("place")
        population = tags.get("population")
        
        geom = None
        if el_type == "node":
            geom = Point(el.get("lon"), el.get("lat"))
        else:
            center = el.get("center")
            if center:
                geom = Point(center.get("lon"), center.get("lat"))
        
        if geom:
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

    if not rows:
        logger.warning("No valid places found in OSM data.")
        return gpd.GeoDataFrame(columns=["osm_id", "osm_type", "name", "place", "population", "tags", "geometry"], geometry="geometry", crs="EPSG:4326")

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    return gdf


def fetch_census_places(state_fips="37", year=2025):
    session = get_requests_session()
    if session is None:
        raise ImportError("requests library is required for fetching data")

    base = f"{CENSUS_BASE}TIGER{year}/PLACE/"
    filename = f"tl_{year}_{state_fips}_place.zip"
    url = base + filename
    
    logger.info(f"Downloading Census TIGER shapefile from {url}...")
    try:
        resp = session.get(url, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download census TIGER {year} place shapefile. Status: {resp.status_code}")
        
        total_size = int(resp.headers.get('content-length', 0))
        tmpdir = tempfile.mkdtemp()
        zpath = os.path.join(tmpdir, filename)
        
        with open(zpath, "wb") as fh:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading TIGER {year}") as pbar:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)
                    pbar.update(len(chunk))
                    
        logger.info("Reading shapefile...")
        gdf = gpd.read_file("zip://" + zpath)
        return gdf
    except requests.RequestException as e:
        logger.error(f"Network error downloading Census data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing Census data: {e}")
        raise


def merge_and_export(osm_gdf, census_gdf, output_dir: Path):
    # Wrap the two helpers to keep public API backward-compatible
    out_geo = prepare_out_geo(osm_gdf, census_gdf)
    write_exports_and_map(out_geo, output_dir)


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
        logger.info("Using sample data for quick local testing...")
        # If geopandas is available, construct a GeoDataFrame; otherwise write minimal output files directly.
        try:
            import geopandas as gpd_mod
            from shapely.geometry import Point as ShapelyPoint

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
            osm_gdf = gpd_mod.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
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
            logger.info("Wrote sample geojson & csv to output folder (no geopandas required)")
            # Create minimal in-memory placeholders so merge_and_export can proceed if needed
            osm_gdf = None
            census_gdf = None
    else:
        logger.info("Fetching state polygon from Nominatim...")
        try:
            state = fetch_state_polygon(args.state)
            poly_geojson = state["geojson"]
            poly_str = polygon_to_overpass_poly(poly_geojson)
            logger.info(
                "Querying Overpass for place nodes/ways/relations in the state polygon..."
            )
            osm_gdf = fetch_osm_places(poly_str)
        except Exception as e:
            logger.error(f"Failed to fetch OSM data: {e}")
            return None, None

    # If not sample mode, try fetching census
    if not args.use_sample:
        logger.info(
            "Downloading Census TIGER place shapefile (attempting the requested year, falling back if needed)..."
        )
        census_gdf = None
        for y in range(args.year, 2019, -1):
            try:
                census_gdf = fetch_census_places(state_fips=args.state_fips, year=y)
                logger.info(
                    f"Census TIGER places loaded (year {y}): {len(census_gdf)} features"
                )
                break
            except Exception as e:
                logger.warning(f"Failed to fetch Census TIGER places for {y}: {e}")
                census_gdf = None
    else:
        census_gdf = None

    if census_gdf is None and not args.use_sample:
        logger.warning(
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


def prepare_out_geo(osm_gdf, census_gdf):
    """Prepare final out_geo GeoDataFrame used for export and mapping."""
    if osm_gdf is None:
        return None
        
    logger.info("Preparing final output data...")
    if census_gdf is not None and not census_gdf.empty:
        census_gdf = census_gdf.to_crs("EPSG:4326")
        census_gdf = census_gdf[["GEOID", "NAME", "geometry"]].rename(
            columns={"NAME": "place_name", "GEOID": "geoid"}
        )
        osm_gdf = osm_gdf.to_crs("EPSG:4326")
        osm_gdf["name_norm"] = osm_gdf["name"].str.strip()
        joined = gpd.sjoin(osm_gdf, census_gdf, how="left", predicate="within")
        joined["final_name"] = joined["name_norm"].fillna(joined["place_name"])
    else:
        # Fallback if no census data
        joined = osm_gdf.copy()
        joined["final_name"] = joined["name"]
        joined["geoid"] = None

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
    return out_geo


def write_exports_and_map(out_geo, outdir: Path):
    if out_geo is None:
        logger.warning("No data to export.")
        return

    logger.info(f"Writing exports to {outdir}...")
    geojson_path = outdir / "nc_localities.geojson"
    csv_path = outdir / "nc_localities.csv"
    shp_dir = outdir / "nc_localities_shp"
    html_path = outdir / "nc_localities_map.html"
    
    out_geo.to_file(geojson_path, driver="GeoJSON")
    out_geo.drop(columns="geometry").to_csv(csv_path, index=False)
    shp_dir.mkdir(parents=True, exist_ok=True)
    out_geo.to_file(str(shp_dir / "nc_localities.shp"))
    
    try:
        import folium
    except ImportError:
        logger.warning("folium not installed; skipping HTML map")
        return

    center = [35.5, -79.0]
    m = folium.Map(location=center, zoom_start=7, tiles="OpenStreetMap")
    for _, row in out_geo.iterrows():
        coords = (row.geometry.y, row.geometry.x)
        popup_content = f"<b>{row.final_name}</b><br>Place: {row.place}<br>Population: {row.population}<br>OSM ID: {row.osm_id}"
        popup = folium.Popup(html=popup_content)
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
            logger.warning(f"Failed to copy map.html to site path: {e}")


def main(argv=None):
    # Entry point wrapper: parse args and run the pipeline
    args = parse_args(argv)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    try:
        osm_gdf, census_gdf = get_osm_and_census(args, outdir)
        # After this point, osm_gdf and census_gdf are set (or sample mode created outputs)
        if osm_gdf is not None:
            logger.info(f"Fetched {len(osm_gdf)} OSM place elements")
        
        # Load mineral localities from CSV
        mineral_csv_path = Path(__file__).resolve().parents[1] / "data" / "mineral_localities.csv"
        mineral_gdf = load_mineral_localities_from_csv(mineral_csv_path)
        
        # get_osm_and_census() already handles census_gdf fetching and fallbacks
        if osm_gdf is not None:
            out_geo = prepare_out_geo(osm_gdf, census_gdf)
            
            # Merge mineral localities if available
            if mineral_gdf is not None and not mineral_gdf.empty:
                logger.info(f"Merging {len(mineral_gdf)} mineral localities into dataset")
                # Select only the columns that match out_geo structure
                mineral_subset = mineral_gdf[["osm_id", "osm_type", "final_name", "place", "population", "geoid", "geometry"]]
                out_geo = pd.concat([out_geo, mineral_subset], ignore_index=True)
                logger.info(f"Total localities after merge: {len(out_geo)}")
            
            write_exports_and_map(out_geo, outdir)
        else:
            if args.use_sample:
                logger.info("Sample mode created pre-built outputs; skipping merge/export step.")
            else:
                logger.error("Failed to fetch OSM data. Pipeline aborted.")
                sys.exit(1)

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
                logger.info(f"Packaged output to {zip_path}")
            except Exception as e:
                logger.error(f"Failed to package output: {e}")
                
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
