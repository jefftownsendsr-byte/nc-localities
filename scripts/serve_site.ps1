param([int]$port = 8000)

# Serve the site directory on the given port
Write-Host "Serving site/ at http://localhost:$port" -ForegroundColor Green
Start-Process -FilePath python -ArgumentList "-m", "http.server", "$port", "--bind", "0.0.0.0", "-d", ".\site" -NoNewWindow
Start-Sleep -Seconds 1
Start-Process "http://localhost:$port"
