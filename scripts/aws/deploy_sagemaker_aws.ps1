# SageMaker on AWS only: CodeBuild image -> endpoint -> invoke proof (no local Docker)
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$AccountId = "864981752170"
$Bucket = "mlops-inference-platform-864981752170"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\sagemaker"
$ProjectName = "portfolio-sagemaker-build"
$RoleName = "SageMakerWineDemoRole"
$BuildRoleName = "PortfolioCodeBuildSageMakerRole"
$ModelName = "wine-quality-demo"
$EndConfigName = "wine-quality-demo-cfg"
$EndPointName = "wine-quality-demo-ep"
$InstanceType = "ml.t2.medium"
$ImageRepo = "portfolio-wine-sagemaker"
$ImageTag = "latest"
$ImageUri = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${ImageRepo}:${ImageTag}"

New-Item -ItemType Directory -Force -Path $ProofDir | Out-Null
New-Item -ItemType Directory -Force -Path "D:\IIMA\Portfolio\demo-proof\aws-optional" | Out-Null
$deployStart = Get-Date
$logFile = "D:\IIMA\Portfolio\demo-proof\aws-optional\sagemaker_aws_deploy.log"

function Log($msg) {
  $line = "$(Get-Date -Format o) $msg"
  Write-Host $msg
  Add-Content -Path $logFile -Value $line -Encoding Ascii
}

function Save-Proof($name, $obj) {
  if ($obj -is [string]) { $obj | Set-Content "$ProofDir\$name" -Encoding UTF8 }
  else { $obj | ConvertTo-Json -Depth 8 | Set-Content "$ProofDir\$name" -Encoding UTF8 }
}

Log "==> SageMaker IAM execution role"
$trust = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"sagemaker.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
$trust | Set-Content "$env:TEMP\sagemaker-trust.json" -Encoding Ascii
aws iam get-role --role-name $RoleName 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  aws iam create-role --role-name $RoleName --assume-role-policy-document "file://$env:TEMP/sagemaker-trust.json" | Out-Null
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess | Out-Null
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess | Out-Null
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly | Out-Null
  Start-Sleep -Seconds 10
}
$RoleArn = "arn:aws:iam::${AccountId}:role/${RoleName}"

Log "==> Package model artifact to S3"
$pkgRoot = "$env:TEMP\sagemaker-model"
if (Test-Path $pkgRoot) { Remove-Item $pkgRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path "$pkgRoot\code" | Out-Null
Copy-Item "D:\IIMA\Portfolio\mlops-inference-platform\models\wine_quality_model.pkl" "$pkgRoot\"
Copy-Item "D:\IIMA\Portfolio\scripts\sagemaker\inference.py" "$pkgRoot\code\"
Copy-Item "D:\IIMA\Portfolio\scripts\sagemaker\requirements.txt" "$pkgRoot\code\"
$tarPath = "$env:TEMP\wine-sagemaker-model.tar.gz"
if (Test-Path $tarPath) { Remove-Item $tarPath -Force }
Push-Location $pkgRoot
tar -czf $tarPath wine_quality_model.pkl code
Pop-Location
aws s3 cp $tarPath "s3://$Bucket/sagemaker/wine-sagemaker-model.tar.gz" --region $Region

Log "==> CodeBuild IAM role"
$cbTrust = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"codebuild.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
$cbTrust | Set-Content "$env:TEMP\codebuild-trust.json" -Encoding Ascii
aws iam get-role --role-name $BuildRoleName 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  aws iam create-role --role-name $BuildRoleName --assume-role-policy-document "file://$env:TEMP/codebuild-trust.json" | Out-Null
  aws iam attach-role-policy --role-name $BuildRoleName --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser | Out-Null
  aws iam attach-role-policy --role-name $BuildRoleName --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess | Out-Null
  aws iam attach-role-policy --role-name $BuildRoleName --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess | Out-Null
  Start-Sleep -Seconds 10
} else {
  aws iam attach-role-policy --role-name $BuildRoleName --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser 2>$null | Out-Null
}
$BuildRoleArn = "arn:aws:iam::${AccountId}:role/${BuildRoleName}"

Log "==> Ensure ECR repository exists"
aws ecr describe-repositories --repository-names $ImageRepo --region $Region 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  aws ecr create-repository --repository-name $ImageRepo --region $Region | Out-Null
}

Log "==> Upload CodeBuild source to S3 (flat context)"
$srcZip = "$env:TEMP\sagemaker-codebuild-src.zip"
if (Test-Path $srcZip) { Remove-Item $srcZip -Force }
$stage = "$env:TEMP\sagemaker-src"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Copy-Item "D:\IIMA\Portfolio\scripts\sagemaker\Dockerfile.codebuild" "$stage\Dockerfile"
Copy-Item "D:\IIMA\Portfolio\scripts\sagemaker\buildspec.codebuild.yml" "$stage\buildspec.yml"
Copy-Item "D:\IIMA\Portfolio\scripts\sagemaker\serve.py" "$stage\"
Copy-Item "D:\IIMA\Portfolio\scripts\sagemaker\wsgi.py" "$stage\"
Copy-Item "D:\IIMA\Portfolio\mlops-inference-platform\models\wine_quality_model.pkl" "$stage\"
Compress-Archive -Path "$stage\*" -DestinationPath $srcZip -Force
aws s3 cp $srcZip "s3://$Bucket/codebuild/sagemaker-src.zip" --region $Region

Log "==> Create/update CodeBuild project"
$projectJson = @{
  name = $ProjectName
  source = @{
    type = "S3"
    location = "$Bucket/codebuild/sagemaker-src.zip"
    buildspec = "buildspec.yml"
  }
  artifacts = @{ type = "NO_ARTIFACTS" }
  environment = @{
    type = "LINUX_CONTAINER"
    image = "aws/codebuild/standard:7.0"
    computeType = "BUILD_GENERAL1_SMALL"
    privilegedMode = $true
    environmentVariables = @(
      @{ name = "AWS_DEFAULT_REGION"; value = $Region; type = "PLAINTEXT" }
      @{ name = "AWS_ACCOUNT_ID"; value = $AccountId; type = "PLAINTEXT" }
      @{ name = "IMAGE_REPO_NAME"; value = $ImageRepo; type = "PLAINTEXT" }
      @{ name = "IMAGE_TAG"; value = $ImageTag; type = "PLAINTEXT" }
    )
  }
  serviceRole = $BuildRoleArn
} | ConvertTo-Json -Depth 6 -Compress
$projectFile = "$env:TEMP\codebuild-project.json"
[System.IO.File]::WriteAllText($projectFile, $projectJson, [System.Text.UTF8Encoding]::new($false))

aws codebuild batch-get-projects --names $ProjectName --region $Region --query "projects[0].name" --output text 2>$null | Out-Null
if ($LASTEXITCODE -eq 0 -and (aws codebuild batch-get-projects --names $ProjectName --region $Region --query "projects[0].name" --output text) -eq $ProjectName) {
  aws codebuild update-project --cli-input-json "file://$($projectFile -replace '\\','/')" --region $Region | Out-Null
} else {
  aws codebuild create-project --cli-input-json "file://$($projectFile -replace '\\','/')" --region $Region | Out-Null
}

Log "==> Start CodeBuild (build + push BYOC image)"
$buildId = aws codebuild start-build --project-name $ProjectName --region $Region --query "build.id" --output text
Log "Build ID: $buildId"
do {
  Start-Sleep -Seconds 20
  $b = aws codebuild batch-get-builds --ids $buildId --region $Region --query "builds[0].{status:buildStatus,phase:currentPhase}" --output json | ConvertFrom-Json
  Log "  build: $($b.status) / $($b.phase)"
} while ($b.status -in @("IN_PROGRESS"))

if ($b.status -ne "SUCCEEDED") {
  aws codebuild batch-get-builds --ids $buildId --region $Region --query "builds[0].phases" --output json | Set-Content "$ProofDir\codebuild_phases.json" -Encoding UTF8
  throw "CodeBuild failed: $($b.status)"
}
Save-Proof "codebuild_build_id.txt" $buildId

Log "==> Create SageMaker model (BYOC)"
aws sagemaker delete-model --model-name $ModelName --region $Region 2>$null
aws sagemaker create-model --model-name $ModelName --region $Region `
  --execution-role-arn $RoleArn `
  --primary-container "Image=$ImageUri" | Out-Null

Log "==> Create endpoint ($InstanceType)"
aws sagemaker delete-endpoint-config --endpoint-config-name $EndConfigName --region $Region 2>$null
aws sagemaker create-endpoint-config --endpoint-config-name $EndConfigName --region $Region `
  --production-variants "VariantName=AllTraffic,ModelName=$ModelName,InitialInstanceCount=1,InstanceType=$InstanceType" | Out-Null
aws sagemaker delete-endpoint --endpoint-name $EndpointName --region $Region 2>$null
aws sagemaker create-endpoint --endpoint-name $EndpointName --endpoint-config-name $EndConfigName --region $Region | Out-Null

Log "Waiting for InService..."
$attempts = 0
do {
  Start-Sleep -Seconds 30
  $attempts++
  $status = aws sagemaker describe-endpoint --endpoint-name $EndpointName --region $Region --query "EndpointStatus" --output text
  Log "  endpoint: $status"
  if ($status -eq "Failed") {
    $reason = aws sagemaker describe-endpoint --endpoint-name $EndpointName --region $Region --query "FailureReason" --output text
    throw "Endpoint failed: $reason"
  }
  if ($attempts -ge 50) { throw "Endpoint timeout" }
} while ($status -ne "InService")

$describe = aws sagemaker describe-endpoint --endpoint-name $EndpointName --region $Region | ConvertFrom-Json
Save-Proof "endpoint_describe.json" $describe

$payload = @{
  instances = @(@{
    fixed_acidity = 7.4; volatile_acidity = 0.7; citric_acid = 0.0
    residual_sugar = 1.9; chlorides = 0.076; free_sulfur_dioxide = 11.0
    total_sulfur_dioxide = 34.0; density = 0.9978; pH = 3.51
    sulphates = 0.56; alcohol = 9.4; wine_type = 0
  })
} | ConvertTo-Json -Depth 4 -Compress
$payload | Set-Content "$ProofDir\invoke_payload.json" -Encoding UTF8

$sw = [System.Diagnostics.Stopwatch]::StartNew()
aws sagemaker-runtime invoke-endpoint --endpoint-name $EndpointName --region $Region `
  --content-type "application/json" --body "fileb://$($ProofDir -replace '\\','/')/invoke_payload.json" `
  "$ProofDir\invoke_response.json" | Out-Null
$sw.Stop()

$responseBody = Get-Content "$ProofDir\invoke_response.json" -Raw -Encoding UTF8
Save-Proof "sagemaker_metrics.json" @{
  service = "SageMaker Real-Time Inference"
  region = $Region
  endpointName = $EndpointName
  instanceType = $InstanceType
  imageUri = $ImageUri
  buildMethod = "AWS CodeBuild"
  buildId = $buildId
  endpointStatus = $status
  deployDurationSec = [math]::Round(((Get-Date) - $deployStart).TotalSeconds, 1)
  invokeLatencyMs = $sw.ElapsedMilliseconds
  prediction = ($responseBody | ConvertFrom-Json)
  capturedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
}

Save-Proof "sagemaker_state.json" @{
  region = $Region
  endpointName = $EndpointName
  imageUri = $ImageUri
  deployedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
}

Log "SageMaker SUCCESS: invoke captured" -ForegroundColor Green
