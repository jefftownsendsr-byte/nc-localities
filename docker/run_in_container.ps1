docker run --rm -v $vol $ImageName
param(
    [string]$OutputDir = "$PWD\output",
    [int]$Year = 2025,
    [string]$State = "North Carolina",
    [string]$StateFips = "37",
    [string]$ImageName = "nc-localities:latest"
)

$ErrorActionPreference = 'Stop'

# Determine script path and repo root (script is in docker\)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir '..')

# Resolve host output directory; create if missing
if (-not (Test-Path $OutputDir)) {
    Write-Host "Creating host output directory: $OutputDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}
$hostOutput = (Resolve-Path $OutputDir).Path

Write-Host "Building Docker image with context: $repoRoot" -ForegroundColor Cyan
docker build -t $ImageName $repoRoot

Write-Host "Running Docker container; mapping $hostOutput -> /workspace/output" -ForegroundColor Cyan
docker run --rm -v "$hostOutput:/workspace/output" $ImageName

Write-Host "Docker run completed. Check $hostOutput for outputs." -ForegroundColor Green
