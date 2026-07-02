# Copy browser screenshots to demo-proof
$src = "$env:LOCALAPPDATA\Temp\cursor\screenshots"
$alt = "C:\Users\Marcelino\AppData\Local\Temp\cursor\screenshots"
if (-not (Test-Path $src)) { $src = $alt }

$p1 = "D:\IIMA\Portfolio\demo-proof\project1"
$p2 = "D:\IIMA\Portfolio\demo-proof\project2"
New-Item -ItemType Directory -Force -Path $p1, $p2 | Out-Null

$map = @{
  "p1_01_swagger_full.png" = "$p1\01_fastapi_swagger_full.png"
  "p1_02_health_full.png"  = "$p1\02_health_full.png"
  "p1_03_mlflow_home_full.png" = "$p1\03_mlflow_home_full.png"
  "p1_04_mlflow_experiments_full.png" = "$p1\04_mlflow_experiments_full.png"
  "p1_05_drift_report_full.png" = "$p1\05_drift_report_full.png"
  "p2_01_status_dashboard_full.png" = "$p2\01_status_dashboard_full.png"
  "p2_02_spark_ui_full.png" = "$p2\02_spark_master_ui_full.png"
  "p2_03_airflow_login_full.png" = "$p2\03_airflow_login_full.png"
  "p2_04_airflow_dags_full.png" = "$p2\04_airflow_dags_full.png"
  "p2_05_airflow_dag_graph_full.png" = "$p2\05_airflow_dag_graph_full.png"
}

foreach ($k in $map.Keys) {
  $from = Join-Path $src $k
  if (Test-Path $from) {
    Copy-Item $from $map[$k] -Force
    Write-Host "Copied $k"
  }
}
Get-ChildItem $p1, $p2 -Filter *.png | Select-Object FullName, Length
