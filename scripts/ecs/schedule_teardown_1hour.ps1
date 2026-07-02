# Schedule full AWS demo teardown after 1 hour from deploy time.
# Usage: Start-Process powershell -ArgumentList '-File D:\IIMA\Portfolio\scripts\ecs\schedule_teardown_1hour.ps1' -WindowStyle Hidden

$StateFile = "D:\IIMA\Portfolio\demo-proof\ecs\ecs_state.json"
$LogFile = "D:\IIMA\Portfolio\demo-proof\ecs\teardown_scheduler.log"

function Log($msg) {
  $line = "$(Get-Date -Format o) $msg"
  Add-Content $LogFile $line -Encoding UTF8
  Write-Host $line
}

if (-not (Test-Path $StateFile)) {
  Log "ERROR: No ecs_state.json - run deploy_ecs_demo.ps1 first"
  exit 1
}

# Prevent accidental immediate teardown from a stale/missing deployedAtUtc
$state = Get-Content $StateFile -Raw | ConvertFrom-Json
if (-not $state.deployedAtUtc) {
  Log "ERROR: ecs_state.json missing deployedAtUtc"
  exit 1
}
$deployed = [datetime]::Parse(
  $state.deployedAtUtc,
  $null,
  [System.Globalization.DateTimeStyles]::AdjustToUniversal
)
$teardownAt = $deployed.ToUniversalTime().AddHours(1)
$waitSeconds = [int](($teardownAt - [datetime]::UtcNow).TotalSeconds)

if ($waitSeconds -lt 0) {
  Log "Deploy was >1h ago - tearing down immediately"
  $waitSeconds = 0
} else {
  Log "Scheduled teardown in $waitSeconds seconds (at $teardownAt UTC)"
}

if ($waitSeconds -gt 0) { Start-Sleep -Seconds $waitSeconds }

Log "Starting teardown..."
& "D:\IIMA\Portfolio\scripts\ecs\teardown_all_aws_demo.ps1" 2>&1 | ForEach-Object { Log $_ }
Log "Teardown script finished"
