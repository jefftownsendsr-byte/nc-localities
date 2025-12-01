param(
    [string]$ImageName = "nc-localities:latest",
    [string]$OutputDir = "$PWD\output",
    [int]$HostPort = 8000
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir '..')

Write-Host "Building Docker image: $ImageName" -ForegroundColor Cyan
docker build -t $ImageName $repoRoot

# Create host output folder if not exists
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }
# Resolve absolute path
$absOutput = (Resolve-Path $OutputDir).Path
Write-Host "Running Docker container (output -> $absOutput)" -ForegroundColor Cyan
# Run, map output, and publish port for serving if needed
$vol = $absOutput + ':/workspace/output'
$port = $HostPort + ':8000'
docker run --rm -v $vol -p $port $ImageName

Write-Host "Container finished. Check $absOutput" -ForegroundColor Green
