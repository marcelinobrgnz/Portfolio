# Full AWS demo teardown (ECS + optional ECR/log group). S3 bucket is preserved.
# Called automatically by schedule_teardown_1hour.ps1 after the 1-hour window.
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$EcrRepo = "portfolio-wine-api"
$LogGroup = "/ecs/portfolio-wine-api"

Write-Host "==> Full AWS demo teardown" -ForegroundColor Yellow
& "$PSScriptRoot\teardown_ecs_demo.ps1"

Write-Host "==> Deleting ECR repository images" -ForegroundColor Yellow
aws ecr delete-repository --repository-name $EcrRepo --force --region $Region 2>$null | Out-Null

Write-Host "==> Deleting CloudWatch log group" -ForegroundColor Yellow
aws logs delete-log-group --log-group-name $LogGroup --region $Region 2>$null | Out-Null

$log = @{
  tornDownAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  region = $Region
  preserved = @("s3://mlops-inference-platform-864981752170")
  removed = @("ecs cluster", "fargate task", "security group", "task definitions", "ecr repo", "log group")
}
$log | ConvertTo-Json | Set-Content "D:\IIMA\Portfolio\demo-proof\ecs\teardown_all_log.json"
Write-Host "Full teardown complete. S3 artifacts preserved." -ForegroundColor Green
