# Delete EMR Serverless application
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\emr-serverless"
$AppName = "portfolio-spark-demo"

$AppId = $null
if (Test-Path "$ProofDir\emr_state.json") {
  $AppId = (Get-Content "$ProofDir\emr_state.json" | ConvertFrom-Json).applicationId
}
if (-not $AppId) {
  $apps = aws emr-serverless list-applications --region $Region --query "applications[?name=='$AppName'].id" --output text
  $AppId = $apps.Trim()
}

if ($AppId) {
  Write-Host "Stopping application $AppId..."
  aws emr-serverless stop-application --application-id $AppId --region $Region 2>$null
  Start-Sleep -Seconds 30
  Write-Host "Deleting application $AppId..."
  aws emr-serverless delete-application --application-id $AppId --region $Region 2>$null
}

@{
  tornDownAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  applicationId = $AppId
  preserved = @("s3://mlops-inference-platform-864981752170/emr-demo/")
} | ConvertTo-Json | Set-Content "$ProofDir\teardown_log.json" -Encoding UTF8

Write-Host "EMR Serverless teardown complete." -ForegroundColor Green
