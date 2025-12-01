# Developer Setup & Quick Guide

This project provides a small pipeline and site generator. These steps get you up and running quickly for development.

Prerequisites (recommended):

- Git (for pre-commit and version control)
- Python 3.11+ (if using venv/pip)
- Conda/Mamba (optional, recommended for full builds with geospatial packages)
- Docker (optional, for reproducible containerized builds)

Quick dev setup (recommended for beginners):

1. Create a virtual environment:

```powershell
python -m venv .\venv
. .\venv\Scripts\Activate
```
2. Install dev dependencies & pre-commit *and* hooks:

```powershell
# Install packages listed in requirements-dev.txt
python -m pip install -r requirements-dev.txt
# Hooks are installed by setup_dev.ps1
.\scripts\setup_dev.ps1
# Run ruff and black locally (optional):
ruff check .
black --check .
```

3. Run the fast demo (sample-mode, minimal dependencies):

```powershell
.\scripts\dev.ps1 -UseSample
# Serve the site and visit http://localhost:8000
```

On macOS/Linux, use the helper shell script:

```bash
./scripts/setup_dev.sh --full   # or without --full for venv dev only
```

Full build (requires conda for geopackages on Windows):

```powershell
conda env create -n nc-localities -f environment.yml
conda activate nc-localities
python .\scripts\build_nc_localities.py --output-dir .\output --year 2025 --non-interactive --pack-output
python .\scripts\build_site.py --output-dir .\output --site-dir .\site
```

Docker-based full run (recommended on Windows if you don't want to manage conda install):

```powershell
.\scripts\run_in_docker.ps1
```

Running tests:

```powershell
# (venv)
python -m pip install -r requirements-dev.txt
pytest -q
```

Pre-commit:

- `setup_dev.ps1` installs the hooks if this repo is a git repo and runs `pre-commit run --all-files` once.
- Fix issues shown by pre-commit and commit changes; hooks will prevent bad commits.

Windows note:
- If you're on Windows, installing geospatial dependencies via pip often fails because of GDAL/Fiona binary build requirements.
- For best results, install `conda`/`mamba` and run: `conda env create -n nc-localities -f environment.yml` to get a working environment.
- The helper `scripts/setup_dev.ps1 -Full` will prefer `mamba` if available and create/update the `nc-localities` environment.
 - Use `scripts/check_env.ps1` to validate your environment and see a short set of recommended commands.

Notes:
- Use `--use-sample` when iterating quickly.
- Use `conda` or Docker for reproducible builds when verifying full pipeline correctness.
