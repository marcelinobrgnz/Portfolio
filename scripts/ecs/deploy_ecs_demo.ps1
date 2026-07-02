# Deploy wine-quality API on ECS Fargate (eu-west-1) — ~1 hour demo
# Usage: .\deploy_ecs_demo.ps1
# No ALB (cheaper): public IP on task port 8000

$ErrorActionPreference = "Stop"

function Invoke-Aws {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
  $prev = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $out = & aws @Args 2>&1
  $code = $LASTEXITCODE
  $ErrorActionPreference = $prev
  if ($code -ne 0) { return @{ Ok = $false; Output = $out; Code = $code } }
  return @{ Ok = $true; Output = $out; Code = 0 }
}
$Region = "eu-west-1"
$AccountId = "864981752170"
$ClusterName = "portfolio-wine-demo"
$ServiceName = "wine-quality-api"
$Family = "portfolio-wine-api"
$EcrRepo = "portfolio-wine-api"
$GhcrImage = "ghcr.io/marcelinobrgnz/portfolio-wine-api:latest"
$EcrImage = "$AccountId.dkr.ecr.$Region.amazonaws.com/${EcrRepo}:latest"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\ecs"
$StateFile = "$ProofDir\ecs_state.json"

New-Item -ItemType Directory -Force -Path $ProofDir | Out-Null

function Save-State($obj) {
  $obj | ConvertTo-Json -Depth 6 | Set-Content $StateFile -Encoding UTF8
}

Write-Host "==> Ensuring ECS task execution role" -ForegroundColor Cyan
$roleName = "ecsTaskExecutionRole"
$roleCheck = Invoke-Aws iam get-role --role-name $roleName
if (-not $roleCheck.Ok) {
  Invoke-Aws iam create-role --role-name $roleName `
    --assume-role-policy-document "file://D:/IIMA/Portfolio/scripts/ecs/trust-policy.json" | Out-Null
  Invoke-Aws iam attach-role-policy --role-name $roleName `
    --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" | Out-Null
  Write-Host "Waiting for IAM role propagation..."
  Start-Sleep -Seconds 15
}
$ExecutionRoleArn = "arn:aws:iam::${AccountId}:role/${roleName}"

Write-Host "==> ECR repository + image copy from GHCR" -ForegroundColor Cyan
$ecrCheck = Invoke-Aws ecr describe-repositories --repository-names $EcrRepo --region $Region
if (-not $ecrCheck.Ok) {
  Invoke-Aws ecr create-repository --repository-name $EcrRepo --region $Region | Out-Null
}

$crane = "$env:TEMP\crane.exe"
if (-not (Test-Path $crane)) {
  Invoke-WebRequest -Uri "https://github.com/google/go-containerregistry/releases/download/v0.20.2/go-containerregistry_Windows_x86_64.tar.gz" `
    -OutFile "$env:TEMP\crane.tar.gz" -UseBasicParsing
  tar -xzf "$env:TEMP\crane.tar.gz" -C $env:TEMP crane.exe
}

$gh = "C:\Users\Marcelino\AppData\Local\Temp\gh-cli\bin\gh.exe"
$ghToken = & $gh auth token
$prevEa = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$ghToken | & $crane auth login ghcr.io -u marcelinobrgnz --password-stdin 2>&1 | Out-Null
aws ecr get-login-password --region $Region | & $crane auth login "$AccountId.dkr.ecr.$Region.amazonaws.com" -u AWS --password-stdin 2>&1 | Out-Null
$imageCheck = Invoke-Aws ecr describe-images --repository-name $EcrRepo --image-ids imageTag=latest --region $Region
if (-not $imageCheck.Ok) {
  Write-Host "Copying image from GHCR to ECR..."
  & $crane copy $GhcrImage $EcrImage 2>&1 | Out-Null
} else {
  Write-Host "ECR image :latest already present, skipping crane copy"
}
$ErrorActionPreference = $prevEa

Write-Host "==> Security group (allow 8000)" -ForegroundColor Cyan
$VpcId = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region $Region --query "Vpcs[0].VpcId" --output text
$SubnetId = aws ec2 describe-subnets --filters "Name=default-for-az,Values=true" "Name=vpc-id,Values=$VpcId" `
  --region $Region --query "Subnets[0].SubnetId" --output text
$sgCreate = Invoke-Aws ec2 create-security-group --group-name "portfolio-wine-api-demo-sg" `
  --description "1hr ECS demo wine API" --vpc-id $VpcId --region $Region
if ($sgCreate.Ok) {
  $SgId = ($sgCreate.Output | ConvertFrom-Json).GroupId
} else {
  $SgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=portfolio-wine-api-demo-sg" `
    --region $Region --query "SecurityGroups[0].GroupId" --output text
}
Invoke-Aws ec2 authorize-security-group-ingress --group-id $SgId --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $Region | Out-Null

Write-Host "==> CloudWatch log group" -ForegroundColor Cyan
$logCheck = Invoke-Aws logs describe-log-groups --log-group-name-prefix "/ecs/portfolio-wine-api" --region $Region
if (-not $logCheck.Ok) {
  Invoke-Aws logs create-log-group --log-group-name "/ecs/portfolio-wine-api" --region $Region | Out-Null
} else {
  $groups = ($logCheck.Output | ConvertFrom-Json).logGroups
  if (-not ($groups | Where-Object { $_.logGroupName -eq "/ecs/portfolio-wine-api" })) {
    Invoke-Aws logs create-log-group --log-group-name "/ecs/portfolio-wine-api" --region $Region | Out-Null
  }
}

Write-Host "==> ECS cluster + task definition" -ForegroundColor Cyan
Invoke-Aws ecs create-cluster --cluster-name $ClusterName --region $Region | Out-Null

$taskDefFile = "D:/IIMA/Portfolio/scripts/ecs/task-definition.json"
$TaskDefArn = aws ecs register-task-definition --cli-input-json "file://$taskDefFile" --region $Region `
  --query "taskDefinition.taskDefinitionArn" --output text
if (-not $TaskDefArn) { throw "Failed to register task definition" }

Write-Host "==> Run Fargate task (public IP)" -ForegroundColor Cyan
$TaskArn = aws ecs run-task --cluster $ClusterName --launch-type FARGATE `
  --task-definition $Family --region $Region `
  --network-configuration "awsvpcConfiguration={subnets=[$SubnetId],securityGroups=[$SgId],assignPublicIp=ENABLED}" `
  --query "tasks[0].taskArn" --output text
if (-not $TaskArn -or $TaskArn -eq "None") { throw "Failed to start ECS task" }

Write-Host "Waiting for task RUNNING..."
$attempts = 0
do {
  Start-Sleep -Seconds 15
  $attempts++
  $last = aws ecs describe-tasks --cluster $ClusterName --tasks $TaskArn --region $Region `
    --query "tasks[0].lastStatus" --output text
  Write-Host "  status: $last"
  if ($attempts -ge 40) { throw "Task did not reach RUNNING within timeout" }
} while ($last -ne "RUNNING")

Start-Sleep -Seconds 20
$EniId = aws ecs describe-tasks --cluster $ClusterName --tasks $TaskArn --region $Region `
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text
$PublicIp = aws ec2 describe-network-interfaces --network-interface-ids $EniId --region $Region `
  --query "NetworkInterfaces[0].Association.PublicIp" --output text
$ApiUrl = "http://${PublicIp}:8000"

Write-Host "API URL: $ApiUrl" -ForegroundColor Green

$deployedAt = (Get-Date).ToUniversalTime().ToString("o")
$teardownAt = (Get-Date).ToUniversalTime().AddHours(1).ToString("o")
Save-State @{
  region = $Region
  cluster = $ClusterName
  service = $ServiceName
  taskArn = $TaskArn
  taskDefinitionArn = $TaskDefArn
  securityGroupId = $SgId
  subnetId = $SubnetId
  publicIp = $PublicIp
  apiUrl = $ApiUrl
  ecrRepo = $EcrRepo
  deployedAtUtc = $deployedAt
  teardownScheduledAtUtc = $teardownAt
}

$deployedAt | Set-Content "$ProofDir\deployed_at.txt"
$ApiUrl | Set-Content "$ProofDir\api_url.txt"
@"
# ECS Fargate Demo Deployed
- **URL:** $ApiUrl
- **Health:** $ApiUrl/health
- **Region:** $Region
- **Deployed (UTC):** $deployedAt
- **Auto-teardown (UTC):** $teardownAt
"@ | Set-Content "$ProofDir\DEPLOYMENT.md"

Write-Host "==> Done. Run capture_ecs_proof.ps1 then schedule_teardown_1hour.ps1" -ForegroundColor Green
Write-Host "    Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File D:\IIMA\Portfolio\scripts\ecs\schedule_teardown_1hour.ps1' -WindowStyle Hidden" -ForegroundColor DarkGray
