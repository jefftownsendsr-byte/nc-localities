param(
    [string]$RepoName = "nc-localities",
    [string]$OutputDir = "./output",
    [int]$Year = 2025
)

$ErrorActionPreference = 'Stop'

Write-Host "Running full setup + build + publish (one-shot)." -ForegroundColor Cyan

# Bootstrap if needed
if (-not (Test-Path .\scripts\build_nc_localities.py)) {
    Write-Host "No pipeline script found; running bootstrap to create files..." -ForegroundColor Yellow
    .\bootstrap_project.ps1
}

# Build the pipeline with Docker if available
if (Get-Command docker -ErrorAction SilentlyContinue) {
  Write-Host "Docker found; running pipeline inside Docker for consistency..." -ForegroundColor Green
  .\scripts\run_all.ps1 -UseDocker -OutputDir $OutputDir -Year $Year
} else {
  Write-Host "Docker not found; running pipeline locally. This may require conda or a working Python environment." -ForegroundColor Yellow
  .\scripts\run_all.ps1 -OutputDir $OutputDir -Year $Year
}

# Copy data into site
python .\scripts\build_site.py --output-dir $OutputDir --year $Year

# Run the publish script (gh or GitHub Desktop step)
if (Get-Command git -ErrorAction SilentlyContinue) {
  Write-Host "Attempting to publish to GitHub with minimal interaction..." -ForegroundColor Green
  .\scripts\publish.ps1 -RepoName $RepoName -Visibility public
} else {
  Write-Host "Git not found on this machine; please install Git or use GitHub Desktop to publish the repository manually." -ForegroundColor Red
}

Write-Host "Auto setup & publish attempted. Please check GitHub or GitHub Desktop to confirm publishing and view Actions." -ForegroundColor Green
