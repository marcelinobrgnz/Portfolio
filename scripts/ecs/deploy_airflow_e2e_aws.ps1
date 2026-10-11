# Airflow E2E on AWS: CodeBuild image -> ECS -> DAG trigger -> proof
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$AccountId = "864981752170"
$Bucket = "mlops-inference-platform-864981752170"
$ClusterName = "airflow-e2e-demo-cluster"
$Family = "airflow-e2e-demo"
$ImageRepo = "portfolio-airflow-e2e"
$ImageUri = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${ImageRepo}:latest"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\ecs-airflow"
$P2 = "D:\IIMA\Portfolio\spark-orchestrated-ml-pipeline"
$ProjectName = "portfolio-airflow-e2e-build"
$BuildRoleName = "PortfolioCodeBuildAirflowRole"

New-Item -ItemType Directory -Force -Path $ProofDir | Out-Null

Write-Host "==> ECR repo"
aws ecr describe-repositories --repository-names $ImageRepo --region $Region 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { aws ecr create-repository --repository-name $ImageRepo --region $Region | Out-Null }

Write-Host "==> CodeBuild source zip"
$stage = "$env:TEMP\airflow-e2e-src"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Copy-Item "D:\IIMA\Portfolio\scripts\ecs\Dockerfile.airflow-e2e" "$stage\Dockerfile"
Copy-Item "D:\IIMA\Portfolio\scripts\ecs\buildspec.airflow-e2e.yml" "$stage\buildspec.yml"
Copy-Item "$P2\dags\wine_feature_pipeline_dag.py" "$stage\"
Copy-Item "$P2\dags\taxi_etl_dag.py" "$stage\"
$zip = "$env:TEMP\airflow-e2e-src.zip"
Compress-Archive -Path "$stage\*" -DestinationPath $zip -Force
aws s3 cp $zip "s3://$Bucket/codebuild/airflow-e2e-src.zip" --region $Region

$cbTrust = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"codebuild.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
$cbTrust | Set-Content "$env:TEMP\cb-trust.json" -Encoding Ascii
aws iam get-role --role-name $BuildRoleName 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  aws iam create-role --role-name $BuildRoleName --assume-role-policy-document "file://$env:TEMP/cb-trust.json" | Out-Null
  aws iam attach-role-policy --role-name $BuildRoleName --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser | Out-Null
  aws iam attach-role-policy --role-name $BuildRoleName --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess | Out-Null
  aws iam attach-role-policy --role-name $BuildRoleName --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess | Out-Null
  Start-Sleep -Seconds 10
}
$BuildRoleArn = "arn:aws:iam::${AccountId}:role/${BuildRoleName}"

$proj = @{
  name = $ProjectName
  source = @{ type = "S3"; location = "$Bucket/codebuild/airflow-e2e-src.zip"; buildspec = "buildspec.yml" }
  artifacts = @{ type = "NO_ARTIFACTS" }
  environment = @{
    type = "LINUX_CONTAINER"; image = "aws/codebuild/standard:7.0"; computeType = "BUILD_GENERAL1_SMALL"; privilegedMode = $true
    environmentVariables = @(
      @{ name = "AWS_DEFAULT_REGION"; value = $Region; type = "PLAINTEXT" }
      @{ name = "AWS_ACCOUNT_ID"; value = $AccountId; type = "PLAINTEXT" }
      @{ name = "IMAGE_REPO_NAME"; value = $ImageRepo; type = "PLAINTEXT" }
      @{ name = "IMAGE_TAG"; value = "latest"; type = "PLAINTEXT" }
    )
  }
  serviceRole = $BuildRoleArn
} | ConvertTo-Json -Depth 6 -Compress
$pf = "$env:TEMP\cb-airflow.json"
[System.IO.File]::WriteAllText($pf, $proj, [System.Text.UTF8Encoding]::new($false))
aws codebuild batch-get-projects --names $ProjectName --region $Region --query "projects[0].name" --output text 2>$null | Out-Null
if ((aws codebuild batch-get-projects --names $ProjectName --region $Region --query "projects[0].name" --output text 2>$null) -eq $ProjectName) {
  aws codebuild update-project --cli-input-json "file://$($pf -replace '\\','/')" --region $Region | Out-Null
} else { aws codebuild create-project --cli-input-json "file://$($pf -replace '\\','/')" --region $Region | Out-Null }

Write-Host "==> CodeBuild"
$buildId = aws codebuild start-build --project-name $ProjectName --region $Region --query "build.id" --output text
do { Start-Sleep 20; $st = aws codebuild batch-get-builds --ids $buildId --region $Region --query "builds[0].buildStatus" --output text; Write-Host "  $st" } while ($st -eq "IN_PROGRESS")
if ($st -ne "SUCCEEDED") { throw "CodeBuild failed: $st" }

Write-Host "==> ECS deploy"
$VpcId = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region $Region --query "Vpcs[0].VpcId" --output text
$SubnetId = aws ec2 describe-subnets --filters "Name=default-for-az,Values=true" "Name=vpc-id,Values=$VpcId" --region $Region --query "Subnets[0].SubnetId" --output text
$sgCreate = aws ec2 create-security-group --group-name "airflow-e2e-demo-sg" --description "Airflow E2E" --vpc-id $VpcId --region $Region 2>&1
if ($LASTEXITCODE -eq 0) { $SgId = ($sgCreate | ConvertFrom-Json).GroupId } else {
  $SgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=airflow-e2e-demo-sg" --region $Region --query "SecurityGroups[0].GroupId" --output text
}
aws ec2 authorize-security-group-ingress --group-id $SgId --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region $Region 2>$null | Out-Null
aws logs create-log-group --log-group-name "/ecs/airflow-e2e-demo" --region $Region 2>$null | Out-Null
aws ecs create-cluster --cluster-name $ClusterName --region $Region 2>$null | Out-Null

$taskJson = @{
  family = $Family
  networkMode = "awsvpc"
  requiresCompatibilities = @("FARGATE")
  cpu = "1024"
  memory = "2048"
  executionRoleArn = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
  containerDefinitions = @(@{
    name = "airflow"
    image = $ImageUri
    essential = $true
    portMappings = @(@{ containerPort = 8080; hostPort = 8080; protocol = "tcp" })
    command = @("bash", "-lc", "airflow db migrate && airflow users create --username admin --password admin --firstname A --lastname U --role Admin --email a@b.com 2>/dev/null || true && exec airflow standalone")
    logConfiguration = @{
      logDriver = "awslogs"
      options = @{
        "awslogs-group" = "/ecs/airflow-e2e-demo"
        "awslogs-region" = $Region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  })
} | ConvertTo-Json -Depth 8 -Compress
$tf = "$env:TEMP\airflow-task.json"
[System.IO.File]::WriteAllText($tf, $taskJson, [System.Text.UTF8Encoding]::new($false))
aws ecs register-task-definition --cli-input-json "file://$($tf -replace '\\','/')" --region $Region | Out-Null

$TaskArn = aws ecs run-task --cluster $ClusterName --launch-type FARGATE --task-definition $Family --region $Region `
  --network-configuration "awsvpcConfiguration={subnets=[$SubnetId],securityGroups=[$SgId],assignPublicIp=ENABLED}" `
  --query "tasks[0].taskArn" --output text
do { Start-Sleep 20; $last = aws ecs describe-tasks --cluster $ClusterName --tasks $TaskArn --region $Region --query "tasks[0].lastStatus" --output text; Write-Host "  $last" } while ($last -ne "RUNNING")

$EniId = aws ecs describe-tasks --cluster $ClusterName --tasks $TaskArn --region $Region --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text
$PublicIp = aws ec2 describe-network-interfaces --network-interface-ids $EniId --region $Region --query "NetworkInterfaces[0].Association.PublicIp" --output text
$Base = "http://${PublicIp}:8080"
Write-Host "URL: $Base"

for ($i=0; $i -lt 36; $i++) {
  $code = curl.exe -s -m 10 -o NUL -w "%{http_code}" "$Base/health"
  if ($code -eq "200") { break }
  Start-Sleep 15
}

$token = (curl.exe -s -X POST "$Base/auth/token" -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin\"}" | ConvertFrom-Json).access_token
curl.exe -s -H "Authorization: Bearer $token" "$Base/api/v1/dags" | Set-Content "$ProofDir\dags_list_api.json" -Encoding UTF8
$ld = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
curl.exe -s -X POST -H "Authorization: Bearer $token" -H "Content-Type: application/json" "$Base/api/v1/dags/wine_feature_pipeline/dagRuns" -d "{\"logical_date\":\"$ld\"}" | Set-Content "$ProofDir\dag_run_trigger.json" -Encoding UTF8
Start-Sleep 20
curl.exe -s -H "Authorization: Bearer $token" "$Base/api/v1/dags/wine_feature_pipeline/dagRuns?limit=3" | Set-Content "$ProofDir\dag_runs_api.json" -Encoding UTF8

@{
  region = $Region; cluster = $ClusterName; taskArn = $TaskArn; publicIp = $PublicIp
  airflowUrl = $Base; imageUri = $ImageUri; buildId = $buildId
  deployedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content "$ProofDir\airflow_e2e_state.json" -Encoding UTF8

Write-Host "Airflow E2E AWS proof captured" -ForegroundColor Green
