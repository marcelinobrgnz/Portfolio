# ECS Fargate Demo — Wine Quality API

| Field | Value |
|-------|-------|
| **API URL** | http://54.76.246.14:8000 |
| **Health** | http://54.76.246.14:8000/health |
| **Swagger** | http://54.76.246.14:8000/docs |
| **Region** | eu-west-1 (Ireland) |
| **AZ** | eu-west-1c |
| **Cluster** | `portfolio-wine-demo` |
| **Task ARN** | `arn:aws:ecs:eu-west-1:864981752170:task/portfolio-wine-demo/881cfc3b354e4b898ea422c014ca911a` |
| **Task definition** | `portfolio-wine-api:3` |
| **CPU / Memory** | 256 (0.25 vCPU) / 512 MB |
| **Launch type** | FARGATE (public IP) |
| **Image** | `864981752170.dkr.ecr.eu-west-1.amazonaws.com/portfolio-wine-api:latest` |
| **Security group** | `sg-08186726d261f8c30` (TCP 8000 from 0.0.0.0/0) |
| **Subnet** | `subnet-0fdf9810d55d97daf` |
| **Public IP** | 54.76.246.14 |
| **Private IP** | 172.31.32.224 |
| **Deployed (UTC)** | 2026-07-01T13:57:58.4864101Z |
| **Auto-teardown (UTC)** | 2026-07-01T14:57:58.5025221Z |

## Measured performance (100 sequential POST /predict)

| Metric | Value |
|--------|-------|
| p95 latency | 332.88 ms |
| mean latency | 329.85 ms |
| throughput | 3.0 req/s |

> Higher latency vs local (4.9 ms p95) is expected: cross-region network RTT to a 0.25 vCPU Fargate task with no ALB.

## Proof files

- `health_response.json`, `predict_response.json`
- `ecs_benchmark_results.json`
- `ecs_task_describe.json`
- `01_ecs_health.png`, `02_ecs_fastapi_swagger.png`

## Teardown

Background scheduler: `scripts/ecs/schedule_teardown_1hour.ps1`  
Manual: `scripts/ecs/teardown_all_aws_demo.ps1` (ECS + ECR + logs; **S3 preserved**)
