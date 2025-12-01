import json
from pathlib import Path
import pytest

# The merge_and_export function is defined in scripts/build_nc_localities.py
build = pytest.importorskip("scripts.build_nc_localities")


def make_osm_gdf(tmp_path):
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    # pandas is not required; we use geopandas to build gdf

    rows = [
        {
            "osm_id": 1,
            "osm_type": "node",
            "name": "Merge Test Place",
            "place": "city",
            "population": "100",
            "tags": {},
            "geometry": Point(-79.0, 35.5),
        }
    ]
    gdf = geopandas.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    return gdf


def make_census_gdf(tmp_path):
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    rows = [
        {
            "GEOID": "0001",
            "NAME": "Census Test Place",
            "geometry": Point(-79.0, 35.5),
        }
    ]
    gdf = geopandas.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    return gdf


def test_merge_and_export_produces_files(tmp_path: Path):
    outdir = tmp_path / "output"
    outdir.mkdir(parents=True)
    osm_gdf = make_osm_gdf(tmp_path)
    census_gdf = make_census_gdf(tmp_path)
    build.merge_and_export(osm_gdf, census_gdf, outdir)
    assert (outdir / "nc_localities.geojson").exists()
    assert (outdir / "nc_localities.csv").exists()
    assert (outdir / "nc_localities_shp" / "nc_localities.shp").exists()
    # Validate geojson content has FeatureCollection
    import json

    gj = json.loads((outdir / "nc_localities.geojson").read_text(encoding="utf8"))
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) >= 1
