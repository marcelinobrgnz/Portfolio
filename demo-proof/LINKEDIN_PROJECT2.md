# LinkedIn Post - Project 2: Spark-Orchestrated ML Pipeline

## Short post (recommended)

Built a batch ML data platform that feeds my inference API (Project 1):

- PySpark: wine (6.4k rows) + NYC Taxi (2.8M trips, 47 MB Parquet)
- Airflow 5-task DAG: ingest, Spark, validate, S3, trigger retrain
- Row-count quality gate (fail if under 6,000 wine rows)
- Partitioned Parquet feature store on S3 (eu-west-1)
- pytest CI + DagBag import check
- $0 local compute, under $2/mo shared S3

Stack: PySpark, Airflow, Docker, Parquet, S3, MLflow integration

Repo: https://github.com/marcelinobrgnz/Portfolio

#DataEngineering #ApacheSpark #Airflow #MLOps #Python #AWS

## Resume bullet

Orchestrated PySpark + Airflow pipeline processing 6.4k wine samples and 2.8M NYC taxi trips into partitioned S3 Parquet with row-count validation gates and automated MLflow retraining trigger.
