import importlib
import json
from pathlib import Path

build_site = importlib.import_module("scripts.build_site")


def make_sample_geojson(path: Path):
    features = [
        {
            "type": "Feature",
            "properties": {"final_name": "Test Place", "place": "city"},
            "geometry": {"type": "Point", "coordinates": [-78.6382, 35.7796]},
        }
    ]
    gj = {"type": "FeatureCollection", "features": features}
    with open(path, "w", encoding="utf8") as fh:
        json.dump(gj, fh)


def test_build_site_copies_and_creates_map(tmp_path: Path):
    # Create temp output and site directories
    outdir = tmp_path / "output"
    outdir.mkdir()
    sdir = tmp_path / "site"
    sdir.mkdir()
    (sdir / "data").mkdir()

    gj_path = outdir / "nc_localities.geojson"
    csv_path = outdir / "nc_localities.csv"

    # Create minimal outputs
    make_sample_geojson(gj_path)
    with open(csv_path, "w", encoding="utf8") as fh:
        fh.write(
            "osm_id,final_name,place,geoid,x,y\n1,Test Place,city,,-78.6382,35.7796\n"
        )

    # Run the build_site copy function
    build_site.copy_data(outdir, sdir)

    # Validate files copied
    assert (sdir / "data" / "nc_localities.geojson").exists()
    assert (sdir / "data" / "nc_localities.csv").exists()

    # Create map (this should generate placeholder map.html if folium not present)
    build_site.create_map(sdir, gj_path)
    assert (sdir / "map.html").exists()


def test_pipeline_sample_mode(tmp_path: Path):
    import subprocess
    import sys

    outdir = tmp_path / "output"
    outdir.mkdir()
    sdir = tmp_path / "site"
    sdir.mkdir()
    # Run the pipeline in sample mode (no network/transitive deps required)
    res = subprocess.run(
        [
            sys.executable,
            "scripts/build_nc_localities.py",
            "--output-dir",
            str(outdir),
            "--use-sample",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert (outdir / "nc_localities.geojson").exists()
    assert (outdir / "nc_localities.csv").exists()
    # Run site build and validate
    res2 = subprocess.run(
        [
            sys.executable,
            "scripts/build_site.py",
            "--output-dir",
            str(outdir),
            "--site-dir",
            str(sdir),
        ],
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0
    assert (sdir / "data" / "nc_localities.geojson").exists()
    assert (sdir / "map.html").exists()
