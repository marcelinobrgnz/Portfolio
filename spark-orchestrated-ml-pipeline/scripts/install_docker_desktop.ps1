# Install Docker Desktop for Project 2 Airflow + Spark demo
# Run this script in an elevated PowerShell (Run as Administrator)

$ErrorActionPreference = "Stop"
$installer = "$env:TEMP\DockerDesktopInstaller.exe"
$url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"

Write-Host "==> Downloading Docker Desktop (~500 MB)..."
Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing

Write-Host "==> Installing Docker Desktop (requires admin, may prompt for reboot)..."
Write-Host "    After install: enable WSL2 if prompted, reboot, then run:"
Write-Host "    cd D:\IIMA\spark-orchestrated-ml-pipeline"
Write-Host "    docker compose up --build -d"
Write-Host ""

Start-Process -FilePath $installer -ArgumentList "install", "--quiet", "--accept-license" -Wait -Verb RunAs

Write-Host "==> Done. Reboot if prompted, then verify with: docker --version"
