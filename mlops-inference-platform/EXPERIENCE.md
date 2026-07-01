# Experience Guide — Project 1 (MLOps Inference Platform)

Use this for interviews, LinkedIn, and resume conversion.

---

## One-line summary

End-to-end MLOps platform: XGBoost training with MLflow tracking, FastAPI inference in Docker, Evidently drift monitoring, CI/CD to GHCR, and optional minikube deploy — fed by Project 2’s Spark feature store.

---

## Step-by-step: what you did and why

### Step 1 — Problem & dataset
**What:** UCI Wine Quality — 6,497 samples, 12 features (11 physicochemical + wine type), quality 3–9.  
**Why:** Recognizable tabular ML benchmark; small enough for fast iteration, credible in interviews.  
**Target engineering:** Mapped quality to 3 tiers (low/medium/high) for stable classification.

### Step 2 — Training + MLflow
**What:** `src/train.py` — XGBoost, logs params/metrics/artifacts, registers `wine-quality-classifier`.  
**Metrics:** ~**66% accuracy**, ~**0.37 F1 macro** (imbalanced classes).  
**Say:** “Every run is reproducible — params, metrics, and model artifacts in MLflow.”

### Step 3 — Feature store integration (P2)
**What:** `load_feature_store()` reads Parquet from Project 2; `--data-source feature_store`.  
**Say:** “Training isn’t tied to CSV — it consumes the Spark feature store output.”

### Step 4 — FastAPI serving
**What:** `POST /predict`, `GET /health`, Pydantic schema validation.  
**Metrics (local, single uvicorn worker, 200 requests):**
- **p95 latency: 4.94 ms**, **throughput: 254.5 req/s** (measured via `scripts/benchmark_api.py`)

### Step 5 — Docker multi-stage
**What:** Trainer stage fits model; API stage is slim (~FastAPI + sklearn + xgboost only).  
**Say:** “Training dependencies don’t ship to production.”

### Step 6 — Testing
**What:** pytest — health, schema validation, prediction shape, training smoke test.  
**Result:** 7/7 passing.

### Step 7 — Drift monitoring
**What:** Evidently batch report vs `data/reference.parquet`; HTML to `reports/` or S3.  
**Say:** “Reference dataset snapshot from training; weekly batch compare.”

### Step 8 — CI/CD + K8s
**What:** GitHub Actions (ruff, pytest, Docker build, GHCR push on main); `k8s/deployment.yaml` for minikube.  
**Say:** “PRs run tests; main publishes a container image.”

### Step 9 — AWS (eu-west-1)
**What:** S3 bucket `mlops-inference-platform-864981752170` — models, drift reports, feature store (with P2).  
**Cost:** **<$2/month** at demo scale.

---

## Engineering metrics cheat sheet

| Metric | Value | Tool |
|--------|-------|------|
| Training samples | 6,497 | UCI wine |
| Model accuracy | ~66% | MLflow |
| F1 macro | ~0.37 | MLflow |
| API p95 latency | **4.94 ms** | `scripts/benchmark_api.py` |
| Throughput | **254.5 req/s** | same benchmark |
| Docker image stages | 2 | Dockerfile |
| Test count | 7 | pytest |
| AWS region | eu-west-1 | S3 |

---

## Resume bullets (with numbers)

1. Built an MLOps inference platform on **6.5k** wine samples: XGBoost + MLflow registry, FastAPI serving (**p95 4.9 ms**, **255 req/s** local benchmark), multi-stage Docker, pytest CI with GHCR publish, and Evidently drift reports to S3 (**eu-west-1**).

2. Integrated batch Spark feature store (Project 2) into MLflow training pipeline; containerized API with health checks and minikube deployment manifests.

---

## Demo script (5 minutes)

1. `python -m src.train` → show MLflow UI / `mlflow.db`.  
2. `uvicorn src.serve.main:app` → `/docs` → live predict.  
3. `python scripts/benchmark_api.py` → latency numbers.  
4. `python -m monitoring.drift` → open HTML report.  
5. `docker compose up` → full stack.

---

## Combined P1+P2 story (30 seconds)

“Project 2 runs weekly Airflow + Spark ETL into partitioned Parquet on S3. Project 1 consumes that feature store, retrains XGBoost with MLflow, serves predictions via FastAPI in Docker, and monitors drift with Evidently — all under $10/month on AWS.”
