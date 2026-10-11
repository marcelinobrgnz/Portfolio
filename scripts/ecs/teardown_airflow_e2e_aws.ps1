# Tear down Airflow E2E ECS demo
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\ecs-airflow"
$ClusterName = "airflow-e2e-demo-cluster"

if (Test-Path "$ProofDir\airflow_e2e_state.json") {
  $state = Get-Content "$ProofDir\airflow_e2e_state.json" | ConvertFrom-Json
  if ($state.taskArn) {
    aws ecs stop-task --cluster $ClusterName --task $state.taskArn --region $Region 2>$null | Out-Null
  }
}
$SgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=airflow-e2e-demo-sg" --region $Region --query "SecurityGroups[0].GroupId" --output text 2>$null
if ($SgId -and $SgId -ne "None") {
  aws ec2 delete-security-group --group-id $SgId --region $Region 2>$null | Out-Null
}
aws ecs delete-cluster --cluster $ClusterName --region $Region 2>$null | Out-Null
aws logs delete-log-group --log-group-name "/ecs/airflow-e2e-demo" --region $Region 2>$null | Out-Null
aws ecr delete-repository --repository-name portfolio-airflow-e2e --region $Region --force 2>$null | Out-Null
aws codebuild delete-project --name portfolio-airflow-e2e-build --region $Region 2>$null | Out-Null
Write-Host "Airflow E2E teardown complete." -ForegroundColor Green
