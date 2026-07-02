# AWS Full Parallel Run — Metrics & Proof (2026-07-02)

> All compute torn down immediately after proof capture. S3 artifacts preserved.

## ECS Fargate — P1 Wine API

| Metric | Value |
|--------|-------|
| Region | eu-west-1 |
| API URL (at capture) | http://3.250.190.207:8000 |
| p95 latency | **337.86 ms** |
| Mean latency | 330.23 ms |
| Throughput | **3.0 req/s** (100 sequential) |
| Model loaded | true |
| Screenshots | `demo-proof/ecs/03_ecs_swagger_full.png`, `04_ecs_health_full.png` |
| JSON proof | `ecs_benchmark_results.json`, `health_response.json`, `predict_response.json` |

## ECS Fargate — Airflow UI

| Metric | Value |
|--------|-------|
| URL | http://54.194.28.113:8080 |
| Health endpoint | 200 OK (scheduler healthy) |
| Login | admin/admin |
| Screenshots | `demo-proof/ecs-airflow/01_airflow_login_full.png` |

## Amazon EKS

| Metric | Value |
|--------|-------|
| Cluster | portfolio-eks-demo |
| Node type | t3.small |
| K8s version | 1.30 |
| Node external IP | 3.254.189.235 |
| NodePort | 30080 |
| Pod status | 1/1 Running |
| Screenshots | `demo-proof/eks/01_eks_swagger_full.png` (via kubectl port-forward) |
| JSON proof | `kubectl_get_all.txt`, `eks_cluster_describe.json` |

## EMR Serverless Spark

| Metric | Value |
|--------|-------|
| Application | portfolio-spark-demo (`00g6ti26amk2al0p`) |
| Release | emr-7.0.0 |
| **Polish run (2026-07-02)** | **SUCCESS** — job `00g6tjkq9nrmm80r` |
| Output | 2 Parquet partitions (`wine_type=0/1`), 6,497 source rows |
| JSON proof | `demo-proof/emr-serverless/job_run_describe.json`, `emr_metrics.json` |

## SageMaker Real-Time Inference

| Metric | Value |
|--------|-------|
| **Polish run status** | CreateModel OK (BYOC); endpoint **Failed** (container `serve` entrypoint) |
| Fix committed | `scripts/sagemaker/wsgi.py` Python entrypoint |
| Model artifact on S3 | `s3://.../sagemaker/wine-sagemaker-model.tar.gz` |
| Details | `demo-proof/AWS_POLISH_RUN_METRICS.md` |

## MWAA

Skipped — requires NAT gateway (~$1/day minimum). ECS Airflow used as AWS orchestration proof.

## Teardown

Script: `scripts/aws/teardown_all_now.ps1`  
Verification: `demo-proof/AWS_TEARDOWN_VERIFICATION.md`
