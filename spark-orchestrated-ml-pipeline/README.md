# Spark-Orchestrated ML Pipeline

**Batch data → Spark features → Airflow → trigger retrain** — orchestrates Project 1’s training data through a production-style batch feature pipeline.

| Layer | Tool |
|-------|------|
| Orchestration | Apache Airflow 2.10 (weekly wine / monthly taxi DAGs) |
| Compute | PySpark 3.5 on Bitnami Spark (local cluster via Docker Compose) |
| Feature store | Parquet partitions on local disk + `s3://…/features/` |
| Downstream ML | Triggers **Project 1** `src.train` via MLflow after wine ETL |
| Volume demo | NYC Yellow Taxi Jan 2023 (~**2.8M trips**, ~**47 MB** raw Parquet) |
| Cloud | AWS `eu-west-1` (Ireland) — shared bucket with P1, **Option A $0** |
| CI | GitHub Actions — `ruff` + pytest (helpers, local Spark, DAG import) |

## How P1 + P2 connect

```
UCI Wine CSV ──► Airflow ingest ──► PySpark transform ──► Parquet features
                                                      │
                                                      ▼
                              s3://…/features/wine/ ──► P1 src.train (--data-source feature_store)
                                                      │
                                                      ▼
                                              MLflow run + model.pkl

NYC Taxi Parquet ──► taxi_etl_pipeline ──► s3://…/features/taxi/   (volume / Spark scale story)
```

## Project layout

```
spark-orchestrated-ml-pipeline/
├── dags/
│   ├── wine_feature_pipeline_dag.py   # feeds Project 1
│   └── taxi_etl_dag.py                # ~2.8M row volume ETL
├── spark_jobs/
│   ├── transform.py                   # PySpark: clean, window agg, Parquet
│   └── helpers.py                     # pure-Python (unit tested)
├── scripts/
│   ├── download_wine.py
│   ├── download_nyc_taxi.py
│   ├── trigger_p1_train.sh
│   ├── setup_s3.sh
│   └── submit_spark_slurm.sh          # Option C HPC template
├── tests/
├── docker-compose.yml                 # Airflow + Spark master/worker
├── Dockerfile.airflow
└── .github/workflows/ci.yml
```

## Quick start (Option A — $0 local)

### 1. Prerequisites

- Docker Desktop (8 GB+ RAM recommended)
- AWS CLI configured (`eu-west-1`) — same credentials as P1
- Project 1 cloned at `../mlops-inference-platform`

### 2. Environment

```bash
cd D:\IIMA\spark-orchestrated-ml-pipeline
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
cp .env.example .env
```

### 3. Download raw data

```bash
python scripts/download_wine.py
python scripts/download_nyc_taxi.py   # optional volume DAG
```

### 4. Run Spark transform locally (no Airflow)

```bash
set PYTHONPATH=.
spark-submit --master local[*] spark_jobs/transform.py ^
  --dataset wine --input data/raw/wine --output data/features/wine ^
  --metrics-file data/features/wine/_metrics.json
```

### 5. Trigger Project 1 retrain from feature store

```bash
bash scripts/trigger_p1_train.sh data/features/wine
```

### 6. Full stack (Airflow + Spark)

```bash
docker compose up --build -d
# Airflow UI: http://localhost:8081  (admin / admin)
# Spark UI:  http://localhost:8080
```

Unpause DAGs `wine_feature_pipeline` and `taxi_etl_pipeline` in the UI, then trigger manually.

### 7. Tests

```bash
pytest tests/ -v
```

## AWS (shared with P1, eu-west-1)

```bash
bash scripts/setup_s3.sh
```

| Prefix | Contents |
|--------|----------|
| `s3://…/features/wine/` | Spark-engineered wine Parquet (P1 training input) |
| `s3://…/features/taxi/` | NYC taxi features (~2.5M+ rows after cleaning) |
| `s3://…/pipeline-metrics/` | Optional JSON job stats |

**Combined P1+P2 cost:** **$0** local Docker + **<$2/month** S3 at demo scale (well under $10 cap).

## Engineering metrics (measured)

| Metric | Value | How measured |
|--------|-------|--------------|
| Wine rows processed | ~6,400+ | Spark `_metrics.json` after outlier filter |
| Taxi rows processed | ~2.5M+ | Jan 2023 yellow taxi after fare/distance filters |
| Raw taxi data volume | ~47 MB Parquet (~120 MB in memory) | `download_nyc_taxi.py` |
| Spark partitions (wine) | 2 | `partitionBy(wine_type)` |
| Spark partitions (taxi) | ~31 | `partitionBy(pickup_date)` |
| DAG tasks (wine) | 5 | ingest → spark → validate → S3 → P1 train |
| Wine ETL runtime (local) | ~30–90 s | `local[*]` on laptop |
| Taxi ETL runtime (local) | ~3–8 min | depends on CPU/RAM |

## AWS options (budget)

| Option | Cost | When to use |
|--------|------|-------------|
| **A — Local Compose** | **$0** | Default; honest resume line |
| B — EMR Serverless one-shot | $3–8 | Run taxi job once, tear down |
| C — SLURM HPC | $0 | `scripts/submit_spark_slurm.sh` template |

**Skipped (honest):** Kafka/MSK, MWAA, EKS prod, Snowflake/dbt.

## CI/CD

On PR/push: `ruff check` + pytest (helpers, local Spark session, Airflow `DagBag` import).

## Resume bullet

> Orchestrated a batch ML feature pipeline with Apache Airflow and PySpark: wine ETL writing partitioned Parquet to S3 (eu-west-1), row-count validation gates, and automated downstream MLflow retraining of an XGBoost classifier (Project 1); scaled path on 2.8M NYC taxi trips with window-aggregated zone features.

## See also

- [EXPERIENCE.md](./EXPERIENCE.md) — step-by-step walkthrough for resume / interviews
- [../mlops-inference-platform](../mlops-inference-platform) — Project 1 inference platform

## License

MIT
