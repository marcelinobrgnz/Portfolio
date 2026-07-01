# Run this script in PowerShell AS ADMINISTRATOR
# Step 2: Docker + Step 3 prep (minikube)

$ErrorActionPreference = "Stop"

Write-Host "=== Step 2: Docker Desktop ===" -ForegroundColor Cyan
$installer = "$env:TEMP\DockerDesktopInstaller.exe"
if (-not (Test-Path $installer)) {
  Write-Host "Downloading Docker Desktop..."
  Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" `
    -OutFile $installer -UseBasicParsing
}
Write-Host "Installing Docker (approve UAC if prompted)..."
Start-Process -FilePath $installer -ArgumentList "install","--quiet","--accept-license" -Wait

Write-Host "`n=== REBOOT REQUIRED ===" -ForegroundColor Yellow
Write-Host "After reboot, open Docker Desktop and wait until it says 'Running'."
Write-Host "Then run: cd D:\IIMA\Portfolio\mlops-inference-platform && docker compose up --build -d"
Write-Host "And:    cd D:\IIMA\Portfolio\spark-orchestrated-ml-pipeline && docker compose up --build -d"

Write-Host "`n=== Step 3: minikube + kubectl (after Docker is running) ===" -ForegroundColor Cyan
$tools = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force -Path $tools | Out-Null

if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
  Invoke-WebRequest -Uri "https://storage.googleapis.com/minikube/releases/latest/minikube-windows-amd64.exe" `
    -OutFile "$tools\minikube.exe" -UseBasicParsing
}
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
  Invoke-WebRequest -Uri "https://dl.k8s.io/release/v1.31.0/bin/windows/amd64/kubectl.exe" `
    -OutFile "$tools\kubectl.exe" -UseBasicParsing
}
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$tools*") {
  [Environment]::SetEnvironmentVariable("Path", "$userPath;$tools", "User")
  $env:Path += ";$tools"
}

Write-Host "Tools installed to $tools"
Write-Host "After Docker is running, execute:"
Write-Host "  minikube start --driver=docker"
Write-Host "  cd D:\IIMA\Portfolio\mlops-inference-platform"
Write-Host "  python -m src.train --no-register"
Write-Host "  docker build --target api -t portfolio-wine-api:local ."
Write-Host "  minikube image load portfolio-wine-api:local"
Write-Host "  kubectl apply -f k8s/deployment.yaml"
Write-Host "  minikube service wine-quality-api --url"
