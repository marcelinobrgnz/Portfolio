# EMR Serverless Spark job — wine ETL demo (tear down app after job completes)
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$AccountId = "864981752170"
$Bucket = "mlops-inference-platform-864981752170"
$AppName = "portfolio-spark-demo"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\emr-serverless"
$RoleName = "EMRServerlessWineDemoRole"
$P2Root = "D:\IIMA\Portfolio\spark-orchestrated-ml-pipeline"

New-Item -ItemType Directory -Force -Path $ProofDir | Out-Null
$jobStart = Get-Date

Write-Host "==> EMR Serverless IAM role" -ForegroundColor Cyan
$trust = @{
  Version = "2012-10-17"
  Statement = @(@{
    Effect = "Allow"
    Principal = @{ Service = "emr-serverless.amazonaws.com" }
    Action = "sts:AssumeRole"
  })
} | ConvertTo-Json -Depth 5 -Compress
$trust | Set-Content "$env:TEMP\emr-trust.json" -Encoding ASCII
$roleCheck = aws iam get-role --role-name $RoleName 2>&1
if ($LASTEXITCODE -ne 0) {
  aws iam create-role --role-name $RoleName --assume-role-policy-document "file://$env:TEMP\emr-trust.json" | Out-Null
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess | Out-Null
  aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole | Out-Null
  Start-Sleep -Seconds 10
}
$RoleArn = "arn:aws:iam::${AccountId}:role/${RoleName}"

Write-Host "==> Upload Spark scripts to S3" -ForegroundColor Cyan
aws s3 sync "$P2Root\spark_jobs" "s3://$Bucket/emr-demo/spark_jobs/" --region $Region --exclude "__pycache__/*"
aws s3 cp "$P2Root\data\raw\wine\winequality-red.csv" "s3://$Bucket/emr-demo/input/wine/winequality-red.csv" --region $Region 2>$null
aws s3 cp "$P2Root\data\raw\wine\winequality-white.csv" "s3://$Bucket/emr-demo/input/wine/winequality-white.csv" --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
  aws s3 sync "$P2Root\tests\fixtures\wine" "s3://$Bucket/emr-demo/input/wine/" --region $Region
}

Write-Host "==> Create EMR Serverless application" -ForegroundColor Cyan
$appJson = aws emr-serverless create-application --name $AppName --release-label emr-7.0.0 --type SPARK --region $Region | ConvertFrom-Json
$AppId = $appJson.applicationId
Write-Host "ApplicationId: $AppId"

aws emr-serverless start-application --application-id $AppId --region $Region 2>$null | Out-Null

Write-Host "Waiting for application STARTED..."
$attempts = 0
do {
  Start-Sleep -Seconds 20
  $attempts++
  $app = aws emr-serverless get-application --application-id $AppId --region $Region | ConvertFrom-Json
  $state = $app.application.state
  Write-Host "  app state: $state"
  if ($attempts -ge 30) { throw "EMR app start timeout" }
} while ($state -ne "STARTED")

$entryPoint = "s3://$Bucket/emr-demo/spark_jobs/transform.py"
$outputPath = "s3://$Bucket/emr-demo/output/wine/"
$inputPath = "s3://$Bucket/emr-demo/input/wine/"

$jobRunJson = aws emr-serverless start-job-run --application-id $AppId --region $Region `
  --execution-role-arn $RoleArn `
  --name "wine-etl-demo" `
  --job-driver "{
    `"sparkSubmit`": {
      `"entryPoint`": `"$entryPoint`",
      `"entryPointArguments`": [`"--dataset`",`"wine`",`"--input`",`"$inputPath`",`"--output`",`"$outputPath`",`"--metrics-file`",`"$outputPath/_metrics.json`"],
      `"sparkSubmitParameters`": `"--conf spark.executor.cores=2 --conf spark.executor.memory=4g --conf spark.driver.cores=2 --conf spark.driver.memory=4g`"
    }
  }" | ConvertFrom-Json

$JobRunId = $jobRunJson.jobRunId
Write-Host "JobRunId: $JobRunId"

Write-Host "Waiting for job SUCCESS..."
$attempts = 0
do {
  Start-Sleep -Seconds 30
  $attempts++
  $job = aws emr-serverless get-job-run --application-id $AppId --job-run-id $JobRunId --region $Region | ConvertFrom-Json
  $jstate = $job.jobRun.state
  Write-Host "  job state: $jstate"
  if ($jstate -in @("SUCCESS", "FAILED", "CANCELLED")) { break }
  if ($attempts -ge 40) { throw "EMR job timeout" }
} while ($true)

$job | ConvertTo-Json -Depth 8 | Set-Content "$ProofDir\job_run_describe.json" -Encoding UTF8
aws s3 cp "s3://$Bucket/emr-demo/output/wine/_metrics.json" "$ProofDir\emr_wine_metrics.json" --region $Region 2>$null

$metrics = @{
  service = "EMR Serverless Spark"
  region = $Region
  applicationId = $AppId
  jobRunId = $JobRunId
  jobState = $jstate
  applicationState = $state
  jobDurationSec = [math]::Round(((Get-Date) - $jobStart).TotalSeconds, 1)
  inputPath = $inputPath
  outputPath = $outputPath
  releaseLabel = "emr-7.0.0"
}
$metrics | ConvertTo-Json | Set-Content "$ProofDir\emr_metrics.json" -Encoding UTF8

@{
  region = $Region
  applicationId = $AppId
  jobRunId = $JobRunId
  roleName = $RoleName
  deployedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content "$ProofDir\emr_state.json" -Encoding UTF8

if ($jstate -ne "SUCCESS") { Write-Warning "EMR job ended with state: $jstate" }
Write-Host "EMR Serverless job complete: $jstate" -ForegroundColor Green
