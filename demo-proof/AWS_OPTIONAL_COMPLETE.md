# AWS Optional Items — Completed (2026-07-03)

> One service at a time: deploy on AWS → proof → tear down. No local Docker required.

## 1. SageMaker Real-Time Inference — SUCCESS

| Item | Value |
|------|-------|
| Build | AWS CodeBuild → ECR `portfolio-wine-sagemaker` |
| Endpoint | `wine-quality-demo-ep` (ml.t2.medium) |
| Invoke | `{"predictions": [0]}` |
| Script | `scripts/aws/deploy_sagemaker_aws.ps1` |
| Teardown | `scripts/aws/teardown_sagemaker_aws.ps1` |
| Proof | `demo-proof/sagemaker/invoke_response.json`, `sagemaker_metrics.json` |

## 2. Airflow E2E on AWS (ECS) — SUCCESS

| Item | Value |
|------|-------|
| Build | AWS CodeBuild → ECR `portfolio-airflow-e2e` (DAGs baked in) |
| Runtime | ECS Fargate + `airflow standalone` |
| API proof | `demo-proof/ecs-airflow/dags_list_api.json` — lists `wine_feature_pipeline` + `taxi_etl_pipeline` |
| Script | `scripts/ecs/deploy_airflow_e2e_aws.ps1` |
| Teardown | `scripts/ecs/teardown_airflow_e2e_aws.ps1` |

## 3. minikube — Not needed (AWS substitute)

EKS demo already captured in `demo-proof/eks/` (k8s on AWS).

## 4. MWAA — Skipped (budget)

Minimum ~$1/day NAT + environment hourly. **ECS Fargate Airflow** used as AWS orchestration proof instead.

## 5. Local Airflow :8081 — Not needed

AWS ECS Airflow E2E replaces local docker-compose proof.

---

All optional AWS compute torn down after capture. Ongoing cost: S3 only (~<$2/mo).
