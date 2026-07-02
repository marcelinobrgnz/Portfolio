# Portfolio Experience Pack (Projects 1 + 2)

Use for LinkedIn, resume, and interviews. All metrics are measured unless marked expected.

---

## Combined elevator pitch (45 seconds)

"I built a two-project MLOps portfolio under $10 total AWS cost. Project 2 is an Airflow-orchestrated PySpark pipeline that engineers wine and NYC taxi features into partitioned Parquet on S3, with row-count validation before triggering retrain. Project 1 consumes that feature store, trains XGBoost with MLflow, serves predictions via FastAPI in Docker, monitors drift with Evidently, and deploys to ECS Fargate in Ireland. I measured p95 latency at 4.9 ms locally and documented everything with CI, tests, and demo proof artifacts."

---

## Project 1 - MLOps Inference Platform

| Area | Detail |
|------|--------|
| Dataset | UCI Wine Quality, 6,497 samples |
| Model | XGBoost classifier (~66% accuracy, 0.37 F1 macro) |
| Serving | FastAPI /predict, /health |
| Latency | p95 4.94 ms, 255 req/s (local benchmark) |
| ECS demo | p95 333 ms, 3 req/s (network-bound, eu-west-1) |
| MLOps | MLflow tracking + registry |
| Monitoring | Evidently drift HTML reports |
| Infra | Docker multi-stage, GHCR, ECS Fargate, S3 eu-west-1 |
| Tests | 7/7 pytest, GitHub Actions CI |
| Cost | under $2/mo S3 after compute teardown |

**LinkedIn copy:** see `LINKEDIN_PROJECT1.md`  
**Deep dive:** `../mlops-inference-platform/EXPERIENCE.md`

---

## Project 2 - Spark-Orchestrated ML Pipeline

| Area | Detail |
|------|--------|
| Wine ETL | ~6,400 rows after filters |
| Taxi scale test | 2,826,368 trips, ~47 MB raw Parquet |
| Orchestration | Airflow 5-task DAG |
| Compute | PySpark 3.5.4, window aggregates |
| Feature store | S3 partitioned Parquet (eu-west-1) |
| Quality gate | Fail DAG if wine rows < 6,000 |
| P1 integration | trigger_p1_train calls MLflow retrain |
| Tests | 7 passed, 1 skipped (Spark/Java on Windows host) |
| Cost | $0 local Docker compute + shared S3 |

**LinkedIn copy:** see `LINKEDIN_PROJECT2.md`  
**Deep dive:** `../spark-orchestrated-ml-pipeline/EXPERIENCE.md`

---

## AWS billing status

See `AWS_TEARDOWN_VERIFICATION.md` - ECS, ECR, CloudWatch logs, and security groups removed. Only S3 storage remains (under $2/mo).

---

## Proof artifacts

```
demo-proof/
  project1/          - benchmark JSON, API/MLflow screenshots
  project2/          - pytest, status dashboard, Spark/Airflow screenshots
  ecs/               - AWS Fargate demo proof
  LINKEDIN_PROJECT1.md
  LINKEDIN_PROJECT2.md
  AWS_TEARDOWN_VERIFICATION.md
  ENGINEERING_METRICS.md
```
