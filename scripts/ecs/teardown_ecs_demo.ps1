# Tear down all ECS demo resources. Safe to re-run.
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$ClusterName = "portfolio-wine-demo"
$StateFile = "D:\IIMA\Portfolio\demo-proof\ecs\ecs_state.json"

Write-Host "==> ECS teardown (eu-west-1)" -ForegroundColor Yellow

if (-not (Test-Path $StateFile)) {
  Write-Host "No state file - skipping teardown to avoid deleting unrelated resources."
  exit 0
}

$state = Get-Content $StateFile -Raw | ConvertFrom-Json
if (-not $state.taskArn) {
  Write-Host "State file has no taskArn - skipping."
  exit 0
}

if ($state.taskArn) {
  aws ecs stop-task --cluster $state.cluster --task $state.taskArn --region $Region 2>$null | Out-Null
  Write-Host "Stopped task $($state.taskArn)"
}
if ($state.securityGroupId) {
  Start-Sleep -Seconds 30
  aws ec2 delete-security-group --group-id $state.securityGroupId --region $Region 2>$null | Out-Null
  Write-Host "Deleted SG $($state.securityGroupId)"
}

aws ecs delete-cluster --cluster $ClusterName --region $Region 2>$null | Out-Null
Write-Host "Deleted cluster $ClusterName (if existed)"

$arns = aws ecs list-task-definitions --family-prefix portfolio-wine-api --region $Region `
  --query "taskDefinitionArns" --output text 2>$null
if ($arns) {
  $arns.Split() | ForEach-Object {
    aws ecs deregister-task-definition --task-definition $_ --region $Region 2>$null | Out-Null
  }
}

$teardownLog = @{
  tornDownAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  region = $Region
  cluster = $ClusterName
  status = "complete"
}
$teardownLog | ConvertTo-Json | Set-Content "D:\IIMA\Portfolio\demo-proof\ecs\teardown_log.json"
Rename-Item -Path $StateFile -NewName "ecs_state.torn_down.json" -Force -ErrorAction SilentlyContinue
Write-Host "Teardown complete." -ForegroundColor Green
