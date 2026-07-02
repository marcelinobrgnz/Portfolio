# Deploy P1 wine API to local minikube (models baked into portfolio-wine-api:local).
$ErrorActionPreference = "Stop"
$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path

$root = "D:\IIMA\Portfolio\mlops-inference-platform"
$image = "portfolio-wine-api:local"

Write-Host "Starting minikube (if needed)..."
minikube start --driver=docker --cpus=2 --memory=2800

Write-Host "Building/loading image into minikube..."
if (-not (docker image inspect $image 2>$null)) {
  docker build -f "$root\Dockerfile.api" -t $image $root
}
minikube image load $image

Write-Host "Applying k8s manifest..."
kubectl apply -f "$root\k8s\deployment-minikube.yaml"

Write-Host "Waiting for deployment..."
kubectl rollout status deployment/wine-quality-api --timeout=180s

$url = minikube service wine-quality-api --url
Write-Host "Service URL: $url"
try {
  $health = Invoke-RestMethod "$url/health" -TimeoutSec 15
  $health | ConvertTo-Json -Compress
} catch {
  Write-Warning "Health check failed: $_"
}

Write-Host "Done. Swagger: $url/docs"
