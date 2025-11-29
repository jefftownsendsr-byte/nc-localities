# NC Localities (Windows)

This folder contains a pipeline and scripts to build an updated dataset of localities for North Carolina and a static website that displays the data.

Quick commands:

PowerShell:

```powershell
cd 'C:\Users\Registered User\nc-localities'
# Bootstrap and create files
.\bootstrap_project.ps1
```

```powershell
# Run the full pipeline using conda or pip/venv (UseDocker uses Docker image path)
.\scripts\run_all.ps1
# Or use Docker for reproducibility
.\scripts\run_all.ps1 -UseDocker
```

```powershell
# Serve the static site locally
.\scripts\serve_site.ps1
```

Docker (Linux / WSL / Docker Desktop):

```bash
# From repo root
docker build -t nc-localities .
mkdir -p output
docker run --rm -v "$(pwd)/output:/workspace/output" nc-localities:latest
```

Build a Windows EXE (may require conda for binary deps):

```powershell
# Build exe with conda
.\scripts\build_exe.ps1 -UseConda
```

Notes:

The script `scripts\build_nc_localities.py` is the main pipeline that queries OSM Overpass and downloads TIGER place shapefiles, merges them, deduplicates and exports GeoJSON/CSV/Shapefiles and an HTML map.

`site/` has the static website; generated `site/data/nc_localities.geojson` and `site/data/nc_localities.csv` are copied there by `scripts\build_site.py`.

If you want me to fully automate EXE builds or Docker image pushes (to a registry), I can add a CI workflow; let me know which of those you'd like me to configure next.

Licenses & Attribution

- Code: MIT (see `LICENSE`)
- OSM data: ODbL — attribution required: "© OpenStreetMap contributors"; share-alike for the database (see `LICENSES.md` / `ATTRIBUTION.md`)
- US Census TIGER/Line: public domain (no attribution required, though good practice to cite Census)

The site footer has been updated to include OpenStreetMap and Census attribution. If you distribute OSM-derived raw datasets, you must respect ODbL requirements.

Choosing a method:

- Docker: best if you don't want to install Python and geospatial libraries locally — Docker runs everything inside the container and produces outputs in the mounted `output` folder (recommended for consistency).
- Conda: best if you want to use local hardware and have the necessary drivers/binaries; conda usually handles binary geospatial dependencies (GDAL, proj, fiona) elegantly.
- PyInstaller EXE: best for non-technical end users who need a single `.exe` to run; building the EXE works best with conda-installed geospatial libs and may still require careful testing on target machines.

Beginner quick-run steps (venv / pip):

PowerShell (Windows):

```powershell
# Bootstrap and create files (one-time)
cd 'C:\Users\Registered User\nc-localities'
.\bootstrap_project.ps1
```

```powershell
# Create a venv and install minimal packages for sample mode
python -m venv .\venv
. .\venv\Scripts\Activate
python -m pip install --upgrade pip
python -m pip install pytest
```

Quick-start (sample mode - minimal dependencies; fastest):

```powershell
# Run sample mode - creates minimal outputs quickly without OSM/Census or GDAL
python .\scripts\build_nc_localities.py --output-dir .\output --use-sample
python .\scripts\build_site.py --output-dir .\output --site-dir .\site
# Or use the helper script (recommended)
.\scripts\dev.ps1 -UseSample
```

Developer setup (pre-commit and dev tooling):

```powershell
# Run this once to set up a quick developer environment (installs requirements and pre-commit hooks)
.\scripts\setup_dev.ps1
```

Note: `setup_dev.ps1` will install `pre-commit` hooks only if this folder is a git repository. If you haven't yet made this a git repo, run:

```powershell
git init
.\scripts\setup_dev.ps1
```

If you want to install the entire runtime (heavy geospatial dependencies) in the venv, run:

```powershell
.
\scripts\setup_dev.ps1 -Full
```

```powershell
# Full local build example (non-Docker)
python -m venv .\venv
. .\venv\Scripts\Activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Run the pipeline locally (non-Docker)
python .\scripts\build_nc_localities.py --output-dir .\output --year 2025
python .\scripts\build_site.py --output-dir .\output --site-dir .\site

# Serve the site locally
.\scripts\serve_site.ps1 -port 8000
```

Quick test run (PowerShell):

```powershell
.\scripts\run_tests.ps1
```

Quick dev mode (no network, fast):

```powershell
# Use sample mode to quickly create outputs without fetching OSM/TIGER
python .\scripts\build_nc_localities.py --output-dir .\output --use-sample
python .\scripts\build_site.py --output-dir .\output --site-dir .\site
```
