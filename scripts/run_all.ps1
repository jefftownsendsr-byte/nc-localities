param(
    [string]$OutputDir = "./output",
    [int]$Year = 2025,
    [switch]$UseDocker,
    [switch]$UseSample
)

$ErrorActionPreference = 'Stop'
$usingConda = $false

Write-Host "Running NC localities pipeline (one-shot)." -ForegroundColor Cyan

# Auto-enable Docker usage if docker is installed and UseDocker not explicitly set; skip auto-enable if running in sample mode
if (-not $UseSample -and -not $UseDocker -and (Get-Command docker -ErrorAction SilentlyContinue)) { $UseDocker = $true }

if ($UseDocker) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker not found; please install Docker or run without --UseDocker'
    }
    # Ensure the Docker daemon is available (sometimes docker CLI exists but daemon isn't running)
    try {
        docker info > $null 2>&1
    } catch {
        throw 'Docker daemon not running; please start Docker Desktop or the Docker service and try again'
    }
    Write-Host 'Building Docker image and running pipeline inside container...' -ForegroundColor Cyan
        # Ensure the host output folder exists before passing it to Docker
        if (-not (Test-Path $OutputDir)) {
            Write-Host "Creating output directory: $OutputDir" -ForegroundColor Cyan
            New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
        }
        $resolvedPath = (Resolve-Path $OutputDir).Path
        # Resolve the path to the helper script relative to this script's location, not the current working directory
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $dockerScript = Join-Path $scriptDir '..\docker\run_in_container.ps1'
        $dockerScriptResolved = (Resolve-Path $dockerScript).Path
        & $dockerScriptResolved -OutputDir $resolvedPath -Year $Year
    return
}

# Prefer conda if available for geospatial deps, else fall back to venv + pip
if (Get-Command conda -ErrorAction SilentlyContinue) {
    Write-Host 'Conda found, creating environment using conda for reliable geospatial deps' -ForegroundColor Green
    # Create env YAML if not present
    if (-not (Test-Path .\environment.yml)) {
        Write-Host 'No environment.yml found; using pip with venv fallback' -ForegroundColor Yellow
    } else {
        $envExists = conda env list | Select-String 'nc-localities'
        if (-not $envExists) {
            Write-Host 'Creating conda env nc-localities' -ForegroundColor Cyan
            conda env create -n nc-localities -f .\environment.yml -y
        } else {
            Write-Host 'Conda env nc-localities exists; using it' -ForegroundColor Cyan
        }
    }
    $usingConda = $true
} else {
    Write-Host 'No conda detected; using virtualenv and pip' -ForegroundColor Green
    if (-not (Test-Path .\venv)) { python -m venv .\venv }
    . .\venv\Scripts\Activate
    python -m pip install --upgrade pip
    if (-not $UseSample) {
        python -m pip install -r requirements.txt
    } else {
        # For sample mode, we only need pytest for local tests and minimal tools
        python -m pip install pytest
    }
}

Write-Host 'Running build pipeline (OSM + TIGER + site copy) ...' -ForegroundColor Cyan
if ($usingConda) {
    if ($UseSample.IsPresent) { $sampleArg = '--use-sample' } else { $sampleArg = '' }
    conda run -n nc-localities python .\scripts\build_nc_localities.py --output-dir $OutputDir --year $Year --non-interactive --pack-output $sampleArg
    conda run -n nc-localities python .\scripts\build_site.py --output-dir $OutputDir --site-dir .\site
} else {
    if ($UseSample.IsPresent) { $sampleArg = '--use-sample' } else { $sampleArg = '' }
    python .\scripts\build_nc_localities.py --output-dir $OutputDir --year $Year --non-interactive --pack-output $sampleArg
    python .\scripts\build_site.py --output-dir $OutputDir --site-dir .\site
}
Write-Host "Pipeline complete. Output is in .\output and site data is in .\site\data" -ForegroundColor Green
