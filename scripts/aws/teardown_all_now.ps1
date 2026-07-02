# Immediate full teardown of all AWS demo resources
$ErrorActionPreference = "Continue"
$Root = "D:\IIMA\Portfolio"
Write-Host "========== FULL TEARDOWN ==========" -ForegroundColor Red

& "$Root\scripts\ecs\teardown_ecs_demo.ps1"
& "$Root\scripts\ecs\teardown_airflow_ecs.ps1"
& "$Root\scripts\aws\teardown_sagemaker.ps1"
& "$Root\scripts\aws\teardown_emr_serverless.ps1"
& "$Root\scripts\aws\teardown_eks_demo.ps1"
& "$Root\scripts\ecs\teardown_all_aws_demo.ps1"

# Extra ECR repos from demos
aws ecr delete-repository --repository-name portfolio-wine-sagemaker --force --region eu-west-1 2>$null | Out-Null

& "$Root\scripts\aws\verify_teardown.ps1"

@{
  tornDownAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  note = "All demo compute torn down; S3 artifacts preserved"
} | ConvertTo-Json | Set-Content "$Root\demo-proof\aws-parallel\full_teardown_log.json" -Encoding UTF8

Write-Host "========== TEARDOWN COMPLETE ==========" -ForegroundColor Green
