param()

Write-Host "Checking environment for nc-localities..." -ForegroundColor Cyan

# Python version
try {
    $pyver = python -c "import sys;print(sys.version)" 2>$null
    Write-Host "Python: $pyver"
} catch {
    Write-Host "Python not found or not on PATH" -ForegroundColor Yellow
}

# Conda/Mamba
if (Get-Command mamba -ErrorAction SilentlyContinue) {
    Write-Host "Mamba found" -ForegroundColor Green
} elseif (Get-Command conda -ErrorAction SilentlyContinue) {
    Write-Host "Conda found" -ForegroundColor Green
} else {
    Write-Host "Conda/Mamba not found. Recommended for geospatial packages; see DEV.md" -ForegroundColor Yellow
}

# Docker
if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        $ver = docker --version
        Write-Host "Docker: $ver" -ForegroundColor Green
    } catch {
        Write-Host "Docker found but 'docker --version' failed; ensure Docker Desktop is running" -ForegroundColor Yellow
    }
} else {
    Write-Host "Docker not found or not on PATH" -ForegroundColor Yellow
}

# Git
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "Git is installed" -ForegroundColor Green
} else {
    Write-Host "Git not found; install to ease development" -ForegroundColor Yellow
}

# Suggest fast setup paths
Write-Host "\nQuick recommendations:\n - Run `scripts/setup_dev.ps1 -Full` if you use conda/mamba (recommended on Windows).\n - Or use Docker: `scripts/run_in_docker.ps1` to build and run the full pipeline." -ForegroundColor Cyan
