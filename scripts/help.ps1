Write-Host "NC Localities Utility Scripts" -ForegroundColor Cyan
Write-Host "---------------------------------"
Write-Host "bootstrap_project.ps1 - Create project skeleton (run if folder is empty)"
Write-Host "scripts\run_all.ps1 - Run full pipeline locally; supports -UseDocker to run inside Docker container"
Write-Host "scripts\build_exe.ps1 - Build a Windows EXE using PyInstaller (may require conda)"
Write-Host "docker\run_in_container.ps1 - Build and run Docker image (Windows script)"
Write-Host "run_all.sh - Quick shell script for Linux/Mac to run pipeline"
