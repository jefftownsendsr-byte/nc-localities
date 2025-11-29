import pytest
from pathlib import Path
import json

build = pytest.importorskip('scripts.build_nc_localities')


def test_merge_removes_duplicates(tmp_path: Path):
    gpd = pytest.importorskip('geopandas')
    from shapely.geometry import Point
    rows = [
        {
            'osm_id': 1,
            'osm_type': 'node',
            'name': 'Dup Place',
            'place': 'city',
            'population': '100',
            'tags': {},
            'geometry': Point(-79.0, 35.5),
        },
        {
            'osm_id': 2,
            'osm_type': 'node',
            'name': 'Dup Place',
            'place': 'city',
            'population': '50',
            'tags': {},
            'geometry': Point(-79.0, 35.5),
        }
    ]
    osm_gdf = gpd.GeoDataFrame(rows, geometry='geometry', crs='EPSG:4326')
    # census GDF empty
    census_gdf = gpd.GeoDataFrame(columns=['GEOID', 'NAME', 'geometry'], geometry='geometry', crs='EPSG:4326')
    outdir = tmp_path / 'output'
    outdir.mkdir()
    build.merge_and_export(osm_gdf, census_gdf, outdir)
    gj = json.loads((outdir / 'nc_localities.geojson').read_text(encoding='utf8'))
    # should dedupe into 1 feature
    assert len(gj['features']) == 1
