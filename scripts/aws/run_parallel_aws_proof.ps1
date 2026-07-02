# Parallel AWS proof orchestrator — deploy tracks concurrently, capture, tear down ASAP
$ErrorActionPreference = "Continue"
$Root = "D:\IIMA\Portfolio"
$ProofRoot = "$Root\demo-proof"
$LogDir = "$ProofRoot\aws-parallel"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$jobs = @()

function Start-Track($name, $script) {
  Write-Host "Starting track: $name" -ForegroundColor Cyan
  $j = Start-Job -Name $name -ScriptBlock {
    param($s)
    & powershell -NoProfile -ExecutionPolicy Bypass -File $s 2>&1
  } -ArgumentList $script
  return @{ name = $name; job = $j; script = $script }
}

# Phase 1 — all independent tracks in parallel
$jobs += Start-Track "ecr" "$Root\scripts\aws\ensure_ecr_image.ps1"
$jobs += Start-Track "sagemaker" "$Root\scripts\aws\deploy_sagemaker_demo.ps1"
$jobs += Start-Track "emr" "$Root\scripts\aws\deploy_emr_serverless_demo.ps1"
$jobs += Start-Track "airflow-ecs" "$Root\scripts\ecs\deploy_airflow_ecs.ps1"
$jobs += Start-Track "eks" "$Root\scripts\aws\deploy_eks_demo.ps1"

Write-Host "Waiting for parallel deploy tracks..."
foreach ($t in $jobs) {
  $out = Receive-Job -Job $t.job -Wait -AutoRemoveJob
  $out | Set-Content "$LogDir\$($t.name)_deploy.log" -Encoding UTF8
  $state = if (($out | Out-String) -match "FAILED|throw|error") { "check log" } else { "done" }
  Write-Host "  $($t.name): $state" -ForegroundColor $(if ($state -eq "done") { "Green" } else { "Yellow" })
}

# Phase 2 — ECS P1 (needs ECR)
Write-Host "Starting ECS P1 (after ECR)..." -ForegroundColor Cyan
& "$Root\scripts\ecs\deploy_ecs_demo.ps1" 2>&1 | Set-Content "$LogDir\ecs-p1_deploy.log"

# Phase 3 — capture CLI metrics
Write-Host "Capturing metrics..." -ForegroundColor Cyan
if (Test-Path "$ProofRoot\ecs\api_url.txt") { & "$Root\scripts\ecs\capture_ecs_proof.ps1" 2>&1 | Set-Content "$LogDir\ecs-p1_capture.log" }

# Write screenshot URL manifest for browser capture
$urls = @()
if (Test-Path "$ProofRoot\ecs\api_url.txt") {
  $u = (Get-Content "$ProofRoot\ecs\api_url.txt" -Raw).Trim()
  $urls += "$u/docs", "$u/health", "$u/openapi.json"
}
if (Test-Path "$ProofRoot\ecs-airflow\airflow_url.txt") {
  $u = (Get-Content "$ProofRoot\ecs-airflow\airflow_url.txt" -Raw).Trim()
  $urls += "$u/login/", "$u/home", "$u/dags/", "$u/dags/example_bash_operator/grid?tab=graph"
}
if (Test-Path "$ProofRoot\eks\eks_state.json") {
  $u = (Get-Content "$ProofRoot\eks\eks_state.json" | ConvertFrom-Json).apiUrl
  if ($u) { $urls += "$u/docs", "$u/health" }
}
$urls | Set-Content "$LogDir\screenshot_urls.txt" -Encoding UTF8

# Phase 4 — immediate teardown (all tracks)
Write-Host "Tearing down ALL AWS resources..." -ForegroundColor Yellow
& "$Root\scripts\ecs\teardown_ecs_demo.ps1" 2>&1 | Set-Content "$LogDir\ecs-p1_teardown.log"
& "$Root\scripts\ecs\teardown_airflow_ecs.ps1" 2>&1 | Set-Content "$LogDir\airflow_teardown.log"
& "$Root\scripts\aws\teardown_sagemaker.ps1" 2>&1 | Set-Content "$LogDir\sagemaker_teardown.log"
& "$Root\scripts\aws\teardown_emr_serverless.ps1" 2>&1 | Set-Content "$LogDir\emr_teardown.log"
& "$Root\scripts\aws\teardown_eks_demo.ps1" 2>&1 | Set-Content "$LogDir\eks_teardown.log"
& "$Root\scripts\ecs\teardown_all_aws_demo.ps1" 2>&1 | Set-Content "$LogDir\final_cleanup.log"

& "$Root\scripts\aws\verify_teardown.ps1" 2>&1 | Set-Content "$LogDir\verify_teardown.log"

@{
  finishedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  screenshotUrls = $urls
  logs = "$LogDir"
} | ConvertTo-Json | Set-Content "$LogDir\parallel_run_summary.json" -Encoding UTF8

Write-Host "Parallel run complete. Screenshot URLs in $LogDir\screenshot_urls.txt" -ForegroundColor Green
