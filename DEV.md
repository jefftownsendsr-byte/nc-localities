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

Full build (requires conda for geopackages on Windows):

```powershell
conda env create -n nc-localities -f environment.yml
conda activate nc-localities
python .\scripts\build_nc_localities.py --output-dir .\output --year 2025 --non-interactive --pack-output
python .\scripts\build_site.py --output-dir .\output --site-dir .\site
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

Notes:
- Use `--use-sample` when iterating quickly.
- Use `conda` or Docker for reproducible builds when verifying full pipeline correctness.
