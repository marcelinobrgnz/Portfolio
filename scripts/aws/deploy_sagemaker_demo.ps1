# Deploy SageMaker real-time endpoint (ml.t2.medium) — tear down immediately after proof
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$AccountId = "864981752170"
$Bucket = "mlops-inference-platform-864981752170"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\sagemaker"
$RoleName = "SageMakerWineDemoRole"
$ModelName = "wine-quality-demo"
$EndConfigName = "wine-quality-demo-cfg"
$EndpointName = "wine-quality-demo-ep"
$InstanceType = "ml.t2.medium"

New-Item -ItemType Directory -Force -Path $ProofDir | Out-Null
$deployStart = Get-Date

function Save-Proof($name, $obj) {
  if ($obj -is [string]) { $obj | Set-Content "$ProofDir\$name" -Encoding UTF8 }
  else { $obj | ConvertTo-Json -Depth 8 | Set-Content "$ProofDir\$name" -Encoding UTF8 }
}

Write-Host "==> SageMaker IAM role" -ForegroundColor Cyan
$trust = @{
  Version = "2012-10-17"
  Statement = @(@{
    Effect = "Allow"
    Principal = @{ Service = "sagemaker.amazonaws.com" }
    Action = "sts:AssumeRole"
  })
} | ConvertTo-Json -Depth 5 -Compress
$trust | Set-Content "$env:TEMP\sagemaker-trust.json" -Encoding ASCII
$roleCheck = aws iam get-role --role-name $RoleName 2>&1
if ($LASTEXITCODE -ne 0) {
  aws iam create-role --role-name $RoleName --assume-role-policy-document "file://$env:TEMP\sagemaker-trust.json" | Out-Null
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess | Out-Null
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess | Out-Null
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly | Out-Null
  Start-Sleep -Seconds 10
} else {
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly 2>$null | Out-Null
}
$RoleArn = "arn:aws:iam::${AccountId}:role/${RoleName}"

Write-Host "==> Package model artifact" -ForegroundColor Cyan
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

Write-Host "==> Create SageMaker model (sklearn DLC)" -ForegroundColor Cyan
$SklearnImage = "763104351884.dkr.ecr.${Region}.amazonaws.com/sklearn-inference:1.2-1-cpu-py3"
$ModelDataUrl = "s3://$Bucket/sagemaker/wine-sagemaker-model.tar.gz"
aws sagemaker delete-model --model-name $ModelName --region $Region 2>$null
$createModel = aws sagemaker create-model --model-name $ModelName --region $Region `
  --execution-role-arn $RoleArn `
  --primary-container "Image=$SklearnImage,ModelDataUrl=$ModelDataUrl,Environment={SAGEMAKER_PROGRAM=inference.py}" 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Warning "sklearn DLC model failed; falling back to BYOC image"
  Write-Host $createModel
  Write-Host "==> Build custom SageMaker image in ECR" -ForegroundColor Cyan
  $SgImage = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/portfolio-wine-sagemaker:latest"
  aws ecr describe-repositories --repository-names portfolio-wine-sagemaker --region $Region 2>$null
  if ($LASTEXITCODE -ne 0) { aws ecr create-repository --repository-name portfolio-wine-sagemaker --region $Region | Out-Null }
  aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "${AccountId}.dkr.ecr.${Region}.amazonaws.com" 2>$null
  aws ecr batch-delete-image --repository-name portfolio-wine-sagemaker --region $Region --image-ids imageTag=latest 2>$null | Out-Null
  docker buildx build --platform linux/amd64 --provenance=false --sbom=false `
    -f "D:\IIMA\Portfolio\scripts\sagemaker\Dockerfile.sagemaker" `
    -t $SgImage `
    --output "type=registry,oci-mediatypes=false" `
    "D:\IIMA\Portfolio"
  if ($LASTEXITCODE -ne 0) { throw "Docker buildx push failed" }
  aws sagemaker delete-model --model-name $ModelName --region $Region 2>$null
  aws sagemaker create-model --model-name $ModelName --region $Region `
    --execution-role-arn $RoleArn `
    --primary-container "Image=$SgImage" | Out-Null
}

Write-Host "==> Create endpoint config + endpoint ($InstanceType)" -ForegroundColor Cyan
aws sagemaker delete-endpoint-config --endpoint-config-name $EndConfigName --region $Region 2>$null
aws sagemaker create-endpoint-config --endpoint-config-name $EndConfigName --region $Region `
  --production-variants "VariantName=AllTraffic,ModelName=$ModelName,InitialInstanceCount=1,InstanceType=$InstanceType" | Out-Null

aws sagemaker delete-endpoint --endpoint-name $EndpointName --region $Region 2>$null
aws sagemaker create-endpoint --endpoint-name $EndpointName --endpoint-config-name $EndConfigName --region $Region | Out-Null

Write-Host "Waiting for endpoint InService (up to 20 min)..."
$attempts = 0
do {
  Start-Sleep -Seconds 30
  $attempts++
  $status = aws sagemaker describe-endpoint --endpoint-name $EndpointName --region $Region `
    --query "EndpointStatus" --output text
  Write-Host "  status: $status"
  if ($attempts -ge 50) { throw "SageMaker endpoint timeout" }
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
$invokeOut = aws sagemaker-runtime invoke-endpoint --endpoint-name $EndpointName --region $Region `
  --content-type "application/json" --body "file://$ProofDir\invoke_payload.json" `
  "$ProofDir\invoke_response.json" 2>&1
$sw.Stop()
Save-Proof "invoke_cli_output.txt" ($invokeOut | Out-String)

$metrics = @{
  service = "SageMaker Real-Time Inference"
  region = $Region
  endpointName = $EndpointName
  instanceType = $InstanceType
  endpointStatus = $status
  deployDurationSec = [math]::Round(((Get-Date) - $deployStart).TotalSeconds, 1)
  invokeLatencyMs = $sw.ElapsedMilliseconds
  creationTime = $describe.CreationTime
}
Save-Proof "sagemaker_metrics.json" $metrics

@{
  region = $Region
  roleName = $RoleName
  roleArn = $RoleArn
  modelName = $ModelName
  endpointConfigName = $EndConfigName
  endpointName = $EndpointName
  instanceType = $InstanceType
  deployedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content "$ProofDir\sagemaker_state.json" -Encoding UTF8

Write-Host "SageMaker endpoint ready: $EndpointName" -ForegroundColor Green
