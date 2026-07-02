# Minimal EKS demo - 1 node, deploy wine API via kubectl, tear down cluster after proof
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$AccountId = "864981752170"
$ClusterName = "portfolio-eks-demo"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\eks"
$NodeType = "t3.small"
$EcrRepo = "portfolio-wine-api"
$EcrImage = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${EcrRepo}:latest"

New-Item -ItemType Directory -Force -Path $ProofDir | Out-Null
$deployStart = Get-Date

$eksctlPath = "$env:USERPROFILE\.local\bin\eksctl.exe"
if (-not (Test-Path $eksctlPath)) {
  New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.local\bin" | Out-Null
  Invoke-WebRequest -Uri "https://github.com/eksctl-io/eksctl/releases/download/v0.194.0/eksctl_Windows_amd64.zip" `
    -OutFile "$env:TEMP\eksctl.zip" -UseBasicParsing
  Expand-Archive -Path "$env:TEMP\eksctl.zip" -DestinationPath "$env:TEMP\eksctl" -Force
  Copy-Item "$env:TEMP\eksctl\eksctl.exe" $eksctlPath -Force
}
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"

Write-Host "==> Creating EKS cluster (this takes ~15 min)..." -ForegroundColor Cyan
aws eks describe-cluster --name $ClusterName --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
  & $eksctlPath create cluster --name $ClusterName --region $Region --nodes 1 --node-type $NodeType `
    --node-volume-size 20 --timeout 25m 2>&1 | Tee-Object -FilePath "$ProofDir\eksctl_create.log"
} else {
  Write-Host "Cluster already exists, reusing."
}

aws eks update-kubeconfig --name $ClusterName --region $Region | Out-Null

$ecrCheck = aws ecr describe-images --repository-names $EcrRepo --image-ids imageTag=latest --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "ECR image missing - run ensure_ecr_image.ps1 first"
  exit 1
}

Write-Host "==> Applying k8s deployment" -ForegroundColor Cyan
$manifest = Get-Content "D:\IIMA\Portfolio\mlops-inference-platform\k8s\deployment-minikube.yaml" -Raw
$manifest = $manifest -replace "portfolio-wine-api:local", $EcrImage
$manifest = $manifest -replace "imagePullPolicy: Never", "imagePullPolicy: Always"
$manifestPath = "$ProofDir\deployment-eks.yaml"
$manifest | Set-Content $manifestPath -Encoding UTF8
kubectl apply -f $manifestPath 2>&1 | Tee-Object -FilePath "$ProofDir\kubectl_apply.log"

kubectl rollout status deployment/wine-quality-api --timeout=300s 2>&1 | Tee-Object -FilePath "$ProofDir\kubectl_rollout.log"

$nodePort = kubectl get svc wine-quality-api -o jsonpath="{.spec.ports[0].nodePort}" 2>$null
$nodeIp = kubectl get nodes -o jsonpath="{.items[0].status.addresses[?(@.type=='ExternalIP')].address}" 2>$null
if (-not $nodeIp) {
  $nodeIp = kubectl get nodes -o jsonpath="{.items[0].status.addresses[?(@.type=='InternalIP')].address}"
}
$ApiUrl = "http://${nodeIp}:${nodePort}"

kubectl get all -o wide 2>&1 | Set-Content "$ProofDir\kubectl_get_all.txt" -Encoding UTF8
aws eks describe-cluster --name $ClusterName --region $Region | Set-Content "$ProofDir\eks_cluster_describe.json" -Encoding UTF8

try {
  $health = Invoke-RestMethod "$ApiUrl/health" -TimeoutSec 30
  $health | ConvertTo-Json | Set-Content "$ProofDir\health_response.json" -Encoding UTF8
} catch {
  @{ error = $_.Exception.Message } | ConvertTo-Json | Set-Content "$ProofDir\health_response.json" -Encoding UTF8
}

@{
  service = "Amazon EKS"
  region = $Region
  clusterName = $ClusterName
  nodeType = $NodeType
  apiUrl = $ApiUrl
  nodePort = $nodePort
  deployDurationSec = [math]::Round(((Get-Date) - $deployStart).TotalSeconds, 1)
} | ConvertTo-Json | Set-Content "$ProofDir\eks_metrics.json" -Encoding UTF8

@{
  region = $Region
  clusterName = $ClusterName
  apiUrl = $ApiUrl
  deployedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content "$ProofDir\eks_state.json" -Encoding UTF8

Write-Host "EKS API URL: $ApiUrl"
