param(
  [switch]$UseSample
)

# Convenience developer script: build sample outputs and serve site
Write-Host "Creating venv (if not present) and running in sample mode..." -ForegroundColor Cyan
if (-not (Test-Path .\venv)) { python -m venv .\venv }
. .\venv\Scripts\Activate
python -m pip install --upgrade pip
  if ($UseSample) {
    python -m pip install -q pytest
  } else {
    python -m pip install -r requirements.txt -q
  }

if ($UseSample) {
    # Quick dev (sample) then serve
    Write-Host "Running sample mode build and copy to site..." -ForegroundColor Green
    python .\scripts\build_nc_localities.py --output-dir .\output --use-sample
    python .\scripts\build_site.py --output-dir .\output --site-dir .\site
    Write-Host "Serving site on port 8000" -ForegroundColor Green
    Start-Process -FilePath python -ArgumentList "-m", "http.server", "8000", "--bind", "0.0.0.0", "-d", ".\site" -NoNewWindow
} else {
    Write-Host "Running full build (this may take time)..." -ForegroundColor Yellow
    python .\scripts\build_nc_localities.py --output-dir .\output --non-interactive --pack-output --year 2025
    python .\scripts\build_site.py --output-dir .\output --site-dir .\site
    Start-Process -FilePath python -ArgumentList "-m", "http.server", "8000", "--bind", "0.0.0.0", "-d", ".\site" -NoNewWindow
}
