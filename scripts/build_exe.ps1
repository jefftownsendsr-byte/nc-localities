param(
    [string]$OutputDir = "./dist",
    [string]$ExeName = "nc_localities.exe",
    [switch]$UseConda
)

$ErrorActionPreference = 'Stop'
Write-Host "Building Windows EXE using PyInstaller (may require conda and binary libs for geopandas)" -ForegroundColor Cyan

# Ensure output dir exists
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force }

if ($UseConda -and (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "Using conda to create a build env and install dependencies..." -ForegroundColor Cyan
    conda create -y -n nc-build python=3.11
    conda activate nc-build
    conda install -y -c conda-forge pyinstaller geopandas requests osmnx folium
} else {
    # Use venv
    if (-not (Test-Path .\venv)) { python -m venv .\venv }
    . .\venv\Scripts\Activate
    python -m pip install --upgrade pip
    python -m pip install pyinstaller geopandas requests osmnx folium
}

# Run PyInstaller
$specArgs = "--onefile --name $ExeName scripts\build_nc_localities.py"
Write-Host "Running pyinstaller with args: $specArgs" -ForegroundColor Cyan
pyinstaller --onefile --name $ExeName scripts\build_nc_localities.py

# If build succeeds, the exe is in dist\
if (Test-Path "dist\$ExeName") {
    Copy-Item "dist\$ExeName" -Destination $OutputDir -Force
    Write-Host "EXE created at $OutputDir\$ExeName" -ForegroundColor Green
} else {
    Write-Host "EXE build failed or exe not found in dist\. Please check build logs." -ForegroundColor Red
}

Write-Host "NOTE: GeoPandas and other geopackages may require extra binaries (GDAL, Fiona, PROJ); using conda is recommended for a successful Windows EXE build." -ForegroundColor Yellow
