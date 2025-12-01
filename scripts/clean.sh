#!/usr/bin/env bash
set -euo pipefail

remove_venv=false
remove_output=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --venv) remove_venv=true; shift;;
    --output) remove_output=true; shift;;
    -h|--help) echo "Usage: $0 [--venv] [--output]"; exit 0;;
    *) echo "Unknown arg $1"; exit 1;;
  esac
done

if [ "$remove_output" = true ]; then
  echo "Removing output/"
  rm -rf output
fi

if [ -d site/data ]; then
  echo "Removing site/data"
  rm -rf site/data
fi

if [ -f site/map.html ]; then
  rm -f site/map.html
fi

if [ "$remove_venv" = true ]; then
  echo "Removing venv"
  rm -rf .venv
fi

find . -name "__pycache__" -type d -prune -exec rm -rf {} +
find . -name "*.pyc" -type f -delete

echo "Clean completed"