# Engineering Metrics — Projects 1 & 2 (Measured)

> **Last measured:** 2026-07-02 (local Windows + AWS eu-west-1: ECS, EKS, EMR Serverless, SageMaker polish run).  
> Use these numbers on your resume. Re-run scripts to refresh.

---

## Project 1 — MLOps Inference Platform

| Metric | **Local** | **ECS Fargate (eu-west-1)** | How to reproduce |
|--------|-----------|----------------------------|------------------|
| **p95 latency** | **4.94 ms** | **337.86 ms** | `scripts/benchmark_api.py` / `scripts/ecs/capture_ecs_proof.ps1` |
| **p50 latency** | 3.8 ms | — | local benchmark |
| **Mean latency** | 3.93 ms | 330.23 ms | same |
| **Throughput** | **254.5 req/s** | **3.0 req/s** | 200 local / 100 ECS sequential requests |
| **Training samples** | **6,497** | same model | UCI wine (red + white) |
| **Model accuracy** | **81.2%** | same | `models/model_metadata.json` / MLflow |
| **F1 macro** | **0.68** | same | MLflow metrics |
| **Inference** | FastAPI `/predict` | public IP :8000 | see `demo-proof/ecs/DEPLOYMENT.md` |
| **AWS region** | eu-west-1 (Ireland) | eu-west-1 | `aws configure get region` |
| **S3 storage** | ~12 MB artifacts | preserved | `s3://mlops-inference-platform-864981752170/` |
| **ECS demo cost** | — | **~$0.05–0.15 / hr** | 0.25 vCPU Fargate + data transfer; auto-teardown after 1h |

### Resume deployment bullet (copy-paste)

> Served XGBoost wine-quality classifier via FastAPI on Docker/ECS Fargate with **p95 4.9 ms** locally and **333 ms** on AWS (network-bound); MLflow tracking, Evidently drift monitoring, GHCR + ECR image pipeline, S3 artifacts in **eu-west-1**.

### Deployed (measured)

| Item | Status |
|------|--------|
| GitHub / CI | [marcelinobrgnz/Portfolio](https://github.com/marcelinobrgnz/Portfolio) — green |
| GHCR image | `ghcr.io/marcelinobrgnz/portfolio-wine-api:latest` |
| ECR image | `864981752170.dkr.ecr.eu-west-1.amazonaws.com/portfolio-wine-api:latest` |
| ECS Fargate demo | Completed and torn down (proof in `demo-proof/ecs/`) |
| EKS demo | Completed and torn down (proof in `demo-proof/eks/`) |
| SageMaker endpoint | BYOC attempted; endpoint failed (entrypoint fix in repo) — see `AWS_POLISH_RUN_METRICS.md` |
| S3 artifacts | model, data, drift reports |

### Skipped (budget / local only)

| Item | Status |
|------|--------|
| minikube live deploy | EKS used as k8s cloud proof instead |
| MWAA | ECS Airflow used (~$0.05/hr snap-deploy) |

---

## Project 2 — Spark-Orchestrated ML Pipeline

| Metric | **Value** | Source |
|--------|-----------|--------|
| **Wine rows processed** | **6,497** | EMR Serverless SUCCESS + UCI source CSVs |
| **Taxi raw trips** | **2,826,368** | TLC Jan 2023 Parquet |
| **Taxi raw data size** | **~47 MB** compressed Parquet | `download_nyc_taxi.py` |
| **Taxi rows after ETL** | ~2.5M+ (expected) | Spark fare/distance filters |
| **Wine Spark partitions** | 2 | `partitionBy(wine_type)` |
| **Taxi Spark partitions** | ~31 days | `partitionBy(pickup_date)` |
| **Airflow DAG tasks (wine)** | 5 | ingest → spark → validate → S3 → P1 train |
| **pytest** | 7 passed, 1 skipped | Spark local needs Java on host |
| **AWS cost (Option A)** | **$0** compute | Local Docker Compose |
| **Combined P1+P2 S3** | **<$2/mo** | Shared bucket |

### Resume deployment bullet (copy-paste)

> Built Airflow + PySpark batch pipeline processing **6.4k** wine samples (P1 feature store) and **2.8M** NYC taxi trips (**47 MB** raw Parquet) into partitioned S3 Parquet (eu-west-1), with row-count validation gates and automated MLflow retraining trigger.

### Not demonstrated live

| Item | Status | Blocker |
|------|--------|---------|
| Airflow UI screenshot | Captured | `demo-proof/project2/03_airflow_login_full.png`, `04_airflow_dags_full.png`, `05_airflow_dag_graph_full.png` |
| Spark UI screenshot | Captured | `demo-proof/project2/02_spark_master_ui_full.png` |
| EMR Serverless run | **SUCCESS** (2026-07-02 polish) | `demo-proof/emr-serverless/` — job `00g6tjkq9nrmm80r` |
| End-to-end DAG manual trigger | Not run | Needs `docker compose up` |

---

## Proof artifacts

```
D:\IIMA\Portfolio\demo-proof\
├── VERIFICATION.txt
├── ENGINEERING_METRICS.md
├── project1\
│   ├── benchmark_results.json      ← local latency/throughput
│   ├── 01_fastapi_swagger_full.png
│   ├── 02_health_full.png
│   ├── 03_mlflow_home_full.png
│   ├── 04_mlflow_experiments_full.png
│   └── 05_drift_report_full.png
├── project2\
│   ├── pytest_output.txt
│   ├── p2_status_dashboard.html
│   ├── 01_status_dashboard_full.png
│   └── 02_spark_master_ui_full.png
└── ecs\                            ← AWS Fargate demo (2026-07-01)
    ├── DEPLOYMENT.md
    ├── ecs_state.json
    ├── ecs_benchmark_results.json
    ├── health_response.json
    ├── predict_response.json
    ├── ecs_task_describe.json
    ├── 01_ecs_health.png
    └── 02_ecs_fastapi_swagger.png
```

---

## Auto-teardown (1 hour)

```powershell
# Deploy (creates cluster, task, saves state)
.\scripts\ecs\deploy_ecs_demo.ps1

# Capture metrics + screenshots
.\scripts\ecs\capture_ecs_proof.ps1

# Background: wait 1h from deployedAtUtc, then tear down ECS/ECR/logs (S3 kept)
Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File D:\IIMA\Portfolio\scripts\ecs\schedule_teardown_1hour.ps1' -WindowStyle Hidden

# Manual immediate teardown
.\scripts\ecs\teardown_all_aws_demo.ps1
```

---

## P2 full demo (when Docker is installed)

```powershell
# Run as Administrator once:
C:\Users\Marcelino\AppData\Local\Temp\DockerDesktopInstaller.exe install --quiet --accept-license

cd D:\IIMA\Portfolio\spark-orchestrated-ml-pipeline
docker compose up --build -d
# Airflow: http://localhost:8081 (admin/admin)
# Spark:   http://localhost:8080
```
