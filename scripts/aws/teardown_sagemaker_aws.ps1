# Tear down SageMaker + CodeBuild demo resources (preserve S3 artifacts)
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\sagemaker"
$EndpointName = "wine-quality-demo-ep"
$EndConfigName = "wine-quality-demo-cfg"
$ModelName = "wine-quality-demo"
$ProjectName = "portfolio-sagemaker-build"
$ImageRepo = "portfolio-wine-sagemaker"

Write-Host "==> SageMaker endpoint" -ForegroundColor Yellow
aws sagemaker delete-endpoint --endpoint-name $EndpointName --region $Region 2>$null
Start-Sleep -Seconds 30
aws sagemaker delete-endpoint-config --endpoint-config-name $EndConfigName --region $Region 2>$null
aws sagemaker delete-model --model-name $ModelName --region $Region 2>$null

Write-Host "==> ECR repository" -ForegroundColor Yellow
aws ecr delete-repository --repository-name $ImageRepo --region $Region --force 2>$null | Out-Null

Write-Host "==> CodeBuild project (optional keep for rebuilds)" -ForegroundColor Yellow
aws codebuild delete-project --name $ProjectName --region $Region 2>$null | Out-Null

@{
  tornDownAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  endpoint = $EndpointName
  codebuildProject = $ProjectName
  ecrRepo = $ImageRepo
  preserved = @("s3://mlops-inference-platform-864981752170/sagemaker/", "s3://mlops-inference-platform-864981752170/codebuild/")
} | ConvertTo-Json | Set-Content "$ProofDir\teardown_log.json" -Encoding UTF8

Write-Host "SageMaker AWS teardown complete." -ForegroundColor Green
