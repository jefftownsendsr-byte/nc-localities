#!/usr/bin/env bash
set -euo pipefail

run_conda=false
run_docker=false

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --conda) run_conda=true; shift;;
    --docker) run_docker=true; shift;;
    -h|--help) echo "Usage: $0 [--conda] [--docker]"; exit 0;;
    *) echo "Unknown arg $1"; exit 1;;
  esac
done

echo "Running local CI checks"
pre-commit run --all-files || exit 1

python -m pytest -q || exit 1

# sample run
echo "Running sample pipeline in venv..."
python scripts/build_nc_localities.py --output-dir output --use-sample || exit 1
python scripts/build_site.py --output-dir output --site-dir site || exit 1

if [ "$run_conda" = true ]; then
  if command -v conda >/dev/null 2>&1; then
    echo "Running tests inside conda env (nc-localities)"
    conda run -n nc-localities python -m pytest -q || echo "Conda pytest failed"
  else
    echo "Conda not found; skipping conda run"
  fi
fi

if [ "$run_docker" = true ]; then
  if command -v docker >/dev/null 2>&1; then
    echo "Running Docker build and container run (ci smoke test)"
    ./scripts/run_in_docker.ps1
  else
    echo "Docker not found; skipping Docker run"
  fi
fi

echo "Local CI checks completed"
