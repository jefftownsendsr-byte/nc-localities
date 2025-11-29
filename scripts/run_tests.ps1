param(
    [string]$venvPath = '.\venv'
)

# Create venv and install test dependencies
if (-not (Test-Path $venvPath)) { python -m venv $venvPath }
. $venvPath\Scripts\Activate
python -m pip install --upgrade pip
python -m pip install pytest
pytest -q
