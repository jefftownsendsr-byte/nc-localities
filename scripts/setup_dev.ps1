param(
    [string]$venvPath = '.\venv',
    [switch]$Full
)

# Sets up a developer environment: venv, installs required packages and pre-commit, and installs pre-commit hooks
Write-Host "Setting up developer environment..." -ForegroundColor Cyan

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating venv at $venvPath" -ForegroundColor Cyan
    python -m venv $venvPath
}

. $venvPath\Scripts\Activate
python -m pip install --upgrade pip
if ($Full) {
    Write-Host "Installing full runtime requirements (may be slow)" -ForegroundColor Yellow
    # Prefer conda/mamba for geospatial packages to avoid building GDAL/Fiona from source on Windows
    if (Get-Command mamba -ErrorAction SilentlyContinue) {
        Write-Host "Detected mamba; using mamba to create/update the conda environment from environment.yml" -ForegroundColor Cyan
        try {
            mamba env update --file environment.yml --name nc-localities --prune -y | Out-String | Write-Host
        } catch {
            # Try to create if update fails (e.g., environment missing)
            mamba env create --file environment.yml --name nc-localities -y | Out-String | Write-Host
        }
        Write-Host "To activate the environment: 'conda activate nc-localities' (or 'mamba activate nc-localities' if using micromamba)" -ForegroundColor Green
    } elseif (Get-Command conda -ErrorAction SilentlyContinue) {
        Write-Host "Detected conda; using conda to create/update the environment from environment.yml" -ForegroundColor Cyan
        try {
            conda env update --file environment.yml --name nc-localities --prune --yes | Out-String | Write-Host
        } catch {
            conda env create --file environment.yml --name nc-localities --yes | Out-String | Write-Host
        }
        Write-Host "To activate the environment: 'conda activate nc-localities'" -ForegroundColor Green
    } else {
        Write-Host "Conda/Mamba not found. Falling back to pip install. This may fail when building geospatial dependencies on Windows; we recommend installing conda/miniconda or using the Docker-based environment." -ForegroundColor Yellow
        python -m pip install -r requirements.txt
    }
} else {
    Write-Host "Installing dev requirements only (fast)" -ForegroundColor Cyan
    # Install dev dependencies
    if (Test-Path .\requirements-dev.txt) {
        python -m pip install -r .\requirements-dev.txt
    } else {
        python -m pip install pre-commit ruff black
    }
}
# Install pre-commit only if this is a git repo; give instructions otherwise
if (Get-Command git -ErrorAction SilentlyContinue) {
    if (Test-Path .git) {
        Write-Host "Detected git repository; installing pre-commit hooks..." -ForegroundColor Cyan
        pre-commit install
        Write-Host "Running pre-commit hooks once to fix issues automatically if possible..." -ForegroundColor Cyan
        try {
            pre-commit run --all-files
        } catch {
            Write-Host "pre-commit found issues. Please review and commit fixes, or run: pre-commit run --all-files --show-diff-on-failure" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "Git CLI found but this directory is not a git repository. Run 'git init' and re-run setup to install hooks." -ForegroundColor Yellow
    }
} else {
    Write-Host "Git CLI not found; skipping pre-commit hooks installation. Install git and re-run setup to enable hooks." -ForegroundColor Yellow
}

Write-Host "Developer environment ready. Run '.\scripts\run_tests.ps1' to run tests or '.\scripts\dev.ps1 -UseSample' to quickly preview the site." -ForegroundColor Green
