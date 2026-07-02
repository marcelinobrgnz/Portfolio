# Deploy Airflow UI on ECS Fargate for portfolio screenshots
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$AccountId = "864981752170"
$ClusterName = "airflow-ui-demo-cluster"
$Family = "airflow-ui-demo"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\ecs-airflow"

New-Item -ItemType Directory -Force -Path $ProofDir | Out-Null

$roleName = "ecsTaskExecutionRole"
$roleCheck = aws iam get-role --role-name $roleName 2>&1
if ($LASTEXITCODE -ne 0) {
  aws iam create-role --role-name $roleName `
    --assume-role-policy-document "file://D:/IIMA/Portfolio/scripts/ecs/trust-policy.json" | Out-Null
  aws iam attach-role-policy --role-name $roleName `
    --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" | Out-Null
  Start-Sleep -Seconds 10
}

$VpcId = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region $Region --query "Vpcs[0].VpcId" --output text
$SubnetId = aws ec2 describe-subnets --filters "Name=default-for-az,Values=true" "Name=vpc-id,Values=$VpcId" `
  --region $Region --query "Subnets[0].SubnetId" --output text

$sgCreate = aws ec2 create-security-group --group-name "airflow-ui-demo-sg" `
  --description "Airflow ECS demo" --vpc-id $VpcId --region $Region 2>&1
if ($LASTEXITCODE -eq 0) {
  $SgId = ($sgCreate | ConvertFrom-Json).GroupId
} else {
  $SgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=airflow-ui-demo-sg" `
    --region $Region --query "SecurityGroups[0].GroupId" --output text
}
aws ec2 authorize-security-group-ingress --group-id $SgId --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region $Region 2>$null | Out-Null

aws logs create-log-group --log-group-name "/ecs/airflow-ui-demo" --region $Region 2>$null | Out-Null
aws ecs create-cluster --cluster-name $ClusterName --region $Region 2>$null | Out-Null

$TaskDefArn = aws ecs register-task-definition --cli-input-json "file://D:/IIMA/Portfolio/scripts/ecs/airflow-task-definition.json" --region $Region `
  --query "taskDefinition.taskDefinitionArn" --output text

$TaskArn = aws ecs run-task --cluster $ClusterName --launch-type FARGATE `
  --task-definition $Family --region $Region `
  --network-configuration "awsvpcConfiguration={subnets=[$SubnetId],securityGroups=[$SgId],assignPublicIp=ENABLED}" `
  --query "tasks[0].taskArn" --output text

Write-Host "Waiting for Airflow task RUNNING..."
$attempts = 0
do {
  Start-Sleep -Seconds 20
  $attempts++
  $last = aws ecs describe-tasks --cluster $ClusterName --tasks $TaskArn --region $Region `
    --query "tasks[0].lastStatus" --output text
  Write-Host "  status: $last"
  if ($attempts -ge 45) { throw "Airflow task timeout" }
} while ($last -ne "RUNNING")

Write-Host "Waiting for Airflow webserver (up to 8 min)..."
$EniId = aws ecs describe-tasks --cluster $ClusterName --tasks $TaskArn --region $Region `
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text
$PublicIp = aws ec2 describe-network-interfaces --network-interface-ids $EniId --region $Region `
  --query "NetworkInterfaces[0].Association.PublicIp" --output text
$AirflowUrl = "http://${PublicIp}:8080"

$ready = $false
for ($i = 0; $i -lt 24; $i++) {
  try {
    $code = curl.exe -s -m 10 -o NUL -w "%{http_code}" "$AirflowUrl/login/"
    if ($code -eq "200") { $ready = $true; break }
  } catch {}
  Write-Host "  UI not ready yet ($code)..."
  Start-Sleep -Seconds 20
}
if (-not $ready) { Write-Warning "Airflow UI may not be fully ready; URL: $AirflowUrl" }

@{
  region = $Region
  cluster = $ClusterName
  taskArn = $TaskArn
  securityGroupId = $SgId
  publicIp = $PublicIp
  airflowUrl = $AirflowUrl
  login = "admin/admin"
  deployedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content "$ProofDir\airflow_ecs_state.json" -Encoding UTF8

$AirflowUrl | Set-Content "$ProofDir\airflow_url.txt" -Encoding UTF8
Write-Host "Airflow URL: $AirflowUrl (admin/admin)" -ForegroundColor Green
