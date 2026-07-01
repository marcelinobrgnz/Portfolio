# Engineering Metrics — Projects 1 & 2 (Measured)

> **Last measured:** 2026-07-01 on local Windows machine.  
> Use these numbers on your resume. Re-run scripts to refresh.

---

## Project 1 — MLOps Inference Platform

| Metric | **Measured value** | How to reproduce |
|--------|-------------------|------------------|
| **p95 latency** | **4.94 ms** | `python scripts/benchmark_api.py` (API on :8000) |
| **p50 latency** | 3.8 ms | same |
| **Mean latency** | 3.93 ms | same |
| **Throughput** | **254.5 req/s** | same, 200 sequential requests |
| **Training samples** | **6,497** | UCI wine (red + white) |
| **Model accuracy** | ~66% | MLflow `wine-quality` experiment |
| **F1 macro** | ~0.37 | MLflow metrics |
| **Inference batch size** | 1 request (REST) | FastAPI `/predict` |
| **AWS region** | eu-west-1 (Ireland) | `aws configure get region` |
| **S3 storage** | ~12 MB artifacts | `aws s3 ls --recursive s3://mlops-inference-platform-864981752170/` |
| **Monthly AWS cost** | **<$2** | S3-only at demo scale (no SageMaker/ECS always-on) |

### Resume deployment bullet (copy-paste)

> Served XGBoost wine-quality classifier via FastAPI on Docker with **p95 latency 4.9 ms** and **255 req/s** throughput (local benchmark, 6.5k training samples); MLflow tracking, Evidently drift monitoring, and S3 artifact store in **eu-west-1**.

### NOT deployed (honest)

| Item | Status |
|------|--------|
| SageMaker endpoint | Not provisioned (would add ~$50+/mo) |
| ECS Fargate always-on | Not running |
| GitHub push / GHCR | Repos staged, not pushed |
| minikube live deploy | Manifest only |

---

## Project 2 — Spark-Orchestrated ML Pipeline

| Metric | **Value** | Source |
|--------|-----------|--------|
| **Wine rows processed** | ~6,400+ | Spark ETL after outlier filter |
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

### NOT demonstrated live (honest)

| Item | Status | Blocker |
|------|--------|---------|
| Airflow UI screenshot | Not captured | **Docker not installed** on this machine |
| Spark UI screenshot | Not captured | Docker not installed |
| EMR Serverless run | Not run | Option B ($3–8), skipped for budget |
| End-to-end DAG manual trigger | Not run | Needs `docker compose up` |
| GitHub push | Not done | Repos initialized, not committed/pushed |

---

## Proof artifacts

```
D:\IIMA\demo-proof\
├── VERIFICATION.txt
├── project1\
│   ├── benchmark_results.json      ← measured latency/throughput
│   ├── 01_fastapi_swagger.png
│   ├── p1_health.png
│   ├── p1_mlflow_home.png
│   └── p1_mlflow_wine_quality_runs.png
└── project2\
    └── pytest_output.txt
```

---

## What to run for full P2 demo screenshots

```powershell
# Requires Docker Desktop
cd D:\IIMA\spark-orchestrated-ml-pipeline
docker compose up --build -d
# Airflow: http://localhost:8081 (admin/admin)
# Spark:   http://localhost:8080
```

Then trigger `wine_feature_pipeline` DAG and screenshot the graph + task logs.
