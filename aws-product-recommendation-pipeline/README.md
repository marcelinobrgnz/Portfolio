# AWS Product Recommendation Pipeline

**SageMaker training · Glue-style ETL · Lambda API** — tabular recommender on public Amazon review data (Electronics subset), aligned with production AWS ML patterns.

Part of the [Portfolio](../README.md) monorepo (Project 4).

| Layer | Tool |
|-------|------|
| Data | Hugging Face / Parquet items & events (Electronics) |
| ETL | Python Parquet prep; Glue ETL scripts (`glue_etl_*.py`) |
| Training | **Amazon SageMaker** — XGBoost recommender (`training_code/sagemaker_train_recommender.py`) |
| Serving | SageMaker endpoint; **Lambda** + API Gateway pattern (`lambda_recommendation_api.py`) |
| Quality | `data_quality_checks.py` |
| Region | **eu-west-1** (Ireland) |

## Layout

```
aws-product-recommendation-pipeline/
├── training_code/sagemaker_train_recommender.py
├── run_sagemaker_training.py
├── glue_etl_process_items.py
├── glue_etl_process_events.py
├── electronics_to_parquet.py
├── download_electronics_hf.py
├── lambda_recommendation_api.py
├── lambda_event_processor.py
├── data_quality_checks.py
├── cloudwatch_dashboard.json
└── docs/
```

## Related monorepo paths

| Asset | Location |
|-------|----------|
| Wine SageMaker BYOC deploy (shared AWS pattern) | [`../scripts/aws/deploy_sagemaker_aws.ps1`](../scripts/aws/deploy_sagemaker_aws.ps1) |
| Invoke / teardown proof | [`../demo-proof/sagemaker/`](../demo-proof/sagemaker/) |
| Feature pipeline (wine) | [`../spark-orchestrated-ml-pipeline/`](../spark-orchestrated-ml-pipeline/) |

## Quick start (local prep)

```powershell
cd aws-product-recommendation-pipeline
python -m venv .venv
.\.venv\Scripts\activate
pip install pandas pyarrow scikit-learn xgboost
# Optional: download subset
python download_electronics_hf.py
python electronics_to_parquet.py
```

SageMaker training: use `run_sagemaker_training.py` with your AWS account, S3 channels, and execution role (see `docs/RecSys-Plan.md`).

## Honesty

Portfolio / demo scope — not Amazon employment. Claim **hands-on SageMaker, ETL, Lambda, recommender modeling** tied to this folder and proofs under `demo-proof/`.

## License

MIT — see repository root.
