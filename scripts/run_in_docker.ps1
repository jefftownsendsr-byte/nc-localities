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
$absOutput = (Resolve-Path $OutputDir).Path

docker run --rm -v "$absOutput:/workspace/output" -p $HostPort:8000 $ImageName
Write-Host "Running Docker container (output -> $absOutput)" -ForegroundColor Cyan
# Run, map output, and publish port for serving if needed
docker run --rm -v "$($absOutput):/workspace/output" -p $($HostPort):8000 $ImageName

Write-Host "Container finished. Check $absOutput" -ForegroundColor Green
