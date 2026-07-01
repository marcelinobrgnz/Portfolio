# MLOps Inference Platform

**Train → track → serve → test → monitor** — a production-style tabular ML pipeline built for your resume.

| Layer | Tool |
|-------|------|
| Data | [UCI Wine Quality](https://archive.ics.uci.edu/ml/datasets/wine+quality) (red + white, 6.5k rows) |
| Training | XGBoost + scikit-learn |
| Experiment tracking | MLflow (params, metrics, model registry) |
| Serving | FastAPI `POST /predict`, `GET /health` |
| Packaging | Multi-stage Docker (trainer + slim API) |
| Tests | pytest (health, schema, prediction shape) |
| CI/CD | GitHub Actions (pytest on PR; GHCR push on `main`) |
| Monitoring | Evidently data-drift HTML reports → `reports/` or S3 |
| Orchestration | docker-compose (API + MLflow), optional minikube |
| Cloud | AWS `eu-west-1` (Ireland) — S3 for artifacts & drift reports |

## Why Wine Quality?

- Classic, interview-friendly tabular dataset (11 physicochemical features)
- Multiclass target (quality tiers 3–9 → low / medium / high)
- Small, free, no API keys — ideal for a self-contained MLOps demo
- Widely cited in ML courses and Kaggle — recruiters recognize it instantly

## Project layout

```
mlops-inference-platform/
├── src/
│   ├── config.py           # paths, feature schema, AWS region
│   ├── data.py             # download & prepare UCI wine CSVs
│   ├── schemas.py          # Pydantic request/response models
│   ├── train.py            # XGBoost + MLflow logging & registry
│   └── serve/main.py       # FastAPI inference API
├── monitoring/drift.py     # Evidently batch drift reports
├── tests/                  # pytest (API + data pipeline)
├── scripts/
│   ├── train.sh
│   ├── run_drift.sh
│   └── setup_s3.sh        # create S3 prefixes in eu-west-1
├── k8s/deployment.yaml     # minikube Deployment + NodePort
├── Dockerfile              # multi-stage: trainer | api
├── docker-compose.yml      # MLflow + API locally
└── .github/workflows/ci.yml
```

## Quick start (local)

### 1. Environment

```bash
cd D:\IIMA\mlops-inference-platform
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env   # optional — defaults work locally
```

### 2. Train & log to MLflow

**File-based tracking (no server):**

```bash
set MLFLOW_TRACKING_URI=sqlite:///mlflow.db
python -m src.train
```

**With MLflow UI (docker-compose):**

```bash
docker compose up -d mlflow
bash scripts/train.sh
# Open http://localhost:5000
```

Artifacts land in `models/wine_quality_model.pkl` and `data/reference.parquet`.

### 3. Run API

```bash
uvicorn src.serve.main:app --reload --port 8000
```

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"instances\":[{\"fixed_acidity\":7.4,\"volatile_acidity\":0.7,\"citric_acid\":0.0,\"residual_sugar\":1.9,\"chlorides\":0.076,\"free_sulfur_dioxide\":11.0,\"total_sulfur_dioxide\":34.0,\"density\":0.9978,\"pH\":3.51,\"sulphates\":0.56,\"alcohol\":9.4,\"wine_type\":0}]}"
```

Interactive docs: http://localhost:8000/docs

### 4. Docker (full stack)

```bash
python -m src.train   # ensure models/ is populated first
docker compose up --build
```

- API: http://localhost:8000  
- MLflow: http://localhost:5000  

### 5. Tests

```bash
pytest tests/ -v
```

### 6. Drift monitoring

```bash
python -m monitoring.drift
# or upload to S3 (Ireland):
bash scripts/run_drift.sh --upload-s3
```

Reports: `reports/drift_report_*.html`

## AWS (eu-west-1 Ireland)

Your account already has bucket **`mlops-inference-platform-864981752170`** in `eu-west-1`.

```bash
bash scripts/setup_s3.sh
```

| Prefix | Purpose |
|--------|---------|
| `s3://…/mlflow-artifacts/` | MLflow artifact store (optional remote tracking) |
| `s3://…/drift-reports/` | Evidently HTML + JSON summaries |
| `s3://…/models/` | Exported model bundles |

**Remote MLflow (optional):**

```bash
export MLFLOW_TRACKING_URI=http://your-mlflow-host:5000
export MLFLOW_S3_UPLOAD_EXTRA_ARGS='{"ServerSideEncryption": "AES256"}'
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root s3://mlops-inference-platform-864981752170/mlflow-artifacts
```

Estimated cost: **<$1/month** for S3 storage at demo scale; GHCR + GitHub Actions + local Docker/minikube are **$0**.

## Kubernetes (minikube)

```bash
minikube start
python -m src.train
minikube cp models /models
kubectl apply -f k8s/deployment.yaml
minikube service wine-quality-api --url
# or NodePort 30080
```

Update the image in `k8s/deployment.yaml` after your first GHCR push.

## CI/CD

On **pull request**: `ruff` + `pytest` + Docker build (no push).

On **push to `main`**: trains a model, builds the API image, pushes to **GHCR** as `ghcr.io/<user>/mlops-inference-platform:latest`.

## Model details

| Item | Value |
|------|-------|
| Algorithm | `XGBClassifier` (3-class: low / medium / high quality) |
| Features | 11 physicochemical + `wine_type` (0=red, 1=white) |
| Registry | MLflow model `wine-quality-classifier` |
| Metrics logged | `accuracy`, `f1_macro` |

## Engineering metrics

| Metric | Value | How to reproduce |
|--------|-------|------------------|
| Training samples | 6,497 | `python -m src.train` logs `n_samples` |
| Test accuracy | ~66% | MLflow / `models/model_metadata.json` |
| F1 macro | ~0.37 | MLflow metrics |
| API p95 latency | **4.94 ms** (measured) | `python scripts/benchmark_api.py` |
| Throughput | **254.5 req/s** (measured) | same benchmark, 200 requests |
| Drift reports | HTML + JSON | `python -m monitoring.drift` |
| S3 region | eu-west-1 (Ireland) | shared bucket with Project 2 |
| Monthly AWS cost | <$2 at demo scale | S3 storage only |

**Feature store (Project 2):** train from Spark Parquet with  
`python -m src.train --data-source feature_store --feature-store-path ../spark-orchestrated-ml-pipeline/data/features/wine`

See [EXPERIENCE.md](./EXPERIENCE.md) for interview walkthrough and resume bullets.

## Git init

```bash
cd D:\IIMA\mlops-inference-platform
git init
git add .
git commit -m "feat: end-to-end MLOps inference platform (wine quality)"
gh repo create mlops-inference-platform --public --source=. --push
```

## Resume bullet

> Built an end-to-end MLOps platform on UCI Wine Quality data: XGBoost training with MLflow experiment tracking and model registry, FastAPI inference in a multi-stage Docker image, pytest CI via GitHub Actions with GHCR publishing, Evidently drift monitoring to S3 (eu-west-1), and minikube deployment manifests.

## License

MIT — dataset courtesy of UCI ML Repository (Cortez et al., 2009).
