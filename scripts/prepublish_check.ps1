# Verify environment readiness before publish
$errors = @()

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $errors += 'Python not found' }
# Check for Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { $errors += 'Git not found' }
# Check for Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Write-Host 'Docker is not installed; Docker option will be unavailable' -ForegroundColor Yellow }
# Check for gh CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { Write-Host 'GitHub CLI (gh) not found; publishing will fall back to GitHub Desktop or manual' -ForegroundColor Yellow }

if ($errors.Count -gt 0) {
  Write-Host "Errors found: " -ForegroundColor Red
  $errors | ForEach-Object { Write-Host $_ }
  Write-Host "Please install missing components or run GitHub Desktop to publish manually." -ForegroundColor Yellow
} else {
  Write-Host "Environment checks passed: Python, Git found. Use Docker if available for a smoother run." -ForegroundColor Green
}
