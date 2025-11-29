param(
  [string]$Repo = "",
  [string]$SourceBranch = "gh-pages"
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI (gh) not found. Install gh to automate Pages enabling.' }

# If repo not provided, get current repo from git remote
if (-not $Repo) {
  $remoteUrl = git config --get remote.origin.url
  if (-not $remoteUrl) { throw 'No remote origin set. Push the repo or set a remote first.' }
  # parse owner/repo from URL
  if ($remoteUrl -match "github.com[:/](.+?)/(.+)(\.git)?$") { $Repo = "$($matches[1])/$($matches[2])" }
}

Write-Host "Enabling Pages for repository $Repo with source branch $SourceBranch" -ForegroundColor Cyan

# Enable pages using gh api
$body = @{ "source" = @{ "branch" = $SourceBranch; "path" = "/" }; "public" = $true } | ConvertTo-Json -Depth 5

$resp = gh api --method PUT -H "Accept: application/vnd.github+json" /repos/$Repo/pages -f source.branch=$SourceBranch -f source.path='/'
Write-Host "Pages setup response: $resp" -ForegroundColor Green

Write-Host "GitHub Pages should be enabled; check https://$Repo.github.io for the site once the build completes." -ForegroundColor Green
