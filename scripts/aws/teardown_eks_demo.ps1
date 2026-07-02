# Delete EKS cluster (all node groups + control plane)
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$ClusterName = "portfolio-eks-demo"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\eks"

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path

Write-Host "==> Deleting EKS cluster $ClusterName (may take ~10 min)..." -ForegroundColor Yellow
eksctl delete cluster --name $ClusterName --region $Region --wait 2>&1 | Tee-Object -FilePath "$ProofDir\eksctl_delete.log"

@{
  tornDownAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  clusterName = $ClusterName
} | ConvertTo-Json | Set-Content "$ProofDir\teardown_log.json" -Encoding UTF8

Write-Host "EKS teardown complete." -ForegroundColor Green
