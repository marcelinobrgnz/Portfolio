# Tear down SageMaker demo endpoint (preserve S3 model tarball)
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\sagemaker"
$EndpointName = "wine-quality-demo-ep"
$EndConfigName = "wine-quality-demo-cfg"
$ModelName = "wine-quality-demo"

Write-Host "==> Deleting SageMaker endpoint" -ForegroundColor Yellow
aws sagemaker delete-endpoint --endpoint-name $EndpointName --region $Region 2>$null
$attempts = 0
do {
  Start-Sleep -Seconds 15
  $attempts++
  $check = aws sagemaker describe-endpoint --endpoint-name $EndpointName --region $Region 2>&1
  if ($LASTEXITCODE -ne 0) { break }
  if ($attempts -ge 20) { break }
} while ($true)

aws sagemaker delete-endpoint-config --endpoint-config-name $EndConfigName --region $Region 2>$null
aws sagemaker delete-model --model-name $ModelName --region $Region 2>$null

@{
  tornDownAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  endpoint = $EndpointName
  preserved = @("s3://mlops-inference-platform-864981752170/sagemaker/")
} | ConvertTo-Json | Set-Content "$ProofDir\teardown_log.json" -Encoding UTF8

Write-Host "SageMaker teardown complete." -ForegroundColor Green
