# Full AWS portfolio proof run: deploy → capture → tear down each service (minimize charges)
# Screenshots: browser captures URLs written to demo-proof/*/screenshot_urls.txt
$ErrorActionPreference = "Stop"
$Root = "D:\IIMA\Portfolio"
$ProofRoot = "$Root\demo-proof"
$RunLog = "$ProofRoot\aws_full_run_log.json"
$runStart = Get-Date
$phases = @()

function Add-Phase($name, $status, $detail) {
  $script:phases += @{
    phase = $name
    status = $status
    detail = $detail
    atUtc = (Get-Date).ToUniversalTime().ToString("o")
  }
}

Write-Host "========== AWS FULL PROOF RUN ==========" -ForegroundColor Magenta
Write-Host "Priority: capture proof → tear down immediately" -ForegroundColor Magenta

# --- 1. ECS P1 Wine API ---
try {
  Write-Host "`n[1/5] ECS Fargate — Wine API" -ForegroundColor Cyan
  & "$Root\scripts\ecs\deploy_ecs_demo.ps1"
  & "$Root\scripts\ecs\capture_ecs_proof.ps1"
  $ecsUrl = (Get-Content "$ProofRoot\ecs\api_url.txt" -Raw).Trim()
  @"
$ecsUrl/
$ecsUrl/docs
$ecsUrl/health
$ecsUrl/openapi.json
"@ | Set-Content "$ProofRoot\ecs\screenshot_urls.txt" -Encoding UTF8
  Add-Phase "ecs-p1" "CAPTURED" $ecsUrl
  & "$Root\scripts\ecs\teardown_ecs_demo.ps1"
  Add-Phase "ecs-p1-teardown" "DONE" "cluster/task/sg removed"
} catch {
  Add-Phase "ecs-p1" "FAILED" $_.Exception.Message
  & "$Root\scripts\ecs\teardown_ecs_demo.ps1" 2>$null
}

# --- 2. ECS Airflow ---
try {
  Write-Host "`n[2/5] ECS Fargate — Airflow UI" -ForegroundColor Cyan
  & "$Root\scripts\ecs\deploy_airflow_ecs.ps1"
  $afUrl = (Get-Content "$ProofRoot\ecs-airflow\airflow_url.txt" -Raw).Trim()
  @"
$afUrl/login/
$afUrl/home
$afUrl/dags/
$afUrl/dags/example_bash_operator/grid?tab=graph
"@ | Set-Content "$ProofRoot\ecs-airflow\screenshot_urls.txt" -Encoding UTF8
  Add-Phase "ecs-airflow" "CAPTURED" $afUrl
  & "$Root\scripts\ecs\teardown_airflow_ecs.ps1"
  Add-Phase "ecs-airflow-teardown" "DONE" ""
} catch {
  Add-Phase "ecs-airflow" "FAILED" $_.Exception.Message
  & "$Root\scripts\ecs\teardown_airflow_ecs.ps1" 2>$null
}

# --- 3. SageMaker ---
try {
  Write-Host "`n[3/5] SageMaker Real-Time Endpoint" -ForegroundColor Cyan
  & "$Root\scripts\aws\deploy_sagemaker_demo.ps1"
  Add-Phase "sagemaker" "CAPTURED" "wine-quality-demo-ep"
  & "$Root\scripts\aws\teardown_sagemaker.ps1"
  Add-Phase "sagemaker-teardown" "DONE" ""
} catch {
  Add-Phase "sagemaker" "FAILED" $_.Exception.Message
  & "$Root\scripts\aws\teardown_sagemaker.ps1" 2>$null
}

# --- 4. EMR Serverless ---
try {
  Write-Host "`n[4/5] EMR Serverless Spark" -ForegroundColor Cyan
  & "$Root\scripts\aws\deploy_emr_serverless_demo.ps1"
  Add-Phase "emr-serverless" "CAPTURED" "wine-etl-demo"
  & "$Root\scripts\aws\teardown_emr_serverless.ps1"
  Add-Phase "emr-teardown" "DONE" ""
} catch {
  Add-Phase "emr-serverless" "FAILED" $_.Exception.Message
  & "$Root\scripts\aws\teardown_emr_serverless.ps1" 2>$null
}

# --- 5. EKS (optional — slow) ---
try {
  Write-Host "`n[5/5] Amazon EKS" -ForegroundColor Cyan
  & "$Root\scripts\aws\deploy_eks_demo.ps1"
  $eksUrl = (Get-Content "$ProofRoot\eks\eks_state.json" | ConvertFrom-Json).apiUrl
  @"
$eksUrl/health
$eksUrl/docs
"@ | Set-Content "$ProofRoot\eks\screenshot_urls.txt" -Encoding UTF8
  Add-Phase "eks" "CAPTURED" $eksUrl
  & "$Root\scripts\aws\teardown_eks_demo.ps1"
  Add-Phase "eks-teardown" "DONE" ""
} catch {
  Add-Phase "eks" "FAILED" $_.Exception.Message
  & "$Root\scripts\aws\teardown_eks_demo.ps1" 2>$null
}

# --- Final cleanup ECR/logs from ECS if any remain ---
& "$Root\scripts\ecs\teardown_all_aws_demo.ps1" 2>$null

# --- Verify ---
& "$Root\scripts\aws\verify_teardown.ps1"

$summary = @{
  startedAtUtc = $runStart.ToUniversalTime().ToString("o")
  finishedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  durationMin = [math]::Round(((Get-Date) - $runStart).TotalMinutes, 1)
  phases = $phases
  mwaaNote = "MWAA skipped: requires private subnets + NAT gateway (~1 USD/day min). ECS Airflow used as AWS orchestration proof."
}
$summary | ConvertTo-Json -Depth 6 | Set-Content $RunLog -Encoding UTF8
Write-Host "`n========== RUN COMPLETE ==========" -ForegroundColor Green
$summary | ConvertTo-Json -Depth 6
