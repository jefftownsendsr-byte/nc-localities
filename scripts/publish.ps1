param(
  [string]$RepoName = "nc-localities",
  [string]$Visibility = "public",
  [string]$Remote = "origin"
)

$ErrorActionPreference = 'Stop'

Write-Host "Preparing to publish repository to GitHub (or instruct GitHub Desktop)." -ForegroundColor Cyan

# Ensure git is initialized
if (-not (Test-Path .git)) {
  Write-Host "Initializing git repository..." -ForegroundColor Green
  git init
}

# Add and commit
Write-Host "Adding all files and committing..." -ForegroundColor Green
git add -A
$timestamp = (Get-Date).ToString('s')
try {
  git commit -m "Initial commit: NC Localities pipeline and site ($timestamp)"
} catch {
  Write-Host "No changes to commit or commit failed: $_" -ForegroundColor Yellow
}

# If gh available, create the repo and push
if (Get-Command gh -ErrorAction SilentlyContinue) {
  Write-Host "GitHub CLI (gh) found. Creating remote repo and pushing..." -ForegroundColor Green
  # Check if a remote origin already exists
  $existing = git remote | Select-String 'origin'
  if ($existing) {
    Write-Host "Remote 'origin' already exists; skipping creation." -ForegroundColor Yellow
  } else {
    # Create a GitHub repo and set remote
    gh repo create $RepoName --$Visibility --source=. --push
    Write-Host "Created repository $RepoName and pushed to GitHub." -ForegroundColor Green
  }
  Write-Host "If your repo is on GitHub now, it will trigger the workflows to build & deploy the site." -ForegroundColor Green
  # Try to enable Pages if gh is available
  try {
    & .\enable_pages.ps1 -Repo $RepoName
  } catch {
    Write-Host "Warning: enable Pages failed or gh not fully configured: $_" -ForegroundColor Yellow
  }
} else {
  # If gh isn't available, try to open GitHub Desktop for manual publish
  Write-Host "GitHub CLI (gh) not found. Attempting to open GitHub Desktop for manual publish..." -ForegroundColor Yellow
  # Common install locations for GitHub Desktop
  $possiblePaths = @(
    "$env:LOCALAPPDATA\GitHubDesktop\GitHubDesktop.exe",
    "$env:ProgramFiles\GitHub Desktop\GitHubDesktop.exe",
    "$env:ProgramFiles(x86)\GitHub Desktop\GitHubDesktop.exe"
  )
  $ghDesktopPath = $possiblePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($ghDesktopPath) {
    Write-Host "Opening GitHub Desktop..." -ForegroundColor Cyan
    Start-Process -FilePath $ghDesktopPath -ArgumentList (Resolve-Path .) -WindowStyle Normal
    Write-Host "GitHub Desktop opened. Please click 'Add Local Repository', choose this repo, then click 'Publish repository' and confirm your GitHub account." -ForegroundColor Cyan
  } else {
    Write-Host "GitHub Desktop not found on your machine. Please open GitHub Desktop and use 'Add Local Repository' to add and publish the repo manually." -ForegroundColor Yellow
    Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList (Resolve-Path .) -ErrorAction SilentlyContinue
  }
}

Write-Host "Publish script complete." -ForegroundColor Green
