param(
    [switch]$RunConda,
    [switch]$RunDocker
)

$ErrorActionPreference = 'Stop'

Write-Host "Running local CI checks" -ForegroundColor Cyan

# Basic lint checks
Write-Host "Running pre-commit hooks..." -ForegroundColor Cyan
pre-commit run --all-files || exit $LASTEXITCODE

Write-Host "Running unit tests (venv)..." -ForegroundColor Cyan
python -m pytest -q || exit $LASTEXITCODE

# Run the sample pipeline in venv
Write-Host "Running sample pipeline in venv..." -ForegroundColor Cyan
python .\scripts\build_nc_localities.py --output-dir .\output --use-sample || exit $LASTEXITCODE
python .\scripts\build_site.py --output-dir .\output --site-dir .\site || exit $LASTEXITCODE

if ($RunConda -and (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "Running tests in conda env (nc-localities) (if present)" -ForegroundColor Cyan
    conda run -n nc-localities pytest -q || Write-Host "Conda env tests failed or conda env not found" -ForegroundColor Yellow
}

if ($RunDocker -and (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Building and running Docker image for CI smoke test..." -ForegroundColor Cyan
    .\scripts\run_in_docker.ps1 || Write-Host "Docker run failed" -ForegroundColor Yellow
}

Write-Host "Local CI checks completed" -ForegroundColor Green
