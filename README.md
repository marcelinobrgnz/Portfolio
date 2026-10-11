# Portfolio — MLE & Data Projects

**Marcelino Braganza** · [braganzamarcelino@gmail.com](mailto:braganzamarcelino@gmail.com)

End-to-end portfolio: **MLOps serving**, **Spark/Airflow batch**, **enterprise RAG**, **SageMaker recommender**, and **analytics engineering (CFPB)** on AWS and modern data stack.

| # | Project | Tagline | Folder |
|---|---------|---------|--------|
| 1 | **MLOps Inference Platform** | Train → track → serve → test → monitor | [`mlops-inference-platform/`](./mlops-inference-platform/) |
| 2 | **Spark-Orchestrated ML Pipeline** | Batch data → Spark → Airflow → retrain | [`spark-orchestrated-ml-pipeline/`](./spark-orchestrated-ml-pipeline/) |
| 3 | **SecureGuard RAG** | Bedrock RAG + guardrails + Streamlit + Lambda API | [`secureguard-rag/`](./secureguard-rag/) |
| 4 | **AWS Product Recommendation Pipeline** | Glue/Parquet ETL → SageMaker XGBoost → Lambda API | [`aws-product-recommendation-pipeline/`](./aws-product-recommendation-pipeline/) |
| 5 | **CFPB Data Platform** | Parquet → Snowflake → dbt → Airflow → Databricks Delta (18.1M rows) | [`cfpb-data-platform/`](./cfpb-data-platform/) |

**GitHub:** [marcelinobrgnz/Portfolio](https://github.com/marcelinobrgnz/Portfolio) — all five projects live in this monorepo.

## Engineering metrics (measured)

| Metric | P1 | P2 |
|--------|----|----|
| **p95 latency** | 4.94 ms | — |
| **Throughput** | 254.5 req/s | — |
| **Training / batch volume** | 6,497 wine samples | 2.8M taxi trips (~47 MB) |
| **AWS region** | eu-west-1 | eu-west-1 |
| **Monthly cost** | <$2 S3 | $0 local + S3 |

See [`demo-proof/ENGINEERING_METRICS.md`](./demo-proof/ENGINEERING_METRICS.md) for full numbers and screenshots.

## Quick start

```bash
# Project 1
cd mlops-inference-platform && pip install -r requirements-dev.txt && pytest tests/ -v

# Project 2
cd spark-orchestrated-ml-pipeline && pip install -r requirements-dev.txt && pytest tests/ -v

# Project 3 (AWS account required; copy config.env.example → config.env)
cd secureguard-rag && pip install -r requirements.txt && python scripts/step01_verify_aws.py

# Project 4
cd aws-product-recommendation-pipeline && pip install pandas pyarrow scikit-learn xgboost

# Project 5
cd cfpb-data-platform && pip install -r requirements.txt
# See cfpb-data-platform/docs/RUNBOOK.md
```

## License

MIT — see individual project folders.
