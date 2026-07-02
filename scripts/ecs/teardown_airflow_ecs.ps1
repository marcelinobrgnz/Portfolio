# Tear down ECS Airflow demo
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\ecs-airflow"
$ClusterName = "airflow-ui-demo-cluster"

if (Test-Path "$ProofDir\airflow_ecs_state.json") {
  $state = Get-Content "$ProofDir\airflow_ecs_state.json" | ConvertFrom-Json
  if ($state.taskArn) {
    aws ecs stop-task --cluster $ClusterName --task $state.taskArn --region $Region 2>$null | Out-Null
  }
  if ($state.securityGroupId) {
    aws ec2 delete-security-group --group-id $state.securityGroupId --region $Region 2>$null | Out-Null
  }
}

aws ecs delete-cluster --cluster $ClusterName --region $Region 2>$null | Out-Null
aws logs delete-log-group --log-group-name "/ecs/airflow-ui-demo" --region $Region 2>$null | Out-Null

@{
  tornDownAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  cluster = $ClusterName
} | ConvertTo-Json | Set-Content "$ProofDir\teardown_log.json" -Encoding UTF8

Write-Host "ECS Airflow teardown complete." -ForegroundColor Green
