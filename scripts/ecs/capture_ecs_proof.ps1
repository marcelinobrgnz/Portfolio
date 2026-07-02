# Capture ECS demo proof: health, predict, benchmark, AWS metadata
$ErrorActionPreference = "Stop"
$ProofDir = "D:\IIMA\Portfolio\demo-proof\ecs"
$StateFile = "$ProofDir\ecs_state.json"
if (Test-Path $StateFile) {
  $state = Get-Content $StateFile -Raw | ConvertFrom-Json
  $ApiUrl = $state.apiUrl
} elseif (Test-Path "$ProofDir\api_url.txt") {
  $ApiUrl = (Get-Content "$ProofDir\api_url.txt" -Raw).Trim()
} else {
  throw "No ECS state found. Run deploy_ecs_demo.ps1 first."
}

Write-Host "Capturing from $ApiUrl"

# Health
$health = Invoke-RestMethod "$ApiUrl/health" -TimeoutSec 30
$health | ConvertTo-Json | Set-Content "$ProofDir\health_response.json"

# Predict
$body = @{
  instances = @(
    @{
      fixed_acidity = 7.4; volatile_acidity = 0.7; citric_acid = 0.0
      residual_sugar = 1.9; chlorides = 0.076; free_sulfur_dioxide = 11.0
      total_sulfur_dioxide = 34.0; density = 0.9978; pH = 3.51
      sulphates = 0.56; alcohol = 9.4; wine_type = 0
    }
  )
} | ConvertTo-Json -Depth 4
$predict = Invoke-RestMethod "$ApiUrl/predict" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
$predict | ConvertTo-Json | Set-Content "$ProofDir\predict_response.json"

# Benchmark (100 requests)
$latencies = @()
$sw = [System.Diagnostics.Stopwatch]::StartNew()
1..100 | ForEach-Object {
  $t = [System.Diagnostics.Stopwatch]::StartNew()
  Invoke-RestMethod "$ApiUrl/predict" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30 | Out-Null
  $latencies += $t.Elapsed.TotalMilliseconds
}
$sw.Stop()
$sorted = $latencies | Sort-Object
$p95idx = [math]::Max(0, [int](0.95 * $sorted.Count) - 1)
$bench = @{
  environment = "AWS ECS Fargate eu-west-1"
  apiUrl = $ApiUrl
  requests = 100
  throughput_rps = [math]::Round(100 / $sw.Elapsed.TotalSeconds, 1)
  latency_ms_mean = [math]::Round(($latencies | Measure-Object -Average).Average, 2)
  latency_ms_p95 = [math]::Round($sorted[$p95idx], 2)
  latency_ms_max = [math]::Round(($latencies | Measure-Object -Maximum).Maximum, 2)
}
$bench | ConvertTo-Json | Set-Content "$ProofDir\ecs_benchmark_results.json"

# AWS task describe
$state = Get-Content $StateFile | ConvertFrom-Json
aws ecs describe-tasks --cluster $state.cluster --tasks $state.taskArn --region eu-west-1 `
  | Set-Content "$ProofDir\ecs_task_describe.json"

Write-Host "Proof saved to $ProofDir"
$bench | Format-List
