param(
    [switch]$RemoveVenv,
    [switch]$RemoveOutput
)

$ErrorActionPreference = 'Stop'

Write-Host "Cleaning project artifacts: output/, site/data/, __pycache__..." -ForegroundColor Cyan

# Remove output
if (Test-Path .\output -and $RemoveOutput) {
    Write-Host "Removing output/" -ForegroundColor Yellow
    Remove-Item -Recurse -Force -Path .\output
}

# Remove site data
if (Test-Path .\site\data) {
    Write-Host "Removing site/data/" -ForegroundColor Yellow
    Remove-Item -Recurse -Force -Path .\site\data
}

# Remove site map
if (Test-Path .\site\map.html) {
    Remove-Item -Force .\site\map.html
}

# Remove venv
if (Test-Path .\venv -and $RemoveVenv) {
    Write-Host "Removing venv/" -ForegroundColor Yellow
    Remove-Item -Recurse -Force -Path .\venv
}

# Clean python caches
Write-Host "Removing __pycache__ and compiled files..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Force -Include '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Force -Include '*.pyc' | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Done cleaning." -ForegroundColor Green
