# Finish optional AWS polish: EMR success + SageMaker endpoint, capture proof, tear down ASAP
$ErrorActionPreference = "Continue"
$Root = "D:\IIMA\Portfolio"
$LogDir = "$Root\demo-proof\aws-polish"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "========== AWS POLISH RUN (EMR + SageMaker) ==========" -ForegroundColor Magenta

# EMR in background
$emrJob = Start-Job -Name emr -ScriptBlock {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "D:\IIMA\Portfolio\scripts\aws\deploy_emr_serverless_demo.ps1"
}

# SageMaker in background
$sgJob = Start-Job -Name sagemaker -ScriptBlock {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "D:\IIMA\Portfolio\scripts\aws\deploy_sagemaker_demo.ps1"
}

Write-Host "Waiting for EMR + SageMaker (parallel)..."
Receive-Job -Job $emrJob -Wait -AutoRemoveJob | Set-Content "$LogDir\emr_deploy.log" -Encoding UTF8
Receive-Job -Job $sgJob -Wait -AutoRemoveJob | Set-Content "$LogDir\sagemaker_deploy.log" -Encoding UTF8

Write-Host "Tearing down immediately..."
& "$Root\scripts\aws\teardown_sagemaker.ps1" 2>&1 | Set-Content "$LogDir\sagemaker_teardown.log"
& "$Root\scripts\aws\teardown_emr_serverless.ps1" 2>&1 | Set-Content "$LogDir\emr_teardown.log"
aws ecr delete-repository --repository-name portfolio-wine-sagemaker --force --region eu-west-1 2>$null | Out-Null

& "$Root\scripts\aws\verify_teardown.ps1" 2>&1 | Set-Content "$LogDir\verify_teardown.log"

@{
  finishedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  emrMetrics = if (Test-Path "$Root\demo-proof\emr-serverless\emr_metrics.json") { Get-Content "$Root\demo-proof\emr-serverless\emr_metrics.json" | ConvertFrom-Json } else { $null }
  sagemakerMetrics = if (Test-Path "$Root\demo-proof\sagemaker\sagemaker_metrics.json") { Get-Content "$Root\demo-proof\sagemaker\sagemaker_metrics.json" | ConvertFrom-Json } else { $null }
} | ConvertTo-Json -Depth 6 | Set-Content "$LogDir\polish_run_summary.json" -Encoding UTF8

Write-Host "========== POLISH RUN COMPLETE ==========" -ForegroundColor Green
