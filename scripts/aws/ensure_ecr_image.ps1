# Populate ECR with wine API image (prerequisite for ECS + EKS)
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$AccountId = "864981752170"
$EcrRepo = "portfolio-wine-api"
$GhcrImage = "ghcr.io/marcelinobrgnz/portfolio-wine-api:latest"
$EcrImage = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${EcrRepo}:latest"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\ecr"
New-Item -ItemType Directory -Force -Path $ProofDir | Out-Null

$check = aws ecr describe-images --repository-names $EcrRepo --image-ids imageTag=latest --region $Region 2>$null
if ($LASTEXITCODE -eq 0) {
  Write-Host "ECR image already present"
  @{ status = "exists"; image = $EcrImage } | ConvertTo-Json | Set-Content "$ProofDir\ecr_status.json"
  exit 0
}

aws ecr describe-repositories --repository-names $EcrRepo --region $Region 2>$null
if ($LASTEXITCODE -ne 0) { aws ecr create-repository --repository-name $EcrRepo --region $Region | Out-Null }

$crane = "$env:TEMP\crane.exe"
if (-not (Test-Path $crane)) {
  Invoke-WebRequest -Uri "https://github.com/google/go-containerregistry/releases/download/v0.20.2/go-containerregistry_Windows_x86_64.tar.gz" `
    -OutFile "$env:TEMP\crane.tar.gz" -UseBasicParsing
  tar -xzf "$env:TEMP\crane.tar.gz" -C $env:TEMP crane.exe
}

aws ecr get-login-password --region $Region | & $crane auth login "${AccountId}.dkr.ecr.${Region}.amazonaws.com" -u AWS --password-stdin 2>$null
& $crane copy $GhcrImage $EcrImage 2>&1 | Tee-Object "$ProofDir\crane_copy.log"
if ($LASTEXITCODE -ne 0) {
  Write-Host "crane failed - docker build + push"
  docker build -f "D:\IIMA\Portfolio\mlops-inference-platform\Dockerfile.api" -t $EcrImage "D:\IIMA\Portfolio\mlops-inference-platform"
  if ($LASTEXITCODE -ne 0) { exit 1 }
  docker push $EcrImage
  if ($LASTEXITCODE -ne 0) { exit 1 }
}
@{ status = "pushed"; image = $EcrImage; atUtc = (Get-Date).ToUniversalTime().ToString("o") } | ConvertTo-Json | Set-Content "$ProofDir\ecr_status.json"
Write-Host "ECR ready: $EcrImage"
