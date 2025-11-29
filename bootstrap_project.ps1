param(
    [string]$TargetDir = "C:\Users\Registered User\nc-localities"
)

# Ensure target dir exists
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}
Set-Location -Path $TargetDir

$files = @{}

# README
$files['README.md'] = @'
# North Carolina Localities (Updated to 2025)

This project contains a pipeline and static site to build a dataset of North Carolina localities updated to 2025.

See `scripts/run_all.ps1` to build everything.
'@

# requirements.txt
$files['requirements.txt'] = @'
geopandas
pandas
requests
osmnx
overpy
folium
shapely
fiona
pyproj
rasterio
tqdm
'@

# simple .gitignore
$files['.gitignore'] = @'
venv/
output/
*.zip
__pycache__/
.env
site/data/
'@

# Basic scripts folder
if (-not (Test-Path .\scripts)) { New-Item -ItemType Directory -Path .\scripts }

# Minimal build script to print placeholders
$files['scripts\build_nc_localities.py'] = @'
#!/usr/bin/env python
print("This is a placeholder build script for NC localities. Replace with the full pipeline from your development environment.")
'@

$files['scripts\run_all.ps1'] = @'
param()

Write-Host "This is a minimal run_all script placeholder. It will create a venv and install requirements. Replace with the full script for full pipeline behavior." -ForegroundColor Cyan

if (-not (Test-Path .\venv)) { python -m venv .\venv }
. .\venv\Scripts\Activate
python -m pip install -r requirements.txt
Write-Host "All done: venv created and dependencies installed. Next: replace scripts\build_nc_localities.py with the pipeline or run the full pipeline script." -ForegroundColor Green
'@

$files['scripts\build_site.py'] = @'
#!/usr/bin/env python
print("This is a minimal build_site script placeholder.")
'@

$files['scripts\serve_site.ps1'] = @'
param([int]$port = 8000)
Start-Process -FilePath python -ArgumentList "-m", "http.server", "$port", "-d", ".\site" -NoNewWindow
Start-Sleep -Seconds 1
Start-Process "http://localhost:$port"
'@

# Site skeleton
if (-not (Test-Path .\site)) { New-Item -ItemType Directory -Path .\site }
if (-not (Test-Path .\site\apps)) { New-Item -ItemType Directory -Path .\site\apps }
if (-not (Test-Path .\site\info)) { New-Item -ItemType Directory -Path .\site\info }
if (-not (Test-Path .\site\data)) { New-Item -ItemType Directory -Path .\site\data }

$files['site\index.html'] = @'
<!doctype html>
<html><body>
<h1>NC Localities</h1>
<p>Welcome — this is a minimal site skeleton. Replace with the full site contents.</p>
<ul>
<li><a href="map.html">Map</a></li>
<li><a href="apps/nearest.html">Apps</a></li>
</ul>
</body></html>
'@

$files['site\map.html'] = @'
<!doctype html>
<html><body>
<h1>Map placeholder</h1>
<p>Place `nc_localities.geojson` in `site/data/` to test the map.</p>
</body></html>
'@

$files['site\apps\nearest.html'] = @'
<!doctype html>
<html><body>
<h1>Nearest placeholder</h1>
</body></html>
'@

$files['site\info\about.html'] = @'
<!doctype html>
<html><body><h1>About</h1></body></html>
'@

# Create all files in target dir
foreach ($rel in $files.Keys) {
    $path = Join-Path $TargetDir $rel
    $dir = Split-Path $path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $content = $files[$rel]
    Set-Content -Path $path -Value $content -Force -Encoding UTF8
    Write-Host "Created: $rel"
}

Write-Host "Bootstrap complete. You can run `.\scripts\run_all.ps1` to install dependencies and start development." -ForegroundColor Green
