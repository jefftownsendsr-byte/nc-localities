#!/usr/bin/env bash
set -euo pipefail

venv_path=".venv"
full=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -f|--full)
      full=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--full]"; exit 0
      ;;
    *)
      echo "Unknown arg: $1"; exit 1
      ;;
  esac
done

if [ "$full" = true ]; then
  if command -v mamba >/dev/null 2>&1; then
    echo "Detected mamba; creating/updating conda env..."
    mamba env update --file environment.yml --name nc-localities --prune -y || mamba env create --file environment.yml --name nc-localities -y
    echo "Installing dev requirements into conda env..."
    mamba run -n nc-localities python -m pip install -r requirements-dev.txt || true
    echo "Installing pre-commit hooks within conda env..."
    mamba run -n nc-localities python -m pip install pre-commit ruff black || true
    mamba run -n nc-localities pre-commit install || true
    mamba run -n nc-localities pre-commit run --all-files || true
  elif command -v conda >/dev/null 2>&1; then
    echo "Detected conda; creating/updating conda env..."
    conda env update --file environment.yml --name nc-localities --prune --yes || conda env create --file environment.yml --name nc-localities --yes
    echo "Installing dev requirements into conda env..."
    conda run -n nc-localities python -m pip install -r requirements-dev.txt || true
    echo "Installing pre-commit hooks within conda env..."
    conda run -n nc-localities python -m pip install pre-commit ruff black || true
    conda run -n nc-localities pre-commit install || true
    conda run -n nc-localities pre-commit run --all-files || true
  else
    echo "Conda or mamba is not installed; falling back to venv/pip install"
    $venv_path=.venv
    python -m venv "$venv_path"
    source "$venv_path/bin/activate"
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt || true
    python -m pip install -r requirements-dev.txt || true
    pre-commit install || true
    pre-commit run --all-files || true
  fi
else
  python -m venv "$venv_path"
  source "$venv_path/bin/activate"
  python -m pip install --upgrade pip
  python -m pip install -r requirements-dev.txt || true
  pre-commit install || true
  pre-commit run --all-files || true
fi

echo "Developer environment ready. Activate your conda env with: conda activate nc-localities"