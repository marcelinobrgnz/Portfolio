# LinkedIn Post - Project 1: MLOps Inference Platform

## Short post (recommended)

I shipped an end-to-end MLOps inference platform on a real budget (under $2/mo AWS):

- 6,497 wine samples (UCI) to XGBoost classifier
- MLflow experiment tracking + model registry
- FastAPI serving: p95 4.9 ms, 255 req/s (local benchmark)
- Evidently drift monitoring to S3
- Docker multi-stage build, GHCR, ECS Fargate demo (eu-west-1)
- pytest + GitHub Actions CI

Stack: Python, XGBoost, MLflow, FastAPI, Docker, GitHub Actions, AWS S3, ECS Fargate

Repo: https://github.com/marcelinobrgnz/Portfolio

#MachineLearning #MLOps #DataScience #Python #AWS #Docker #FastAPI #MLflow

## Resume bullet

Built MLOps inference platform on 6.5k wine samples: XGBoost + MLflow registry, FastAPI (p95 4.9 ms, 255 req/s), multi-stage Docker, pytest CI with GHCR publish, Evidently drift reports, ECS Fargate deploy in eu-west-1.
